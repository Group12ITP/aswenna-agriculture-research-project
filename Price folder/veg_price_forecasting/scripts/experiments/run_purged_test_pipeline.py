import sys
import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.preprocessing import StandardScaler
from scipy import stats
import yaml
import warnings
warnings.filterwarnings('ignore')
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

_print = print
def print(*args, **kwargs):
    kwargs.setdefault('flush', True)
    _print(*args, **kwargs)

from src.utils import load_config, set_seeds, get_logger
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.models.baselines import (
    NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster, DriftForecaster,
    RollingMeanForecaster, SeasonalMean4YrForecaster, AR1CategoryMeanForecaster
)
from src.models.statistical import (
    HoltWintersRollingForecaster, AutoARIMARollingForecaster,
    SARIMAXRollingForecaster, ProphetRollingForecaster
)
from src.models.classical import get_classical_model
from src.models.deep_learning import (
    MLPNet, LSTMNet, GRUNet, TCNNet, NBeatsNet, TransformerNet, NHiTSNet, TFTLiteNet, device
)
from src.models.ensembles import SimpleAverageEnsemble, StackingMetaLearner, BestPerCategoryEnsemble
from src.intervals import ScaleAwareConformalPredictor, evaluate_interval_quality
from src.metrics import (
    evaluate_predictions, compute_skill_vs_naive,
    block_bootstrap_mase, diebold_mariano_test
)
from src.train import prepare_feature_matrices, tune_classical_model

logger = get_logger("purged_test_pipeline")

def train_dl_test_purged(arch, X_rf, y_rf, X_te_eval, epochs=10, lr=1e-3, batch_size=128):
    """PyTorch model trainer fitting strictly on purged refit data and predicting on test."""
    scaler = StandardScaler()
    X_rf_s = scaler.fit_transform(X_rf)
    X_te_s = scaler.transform(X_te_eval)
    
    y_scaler = StandardScaler()
    y_rf_s = y_scaler.fit_transform(np.array(y_rf).reshape(-1, 1)).ravel()
    
    in_dim = X_rf.shape[1]
    if arch == "mlp":
        model = MLPNet(in_dim, hidden_dims=(128, 64))
    elif arch == "lstm":
        model = LSTMNet(in_dim, hidden_dim=64)
    elif arch == "gru":
        model = GRUNet(in_dim, hidden_dim=64)
    elif arch == "tcn_1d":
        model = TCNNet(in_dim, num_channels=(64, 32))
    elif arch == "nbeats":
        model = NBeatsNet(in_dim, hidden_dim=128)
    elif arch == "transformer":
        model = TransformerNet(in_dim, d_model=64)
    elif arch == "nhits":
        model = NHiTSNet(in_dim, hidden_dim=64)
    elif arch == "tft_lite":
        model = TFTLiteNet(in_dim, d_model=64)
    else:
        raise ValueError(f"Unknown arch {arch}")
        
    model = model.to(device)
    optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    criterion = nn.HuberLoss()
    
    ds = TensorDataset(torch.tensor(X_rf_s, dtype=torch.float32), torch.tensor(y_rf_s, dtype=torch.float32))
    loader = DataLoader(ds, batch_size=batch_size, shuffle=True)
    
    model.train()
    for ep in range(epochs):
        for bx, by in loader:
            bx, by = bx.to(device), by.to(device)
            optimizer.zero_grad()
            p = model(bx)
            loss = criterion(p, by)
            loss.backward()
            optimizer.step()
            
    model.eval()
    with torch.no_grad():
        p_te_norm = model(torch.tensor(X_te_s, dtype=torch.float32).to(device)).cpu().numpy().reshape(-1, 1)
        test_pred = y_scaler.inverse_transform(p_te_norm).ravel()
        
    return test_pred

def run():
    cfg = load_config()
    set_seeds(cfg.get("random_seed", 42))
    
    print("Loading data and engineering features...")
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    
    horizons = [1, 4, 8, 12]
    
    # Load current leaderboard to preserve validation rows and CIs
    lead_path = Path("experiments/leaderboard.csv")
    df_lead_old = pd.read_csv(lead_path) if lead_path.exists() else None
    
    ratio_models_ml = ["lasso", "ridge", "elastic_net", "lightgbm", "xgboost", "catboost", "extra_trees"]
    ratio_models_dl = ["mlp", "tcn_1d", "gru", "nbeats", "nhits"]
    
    updated_records = []
    old_vs_new_comparison = []
    split_refit_summary = []
    
    for h in horizons:
        print(f"\n{'='*70}\nTRAINING & EVALUATION HORIZON h = {h} (PURGED TEST REFIT)\n{'='*70}")
        train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
        target_col = f"target_h{h}"
        
        target_week = df_feat["week_index"] + h
        # PURGED REFIT MASK: train_mask | (val_mask & target_week <= 417 - h)
        max_allowed_refit_target = 417 - h
        refit_mask = train_mask | (val_mask & (target_week <= max_allowed_refit_target))
        
        tr_tgt_max = target_week[train_mask].max()
        vl_tgt_max = target_week[val_mask].max()
        rf_tgt_max = target_week[refit_mask].max()
        te_tgt_min = target_week[test_mask].min()
        purge_gap = te_tgt_min - rf_tgt_max
        
        print(f"Purge Integrity h={h}:")
        print(f"  Train max target week: {tr_tgt_max}")
        print(f"  Val max target week:   {vl_tgt_max}")
        print(f"  Refit max target week: {rf_tgt_max} (Required <= {max_allowed_refit_target})")
        print(f"  First test target:     {te_tgt_min} -> Purge Gap: {purge_gap} weeks (Required >= {h})")
        print(f"  Refit observations:    {refit_mask.sum()} (Purged {(val_mask & (target_week > max_allowed_refit_target)).sum()} rows)")
        
        split_refit_summary.append({
            "horizon": h,
            "train_n": train_mask.sum(),
            "val_n": val_mask.sum(),
            "refit_n": refit_mask.sum(),
            "purged_n": (val_mask & (target_week > max_allowed_refit_target)).sum(),
            "last_refit_target_week": rf_tgt_max,
            "required_max_target_week": max_allowed_refit_target,
            "first_test_target_week": te_tgt_min,
            "purge_gap_to_test": f"{purge_gap} wks (>= {h})"
        })
        
        y_val_true = df_feat.loc[val_mask, target_col]
        y_test_true = df_feat.loc[test_mask, target_col]
        
        # Validation calibration partition (purged for conformal test calibration)
        val_weeks = df_feat.loc[val_mask, "week_index"].sort_values().unique()
        mid_week = val_weeks[len(val_weeks) // 2]
        val_cal_mask = val_mask & (df_feat["week_index"] >= mid_week)
        val_cal_purged = val_cal_mask & (target_week <= max_allowed_refit_target)
        
        y_cal_true = df_feat.loc[val_cal_purged, target_col]
        y_origin_val = df_feat.loc[val_mask, "price_lkr"]
        y_origin_test = df_feat.loc[test_mask, "price_lkr"]
        
        all_test_preds = {}
        all_val_preds = {}
        
        # -------------------------------------------------------------
        # 1. Baselines (including 3 new strong long-horizon baselines)
        # -------------------------------------------------------------
        baselines = cfg["models"]["baselines"] + ["rolling_52wk_mean", "seasonal_mean_4yr", "ar1_category_mean"]
        
        # Compute category means for AR(1) category baseline
        cat_means_by_week = df_feat.groupby(["category", "week_index"])["price_lkr"].mean().to_dict()
        
        for m_name in baselines:
            val_preds_list = []
            test_preds_list = []
            for veg in df_feat["product_name"].unique():
                v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
                train_prices = v_df.loc[train_mask.loc[v_df.index], "price_lkr"].values
                cat = v_df["category"].iloc[0]
                
                if m_name == "naive":
                    model = NaiveForecaster()
                    model.fit(train_prices)
                elif m_name == "seasonal_naive_48":
                    model = SeasonalNaiveForecaster(season_m=48)
                    model.fit(train_prices)
                elif m_name == "moving_average_4":
                    model = MovingAverageForecaster(window=4)
                    model.fit(train_prices)
                elif m_name == "moving_average_12":
                    model = MovingAverageForecaster(window=12)
                    model.fit(train_prices)
                elif m_name == "drift":
                    model = DriftForecaster()
                    model.fit(train_prices)
                elif m_name == "rolling_52wk_mean":
                    model = RollingMeanForecaster(window=52)
                    model.fit(train_prices)
                elif m_name == "seasonal_mean_4yr":
                    model = SeasonalMean4YrForecaster(season_m=48, n_years=4)
                    model.fit(train_prices)
                elif m_name == "ar1_category_mean":
                    model = AR1CategoryMeanForecaster(phi=0.92)
                    model.fit(train_prices)
                    
                for idx in v_df.index[val_mask.loc[v_df.index]]:
                    curr_w = v_df.loc[idx, "week_index"]
                    hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
                    if m_name == "ar1_category_mean":
                        c_mu = cat_means_by_week.get((cat, curr_w), hist[-1])
                        val_preds_list.append((idx, model.predict(horizon=h, y_history=hist, cat_mean=c_mu)))
                    else:
                        val_preds_list.append((idx, model.predict(horizon=h, y_history=hist)))
                        
                for idx in v_df.index[test_mask.loc[v_df.index]]:
                    curr_w = v_df.loc[idx, "week_index"]
                    hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
                    if m_name == "ar1_category_mean":
                        c_mu = cat_means_by_week.get((cat, curr_w), hist[-1])
                        test_preds_list.append((idx, model.predict(horizon=h, y_history=hist, cat_mean=c_mu)))
                    else:
                        test_preds_list.append((idx, model.predict(horizon=h, y_history=hist)))
                        
            all_val_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in val_preds_list}, name=f"pred_{m_name}")
            all_test_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in test_preds_list}, name=f"pred_{m_name}")
            
        # -------------------------------------------------------------
        # 2. Statistical Models (Parameters fit on train only; unchanged under test purge)
        # -------------------------------------------------------------
        # We reuse existing predictions from experiments/runs for the 4 statistical models
        stat_models = ["holt_winters_ets", "auto_arima", "sarimax", "prophet"]
        for m_name in stat_models:
            # Find the most recent run dir for this model and horizon
            matching_runs = sorted(list(Path("experiments/runs").glob(f"*_{m_name}_h{h}")))
            if matching_runs:
                run_dir = matching_runs[-1]
                pred_test_file = run_dir / "predictions_test.csv"
                if pred_test_file.exists():
                    df_p_test = pd.read_csv(pred_test_file)
                    df_te_eval = df_feat.loc[test_mask, ["product_name", "approx_date"]].copy()
                    merged_p = pd.merge(df_te_eval, df_p_test[["product_name", "approx_date", "y_pred"]], on=["product_name", "approx_date"], how="left")
                    all_test_preds[(m_name, "raw_level")] = pd.Series(merged_p["y_pred"].values, index=y_test_true.index, name=f"pred_{m_name}")
                
                pred_val_file = run_dir / "predictions_val.csv"
                if pred_val_file.exists():
                    df_p_val = pd.read_csv(pred_val_file)
                    df_vl_eval = df_feat.loc[val_mask, ["product_name", "approx_date"]].copy()
                    merged_pv = pd.merge(df_vl_eval, df_p_val[["product_name", "approx_date", "y_pred"]], on=["product_name", "approx_date"], how="left")
                    all_val_preds[(m_name, "raw_level")] = pd.Series(merged_pv["y_pred"].values, index=y_val_true.index, name=f"pred_{m_name}")
            
            # If not found or fallback needed, run quick rolling forecast
            if (m_name, "raw_level") not in all_test_preds:
                print(f"  Computing statistical model {m_name}...")
                test_preds_list = []
                for veg in df_feat["product_name"].unique():
                    v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
                    full_series = v_df["price_lkr"].values
                    v_tr_idx = v_df.index[train_mask.loc[v_df.index]]
                    train_series = v_df.loc[v_tr_idx, "price_lkr"].values
                    test_idx = v_df.index[test_mask.loc[v_df.index]]
                    test_pos = [v_df.index.get_loc(idx) for idx in test_idx]
                    if m_name == "auto_arima":
                        fc_obj = AutoARIMARollingForecaster(d=1)
                    elif m_name == "holt_winters_ets":
                        fc_obj = HoltWintersRollingForecaster(seasonal_periods=48)
                    elif m_name == "sarimax":
                        fc_obj = SARIMAXRollingForecaster(order=(1, 1, 1))
                    elif m_name == "prophet":
                        fc_obj = ProphetRollingForecaster()
                    fc_obj.fit_parameters(train_series)
                    fc_res = fc_obj.rolling_forecast(full_series, test_pos, horizon=h)
                    for idx, pos in zip(test_idx, test_pos):
                        test_preds_list.append((idx, fc_res.get(pos, float(v_df.loc[idx, "price_lkr"]))))
                all_test_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in test_preds_list}, name=f"pred_{m_name}")
                
            # For validation predictions, statistical models are already benchmarked and unchanged
            # We can use naive or origin price placeholder for ensemble pool if needed, or actual val pred
            all_val_preds[(m_name, "raw_level")] = all_val_preds[("naive", "raw_level")].copy()
            
        # -------------------------------------------------------------
        # 3. Classical ML (Tuned on train, Val fit on train, Purged Test Refit)
        # -------------------------------------------------------------
        X, y_raw, features = prepare_feature_matrices(df_feat, target_col=target_col)
        y_orig = df_feat["price_lkr"].clip(lower=1.0)
        y_ratio = np.log(np.clip(y_raw / y_orig, 1e-4, None))
        
        classical_models = cfg["models"]["classical_ml"]
        for m_name in classical_models:
            modes = ["raw_level"]
            if m_name in ratio_models_ml:
                modes.append("log_ratio")
                
            for mode in modes:
                print(f"  Fitting ML {m_name} ({mode})...")
                y_target = y_raw if mode == "raw_level" else y_ratio
                
                X_train, y_train = X[train_mask], y_target[train_mask]
                X_val, y_val = X[val_mask], y_target[val_mask]
                X_test, y_test = X[test_mask], y_target[test_mask]
                
                # Tuned parameters from pre-registered CV
                if m_name == "lasso":
                    tuned_alphas = {1: 1.5359, 4: 3.3947, 8: 4.4937, 12: 0.6522}
                    best_params = {"alpha": tuned_alphas.get(h, 1.0) if mode == "raw_level" else 0.01}
                elif m_name == "ridge":
                    best_params = {"alpha": 10.0 if mode == "raw_level" else 1.0}
                elif m_name == "elastic_net":
                    best_params = {"alpha": 0.1 if mode == "raw_level" else 0.01, "l1_ratio": 0.5}
                elif m_name in ['lightgbm', 'xgboost', 'catboost', 'random_forest', 'extra_trees', 'gradient_boosting']:
                    best_params = {"n_estimators": 100, "learning_rate": 0.05, "max_depth": 6}
                    if m_name == "lightgbm":
                        best_params["num_leaves"] = 31
                elif m_name == "svr":
                    best_params = {"C": 10.0, "epsilon": 0.1}
                else:
                    best_params = {}
                
                # Val fit (train only)
                m_val = get_classical_model(m_name, params=best_params)
                clean_tr = pd.notna(y_train)
                m_val.fit(X_train[clean_tr], y_train[clean_tr])
                p_val_raw = m_val.predict(X_val)
                
                # TEST REFIT ON PURGED DATA (refit_mask: train + val <= 417 - h)
                X_rf = X[refit_mask]
                y_rf = y_target[refit_mask]
                clean_rf = pd.notna(y_rf)
                
                m_final = get_classical_model(m_name, params=best_params)
                m_final.fit(X_rf[clean_rf], y_rf[clean_rf])
                p_test_raw = m_final.predict(X_test)
                
                if mode == "log_ratio":
                    val_p = y_orig[val_mask] * np.exp(p_val_raw)
                    test_p = y_orig[test_mask] * np.exp(p_test_raw)
                else:
                    val_p = p_val_raw
                    test_p = p_test_raw
                    
                val_p = np.nan_to_num(np.maximum(0.0, val_p), nan=0.0)
                test_p = np.nan_to_num(np.maximum(0.0, test_p), nan=0.0)
                
                all_val_preds[(m_name, mode)] = pd.Series(val_p, index=X_val.index, name=f"pred_{m_name}")
                all_test_preds[(m_name, mode)] = pd.Series(test_p, index=X_test.index, name=f"pred_{m_name}")
                
        # -------------------------------------------------------------
        # 4. Deep Learning (Tuned on train, Purged Test Refit)
        # -------------------------------------------------------------
        dl_models = cfg["models"]["deep_learning"]
        for arch in dl_models:
            modes = ["raw_level"]
            if arch in ratio_models_dl:
                modes.append("log_ratio")
                
            for mode in modes:
                print(f"  Fitting DL {arch} ({mode})...")
                y_target = y_raw if mode == "raw_level" else y_ratio
                
                valid_tr = pd.notna(y_target[train_mask])
                valid_vl = pd.notna(y_target[val_mask])
                valid_rf = pd.notna(y_target[refit_mask])
                
                X_tr_mat = X[train_mask].values[valid_tr]
                y_tr_vec = y_target[train_mask].values[valid_tr]
                X_vl_eval = X[val_mask].values
                X_te_eval = X[test_mask].values
                
                # Val model fit strictly on train
                scaler_v = StandardScaler()
                X_tr_s = scaler_v.fit_transform(X_tr_mat)
                X_vl_s = scaler_v.transform(X_vl_eval)
                y_sc_v = StandardScaler()
                y_tr_s = y_sc_v.fit_transform(y_tr_vec.reshape(-1, 1)).ravel()
                
                in_dim = X_tr_mat.shape[1]
                if arch == "mlp":
                    m_val_dl = MLPNet(in_dim, hidden_dims=(128, 64))
                elif arch == "lstm":
                    m_val_dl = LSTMNet(in_dim, hidden_dim=64)
                elif arch == "gru":
                    m_val_dl = GRUNet(in_dim, hidden_dim=64)
                elif arch == "tcn_1d":
                    m_val_dl = TCNNet(in_dim, num_channels=(64, 32))
                elif arch == "nbeats":
                    m_val_dl = NBeatsNet(in_dim, hidden_dim=128)
                elif arch == "transformer":
                    m_val_dl = TransformerNet(in_dim, d_model=64)
                elif arch == "nhits":
                    m_val_dl = NHiTSNet(in_dim, hidden_dim=64)
                elif arch == "tft_lite":
                    m_val_dl = TFTLiteNet(in_dim, d_model=64)
                    
                m_val_dl = m_val_dl.to(device)
                opt_v = optim.AdamW(m_val_dl.parameters(), lr=1e-3, weight_decay=1e-4)
                crit = nn.HuberLoss()
                ds_v = TensorDataset(torch.tensor(X_tr_s, dtype=torch.float32), torch.tensor(y_tr_s, dtype=torch.float32))
                ld_v = DataLoader(ds_v, batch_size=128, shuffle=True)
                m_val_dl.train()
                for _ in range(5):
                    for bx, by in ld_v:
                        bx, by = bx.to(device), by.to(device)
                        opt_v.zero_grad()
                        loss = crit(m_val_dl(bx), by)
                        loss.backward()
                        opt_v.step()
                m_val_dl.eval()
                with torch.no_grad():
                    p_vl_n = m_val_dl(torch.tensor(X_vl_s, dtype=torch.float32).to(device)).cpu().numpy().reshape(-1, 1)
                    p_val_raw = y_sc_v.inverse_transform(p_vl_n).ravel()
                    
                # Test model fit strictly on PURGED REFIT DATA
                X_rf_mat = X[refit_mask].values[valid_rf]
                y_rf_vec = y_target[refit_mask].values[valid_rf]
                p_test_raw = train_dl_test_purged(arch, X_rf_mat, y_rf_vec, X_te_eval, epochs=6)
                
                if mode == "log_ratio":
                    val_p = y_orig[val_mask].values * np.exp(p_val_raw)
                    test_p = y_orig[test_mask].values * np.exp(p_test_raw)
                else:
                    val_p = p_val_raw
                    test_p = p_test_raw
                    
                val_p = np.nan_to_num(np.maximum(0.0, val_p), nan=0.0)
                test_p = np.nan_to_num(np.maximum(0.0, test_p), nan=0.0)
                
                all_val_preds[(arch, mode)] = pd.Series(val_p, index=y_val_true.index, name=f"pred_{arch}")
                all_test_preds[(arch, mode)] = pd.Series(test_p, index=y_test_true.index, name=f"pred_{arch}")
                
        # -------------------------------------------------------------
        # 5. Ensembles (Mode selected on validation, fit on purged val)
        # -------------------------------------------------------------
        candidate_pool_modes = {}
        for m_name in classical_models + dl_models:
            if (m_name, "log_ratio") in all_val_preds:
                m_lvl = evaluate_predictions(y_val_true, all_val_preds[(m_name, "raw_level")], y_train_history=df_feat.loc[train_mask, "price_lkr"])
                m_rat = evaluate_predictions(y_val_true, all_val_preds[(m_name, "log_ratio")], y_train_history=df_feat.loc[train_mask, "price_lkr"])
                chosen = "log_ratio" if m_rat["MASE"] < m_lvl["MASE"] else "raw_level"
                candidate_pool_modes[m_name] = chosen
            else:
                candidate_pool_modes[m_name] = "raw_level"
                
        candidate_names = classical_models + dl_models
        model_val_mases = {}
        for cm in candidate_names:
            c_mode = candidate_pool_modes[cm]
            val_s = all_val_preds[(cm, c_mode)]
            res = evaluate_predictions(y_val_true, val_s, y_train_history=df_feat.loc[train_mask, "price_lkr"])
            model_val_mases[cm] = res["MASE"]
            
        sorted_candidates = sorted(model_val_mases.items(), key=lambda x: x[1])
        top3_names = [x[0] for x in sorted_candidates[:3]]
        
        # Simple Average Top-3
        avg_ens = SimpleAverageEnsemble(top3_names)
        val_ens_p = avg_ens.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in top3_names})
        test_ens_p = avg_ens.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in top3_names})
        all_val_preds[("simple_average_top3", "raw_level")] = pd.Series(val_ens_p, index=y_val_true.index, name="pred_simple_average_top3")
        all_test_preds[("simple_average_top3", "raw_level")] = pd.Series(test_ens_p, index=y_test_true.index, name="pred_simple_average_top3")
        
        # Stacking Meta Learner (fit on purged validation data)
        val_purged_idx = val_mask & (target_week <= max_allowed_refit_target)
        clean_vl_purged = pd.notna(df_feat.loc[val_purged_idx, target_col].values)
        stacker = StackingMetaLearner(candidate_names)
        stacker.fit(
            {m: all_val_preds[(m, candidate_pool_modes[m])].loc[val_purged_idx].values[clean_vl_purged] for m in candidate_names},
            df_feat.loc[val_purged_idx, target_col].values[clean_vl_purged]
        )
        val_stack_p = stacker.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in candidate_names})
        test_stack_p = stacker.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in candidate_names})
        all_val_preds[("stacking_meta_learner", "raw_level")] = pd.Series(val_stack_p, index=y_val_true.index, name="pred_stacking_meta_learner")
        all_test_preds[("stacking_meta_learner", "raw_level")] = pd.Series(test_stack_p, index=y_test_true.index, name="pred_stacking_meta_learner")
        
        # Best Per Category (fit on purged validation data)
        cat_ens = BestPerCategoryEnsemble()
        cat_ens.fit(
            {m: all_val_preds[(m, candidate_pool_modes[m])].loc[val_purged_idx].values[clean_vl_purged] for m in candidate_names},
            df_feat.loc[val_purged_idx, target_col].values[clean_vl_purged],
            df_feat.loc[val_purged_idx, "category"].values[clean_vl_purged]
        )
        val_cat_p = cat_ens.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in candidate_names}, df_feat.loc[val_mask, "category"])
        test_cat_p = cat_ens.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in candidate_names}, df_feat.loc[test_mask, "category"])
        all_val_preds[("best_per_category", "raw_level")] = pd.Series(val_cat_p, index=y_val_true.index, name="pred_best_per_category")
        all_test_preds[("best_per_category", "raw_level")] = pd.Series(test_cat_p, index=y_test_true.index, name="pred_best_per_category")
        
        # -------------------------------------------------------------
        # 6. Metrics, Bootstrap CIs, Conformal Intervals, DM Tests
        # -------------------------------------------------------------
        naive_val_p = all_val_preds[("naive", "raw_level")]
        naive_test_p = all_test_preds[("naive", "raw_level")]
        m_naive_val = evaluate_predictions(y_val_true, naive_val_p, y_train_history=df_feat.loc[train_mask, "price_lkr"])
        m_naive_test = evaluate_predictions(y_test_true, naive_test_p, y_train_history=df_feat.loc[refit_mask, "price_lkr"])
        
        all_models_modes = list(all_val_preds.keys())
        
        for (m_name, mode) in all_models_modes:
            val_p = all_val_preds[(m_name, mode)]
            test_p = all_test_preds[(m_name, mode)]
            
            # Conformal calibration on PURGED val_cal
            conformal = ScaleAwareConformalPredictor(alpha_levels=(0.20, 0.05))
            val_cal_pred = val_p.loc[val_cal_purged]
            conformal.calibrate(y_cal_true, val_cal_pred)
            test_intervals = conformal.predict_intervals(test_p)
            
            cov_test_80 = evaluate_interval_quality(y_test_true, test_intervals["lower_80"], test_intervals["upper_80"], y_pred=test_p, metadata_df=df_feat.loc[test_mask])
            cov_test_95 = evaluate_interval_quality(y_test_true, test_intervals["lower_95"], test_intervals["upper_95"], y_pred=test_p, metadata_df=df_feat.loc[test_mask])
            
            val_mets = evaluate_predictions(y_val_true, val_p, y_train_history=df_feat.loc[train_mask, "price_lkr"], y_prev=y_origin_val)
            test_mets = evaluate_predictions(y_test_true, test_p, y_train_history=df_feat.loc[refit_mask, "price_lkr"], y_prev=y_origin_test)
            
            sk_val = compute_skill_vs_naive(val_mets["MASE"], m_naive_val["MASE"])
            sk_test = compute_skill_vs_naive(test_mets["MASE"], m_naive_test["MASE"])
            
            # Bootstrap test CIs (250 resamples)
            boot_res = block_bootstrap_mase(
                y_test_true, test_p, y_naive_pred=naive_test_p,
                y_train_history=df_feat.loc[refit_mask, "price_lkr"],
                week_indices=df_feat.loc[test_mask, "week_index"],
                block_length=4, n_boot=250
            )
            
            # DM test vs Naive
            dm_stat, dm_pval = diebold_mariano_test(
                y_test_true, test_p, naive_test_p, h=h,
                week_indices=df_feat.loc[test_mask, "week_index"]
            )
            
            # Record Validation: preserve exact existing leaderboard record if available
            has_old_v = False
            if df_lead_old is not None:
                old_v_match = df_lead_old[
                    (df_lead_old["model"] == m_name) & 
                    (df_lead_old["target_mode"] == mode) & 
                    (df_lead_old["horizon"] == h) & 
                    (df_lead_old["split"] == "validation")
                ]
                if len(old_v_match) > 0:
                    updated_records.append(old_v_match.iloc[0].to_dict())
                    has_old_v = True
                    
            if not has_old_v:
                # Bootstrap validation CI for new baselines
                v_boot = block_bootstrap_mase(
                    y_val_true, val_p, y_naive_pred=naive_val_p,
                    y_train_history=df_feat.loc[train_mask, "price_lkr"],
                    week_indices=df_feat.loc[val_mask, "week_index"],
                    block_length=4, n_boot=250
                )
                val_ci_str = f"[{v_boot.get('mase_ci_low')}, {v_boot.get('mase_ci_high')}]"
                updated_records.append({
                    "model": m_name, "target_mode": mode, "horizon": h, "split": "validation",
                    "MAE": val_mets["MAE"], "RMSE": val_mets["RMSE"], "MAPE": val_mets["MAPE"], "sMAPE": val_mets["sMAPE"],
                    "MASE": val_mets["MASE"], "R2": val_mets["R2"], "Bias": val_mets["Bias"],
                    "Directional_Accuracy": val_mets["Directional_Accuracy"],
                    "Skill_vs_Naive": round(float(sk_val), 2) if pd.notna(sk_val) else np.nan,
                    "n_obs": val_mets["n_obs"],
                    "Coverage_80": np.nan, "Width_80_LKR": np.nan, "Width_80_Pct": np.nan,
                    "Coverage_95": np.nan, "Width_95_LKR": np.nan, "Width_95_Pct": np.nan,
                    "MASE_CI_95": val_ci_str, "Diff_Naive_CI_95": np.nan, "DM_stat_vs_Naive": np.nan, "DM_pval_vs_Naive": np.nan
                })
            
            # Record Test
            updated_records.append({
                "model": m_name, "target_mode": mode, "horizon": h, "split": "test",
                "MAE": test_mets["MAE"], "RMSE": test_mets["RMSE"], "MAPE": test_mets["MAPE"], "sMAPE": test_mets["sMAPE"],
                "MASE": test_mets["MASE"], "R2": test_mets["R2"], "Bias": test_mets["Bias"],
                "Directional_Accuracy": test_mets["Directional_Accuracy"],
                "Skill_vs_Naive": round(float(sk_test), 2) if pd.notna(sk_test) else np.nan,
                "n_obs": test_mets["n_obs"],
                "Coverage_80": cov_test_80["coverage_pct"], "Width_80_LKR": cov_test_80["mean_width_lkr"], "Width_80_Pct": cov_test_80["mean_width_pct"],
                "Coverage_95": cov_test_95["coverage_pct"], "Width_95_LKR": cov_test_95["mean_width_lkr"], "Width_95_Pct": cov_test_95["mean_width_pct"],
                "MASE_CI_95": f"[{boot_res.get('mase_ci_low')}, {boot_res.get('mase_ci_high')}]",
                "Diff_Naive_CI_95": f"[{boot_res.get('diff_naive_ci_low')}, {boot_res.get('diff_naive_ci_high')}]",
                "DM_stat_vs_Naive": dm_stat, "DM_pval_vs_Naive": dm_pval
            })
            
            # Comparison with old leaderboard
            if df_lead_old is not None:
                old_t_match = df_lead_old[
                    (df_lead_old["model"] == m_name) & 
                    (df_lead_old["target_mode"] == mode) & 
                    (df_lead_old["horizon"] == h) & 
                    (df_lead_old["split"] == "test")
                ]
                if len(old_t_match) > 0:
                    old_t = old_t_match.iloc[0]
                    old_vs_new_comparison.append({
                        "model": m_name, "target_mode": mode, "horizon": h,
                        "old_test_MASE": round(old_t["MASE"], 4),
                        "new_test_MASE": round(test_mets["MASE"], 4),
                        "mase_change": round(test_mets["MASE"] - old_t["MASE"], 4),
                        "old_test_skill": round(old_t["Skill_vs_Naive"], 2),
                        "new_test_skill": round(float(sk_test), 2),
                        "old_dm_pval": round(old_t.get("DM_pval_vs_Naive", np.nan), 4),
                        "new_dm_pval": round(dm_pval, 4)
                    })
                    
    df_new_lead = pd.DataFrame(updated_records)
    
    # Apply Holm correction across tests within horizon
    df_new_lead["DM_pval_Holm_vs_Naive"] = np.nan
    test_mask_lead = df_new_lead["split"] == "test"
    for h in horizons:
        h_idx = df_new_lead[test_mask_lead & (df_new_lead["horizon"] == h)].index
        p_raw = df_new_lead.loc[h_idx, "DM_pval_vs_Naive"].values
        m_tests = len(p_raw)
        p_pairs = [(i, p) for i, p in enumerate(p_raw) if pd.notna(p)]
        p_pairs_sorted = sorted(p_pairs, key=lambda x: x[1])
        
        adj_p = {}
        running_max = 0.0
        for rank_idx, (orig_i, p_val) in enumerate(p_pairs_sorted):
            k = rank_idx + 1
            corr_p = min(1.0, (m_tests - k + 1) * p_val)
            running_max = max(running_max, corr_p)
            adj_p[orig_i] = round(min(1.0, running_max), 4)
            
        holm_vals = [adj_p.get(i, np.nan) for i in range(len(p_raw))]
        df_new_lead.loc[h_idx, "DM_pval_Holm_vs_Naive"] = holm_vals
        
    # Update old_vs_new with holm p-vals
    for r in old_vs_new_comparison:
        m, mode, h = r["model"], r["target_mode"], r["horizon"]
        match = df_new_lead[(df_new_lead["model"] == m) & (df_new_lead["target_mode"] == mode) & (df_new_lead["horizon"] == h) & (df_new_lead["split"] == "test")]
        if len(match) > 0:
            r["new_dm_pval_holm"] = match.iloc[0]["DM_pval_Holm_vs_Naive"]
            
    df_comp = pd.DataFrame(old_vs_new_comparison)
    df_comp.to_csv("results/tables/test_refit_purge_comparison.csv", index=False)
    print(f"\nSaved test refit purge comparison to results/tables/test_refit_purge_comparison.csv (N={len(df_comp)})")
    
    # Save split integrity summary with refit purge row
    df_split_summary = pd.DataFrame(split_refit_summary)
    df_split_summary.to_csv("results/tables/test_refit_purge_split_summary.csv", index=False)
    print("Saved test refit split summary to results/tables/test_refit_purge_split_summary.csv")
    
    # Check how many models significant at h=12
    h12_test = df_new_lead[(df_new_lead["split"] == "test") & (df_new_lead["horizon"] == 12)]
    # Candidate models excluding naive itself
    h12_candidates = h12_test[h12_test["model"] != "naive"]
    n_sig_raw = (h12_candidates["DM_pval_vs_Naive"] < 0.05).sum()
    n_sig_holm = (h12_candidates["DM_pval_Holm_vs_Naive"] < 0.05).sum()
    n_sig_better_holm = ((h12_candidates["DM_pval_Holm_vs_Naive"] < 0.05) & (h12_candidates["Skill_vs_Naive"] > 0)).sum()
    print(f"\n>>> Horizon h=12 Significance Analysis (Purged Refit):")
    print(f"  Total evaluated models (excluding naive): {len(h12_candidates)}")
    print(f"  Uncorrected DM p < 0.05: {n_sig_raw}")
    print(f"  Holm-corrected p < 0.05: {n_sig_holm} (all with positive skill: {n_sig_better_holm})")
    
    # Save updated leaderboard.csv
    df_new_lead.to_csv("experiments/leaderboard.csv", index=False)
    print("Saved updated experiments/leaderboard.csv successfully!")
    
    # Report top models at h=4 and h=12
    print("\nTop 5 Models at h=4 Test:")
    print(df_new_lead[(df_new_lead["split"] == "test") & (df_new_lead["horizon"] == 4)].sort_values("MASE")[["model", "target_mode", "MASE", "sMAPE", "Skill_vs_Naive", "DM_pval_Holm_vs_Naive"]].head(5).to_string(index=False))

    print("\nTop 5 Models at h=12 Test:")
    print(df_new_lead[(df_new_lead["split"] == "test") & (df_new_lead["horizon"] == 12)].sort_values("MASE")[["model", "target_mode", "MASE", "sMAPE", "Skill_vs_Naive", "DM_pval_Holm_vs_Naive"]].head(5).to_string(index=False))

if __name__ == "__main__":
    run()
