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
    NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster, DriftForecaster
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

logger = get_logger("retrain_target_splits")

def train_dl_model(arch, X_train, y_train, X_val_fit, y_val_fit, X_val_eval, X_test_eval, epochs=10, lr=1e-3, batch_size=128):
    """Clean PyTorch model trainer returning val_preds and test_preds on full eval matrices."""
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_vl_s = scaler.transform(X_val_eval)
    X_te_s = scaler.transform(X_test_eval)
    
    y_scaler = StandardScaler()
    y_tr_s = y_scaler.fit_transform(np.array(y_train).reshape(-1, 1)).ravel()
    
    in_dim = X_train.shape[1]
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
    
    ds = TensorDataset(torch.tensor(X_tr_s, dtype=torch.float32), torch.tensor(y_tr_s, dtype=torch.float32))
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
        p_vl_norm = model(torch.tensor(X_vl_s, dtype=torch.float32).to(device)).cpu().numpy().reshape(-1, 1)
        val_pred = y_scaler.inverse_transform(p_vl_norm).ravel()
        
    # Refit on train + val for test
    X_tr_val = np.vstack([X_train, X_val_fit])
    y_tr_val = np.concatenate([y_train, y_val_fit])
    X_tr_val_s = scaler.fit_transform(X_tr_val)
    X_te_s = scaler.transform(X_test_eval)
    y_tr_val_s = y_scaler.fit_transform(y_tr_val.reshape(-1, 1)).ravel()
    
    if arch == "mlp":
        model_final = MLPNet(in_dim, hidden_dims=(128, 64))
    elif arch == "lstm":
        model_final = LSTMNet(in_dim, hidden_dim=64)
    elif arch == "gru":
        model_final = GRUNet(in_dim, hidden_dim=64)
    elif arch == "tcn_1d":
        model_final = TCNNet(in_dim, num_channels=(64, 32))
    elif arch == "nbeats":
        model_final = NBeatsNet(in_dim, hidden_dim=128)
    elif arch == "transformer":
        model_final = TransformerNet(in_dim, d_model=64)
    elif arch == "nhits":
        model_final = NHiTSNet(in_dim, hidden_dim=64)
    elif arch == "tft_lite":
        model_final = TFTLiteNet(in_dim, d_model=64)
        
    model_final = model_final.to(device)
    opt_final = optim.AdamW(model_final.parameters(), lr=lr, weight_decay=1e-4)
    ds_final = TensorDataset(torch.tensor(X_tr_val_s, dtype=torch.float32), torch.tensor(y_tr_val_s, dtype=torch.float32))
    loader_final = DataLoader(ds_final, batch_size=batch_size, shuffle=True)
    
    model_final.train()
    for ep in range(epochs):
        for bx, by in loader_final:
            bx, by = bx.to(device), by.to(device)
            opt_final.zero_grad()
            p = model_final(bx)
            loss = criterion(p, by)
            loss.backward()
            opt_final.step()
            
    model_final.eval()
    with torch.no_grad():
        p_te_norm = model_final(torch.tensor(X_te_s, dtype=torch.float32).to(device)).cpu().numpy().reshape(-1, 1)
        test_pred = y_scaler.inverse_transform(p_te_norm).ravel()
        
    return val_pred, test_pred

def run():
    cfg = load_config()
    set_seeds(cfg.get("random_seed", 42))
    
    print("Loading data and engineering features...")
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    
    horizons = [1, 4, 8, 12]
    
    ratio_models_ml = ["lasso", "ridge", "elastic_net", "lightgbm", "xgboost", "catboost", "extra_trees"]
    ratio_models_dl = ["mlp", "tcn_1d", "gru", "nbeats", "nhits"]
    
    leaderboard_records = []
    target_comp_records = []
    by_veg_records = []
    all_val_preds_by_h = {}
    val_truth_by_h = {}
    train_hist_by_h = {}
    val_weeks_by_h = {}
    
    # Store old leaderboard to report old-vs-new difference
    old_lead_path = Path("experiments/leaderboard.csv")
    df_old_lead = pd.read_csv(old_lead_path) if old_lead_path.exists() else None
    
    for h in horizons:
        print(f"\n{'='*70}\nTRAINING HORIZON h = {h} (TARGET-DATE SPLIT)\n{'='*70}")
        train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
        
        target_col = f"target_h{h}"
        y_val_true = df_feat.loc[val_mask, target_col]
        y_test_true = df_feat.loc[test_mask, target_col]
        
        # Validation partitions: first 24 weeks tune, last 24 weeks cal
        val_weeks = df_feat.loc[val_mask, "week_index"].sort_values().unique()
        mid_week = val_weeks[len(val_weeks) // 2]
        val_tune_mask = val_mask & (df_feat["week_index"] < mid_week)
        val_cal_mask = val_mask & (df_feat["week_index"] >= mid_week)
        
        y_cal_true = df_feat.loc[val_cal_mask, target_col]
        y_origin_val = df_feat.loc[val_mask, "price_lkr"]
        y_origin_test = df_feat.loc[test_mask, "price_lkr"]
        
        tr_orig_min, tr_orig_max = df_feat.loc[train_mask, "week_index"].min(), df_feat.loc[train_mask, "week_index"].max()
        tr_tgt_min, tr_tgt_max = tr_orig_min + h, tr_orig_max + h
        vl_orig_min, vl_orig_max = df_feat.loc[val_mask, "week_index"].min(), df_feat.loc[val_mask, "week_index"].max()
        vl_tgt_min, vl_tgt_max = vl_orig_min + h, vl_orig_max + h
        te_orig_min, te_orig_max = df_feat.loc[test_mask, "week_index"].min(), df_feat.loc[test_mask, "week_index"].max()
        te_tgt_min, te_tgt_max = te_orig_min + h, te_orig_max + h
        
        print(f"Split Verification h={h}:")
        print(f"  Train: origin [{tr_orig_min}, {tr_orig_max}], target [{tr_tgt_min}, {tr_tgt_max}], N={train_mask.sum()}")
        print(f"  Val:   origin [{vl_orig_min}, {vl_orig_max}], target [{vl_tgt_min}, {vl_tgt_max}], N={val_mask.sum()}")
        print(f"  Test:  origin [{te_orig_min}, {te_orig_max}], target [{te_tgt_min}, {te_tgt_max}], N={test_mask.sum()}")
        assert vl_tgt_min - tr_tgt_max >= h, f"Train targets must end >= h weeks before val: {vl_tgt_min} - {tr_tgt_max} < {h}"
        assert vl_tgt_max < te_tgt_min, f"Val targets must end before test targets: {vl_tgt_max} >= {te_tgt_min}"
        
        all_val_preds = {} # (m_name, mode) -> Series
        all_test_preds = {}
        
        # 1. Baselines
        baselines = cfg["models"]["baselines"]
        for m_name in baselines:
            print(f"  Running Baseline: {m_name}...")
            val_preds_list = []
            test_preds_list = []
            for veg in df_feat["product_name"].unique():
                v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
                train_prices = v_df.loc[train_mask.loc[v_df.index], "price_lkr"].values
                if m_name == "naive":
                    model = NaiveForecaster()
                elif m_name == "seasonal_naive_48":
                    model = SeasonalNaiveForecaster(season_m=48)
                elif m_name == "moving_average_4":
                    model = MovingAverageForecaster(window=4)
                elif m_name == "moving_average_12":
                    model = MovingAverageForecaster(window=12)
                elif m_name == "drift":
                    model = DriftForecaster()
                model.fit(train_prices)
                
                for idx in v_df.index[val_mask.loc[v_df.index]]:
                    curr_w = v_df.loc[idx, "week_index"]
                    hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
                    val_preds_list.append((idx, model.predict(horizon=h, y_history=hist)))
                for idx in v_df.index[test_mask.loc[v_df.index]]:
                    curr_w = v_df.loc[idx, "week_index"]
                    hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
                    test_preds_list.append((idx, model.predict(horizon=h, y_history=hist)))
                    
            all_val_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in val_preds_list}, name=f"pred_{m_name}")
            all_test_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in test_preds_list}, name=f"pred_{m_name}")
            
        # 2. Statistical Models
        stat_models = cfg["models"]["statistical"]
        for m_name in stat_models:
            print(f"  Running Statistical: {m_name}...")
            val_preds_list = []
            test_preds_list = []
            for veg in df_feat["product_name"].unique():
                v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index").copy()
                v_df["ds"] = pd.to_datetime(v_df["approx_date"])
                full_series = v_df["price_lkr"].values
                v_tr_idx = v_df.index[train_mask.loc[v_df.index]]
                train_series = v_df.loc[v_tr_idx, "price_lkr"].values
                val_idx = v_df.index[val_mask.loc[v_df.index]]
                test_idx = v_df.index[test_mask.loc[v_df.index]]
                val_pos = [v_df.index.get_loc(idx) for idx in val_idx]
                test_pos = [v_df.index.get_loc(idx) for idx in test_idx]
                
                if m_name == "holt_winters_ets":
                    forecaster = HoltWintersRollingForecaster(seasonal_periods=48)
                    forecaster.fit_parameters(train_series)
                    val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=h)
                    test_fc = forecaster.rolling_forecast(full_series, test_pos, horizon=h)
                elif m_name == "auto_arima":
                    forecaster = AutoARIMARollingForecaster(d=1)
                    forecaster.fit_parameters(train_series)
                    val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=h)
                    test_fc = forecaster.rolling_forecast(full_series, test_pos, horizon=h)
                elif m_name == "sarimax":
                    forecaster = SARIMAXRollingForecaster(order=(1, 1, 1))
                    forecaster.fit_parameters(train_series)
                    val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=h)
                    test_fc = forecaster.rolling_forecast(full_series, test_pos, horizon=h)
                elif m_name == "prophet":
                    forecaster = ProphetRollingForecaster()
                    val_fc = forecaster.rolling_forecast(v_df, val_pos, horizon=h)
                    test_fc = forecaster.rolling_forecast(v_df, test_pos, horizon=h)
                    
                for idx, pos in zip(val_idx, val_pos):
                    val_preds_list.append((idx, val_fc.get(pos, float(v_df.loc[idx, "price_lkr"]))))
                for idx, pos in zip(test_idx, test_pos):
                    test_preds_list.append((idx, test_fc.get(pos, float(v_df.loc[idx, "price_lkr"]))))
                    
            all_val_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in val_preds_list}, name=f"pred_{m_name}")
            all_test_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in test_preds_list}, name=f"pred_{m_name}")
            
        # 3. Classical ML
        X, y_raw, features = prepare_feature_matrices(df_feat, target_col=target_col)
        y_orig = df_feat["price_lkr"].clip(lower=1.0)
        y_ratio = np.log(np.clip(y_raw / y_orig, 1e-4, None))
        
        classical_models = cfg["models"]["classical_ml"]
        for m_name in classical_models:
            modes = ["raw_level"]
            if m_name in ratio_models_ml:
                modes.append("log_ratio")
                
            for mode in modes:
                print(f"  Running Classical ML: {m_name} (mode={mode})...")
                y_target = y_raw if mode == "raw_level" else y_ratio
                
                X_train, y_train = X[train_mask], y_target[train_mask]
                X_val, y_val = X[val_mask], y_target[val_mask]
                X_test, y_test = X[test_mask], y_target[test_mask]
                
                # Hyperparameter tuning
                n_t = 2 if m_name in ['catboost', 'random_forest', 'extra_trees', 'gradient_boosting', 'xgboost', 'lightgbm'] else 8
                best_params = tune_classical_model(m_name, X_train, y_train, horizon=h, n_trials=n_t)
                
                # Val fit
                m_val = get_classical_model(m_name, params=best_params)
                clean_tr = pd.notna(y_train)
                m_val.fit(X_train[clean_tr], y_train[clean_tr])
                p_val_raw = m_val.predict(X_val)
                
                # Test refit on train+val
                X_tr_val = pd.concat([X_train, X_val], axis=0)
                y_tr_val = pd.concat([y_train, y_val], axis=0)
                clean_tr_val = pd.notna(y_tr_val)
                
                m_final = get_classical_model(m_name, params=best_params)
                m_final.fit(X_tr_val[clean_tr_val], y_tr_val[clean_tr_val])
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
                
        # 4. Deep Learning
        dl_models = cfg["models"]["deep_learning"]
        for arch in dl_models:
            modes = ["raw_level"]
            if arch in ratio_models_dl:
                modes.append("log_ratio")
                
            for mode in modes:
                print(f"  Running Deep Learning: {arch} (mode={mode})...", flush=True)
                y_target = y_raw if mode == "raw_level" else y_ratio
                
                valid_tr = pd.notna(y_target[train_mask])
                valid_vl = pd.notna(y_target[val_mask])
                
                X_tr_mat = X[train_mask].values[valid_tr]
                y_tr_vec = y_target[train_mask].values[valid_tr]
                X_vl_fit = X[val_mask].values[valid_vl]
                y_vl_fit = y_target[val_mask].values[valid_vl]
                
                X_vl_eval = X[val_mask].values
                X_te_eval = X[test_mask].values
                
                p_val_raw, p_test_raw = train_dl_model(
                    arch, X_tr_mat, y_tr_vec, X_vl_fit, y_vl_fit, X_vl_eval, X_te_eval, epochs=10
                )
                
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
                
        # 5. Target Formulation Comparison & Winner Selection on Validation
        print("\n  Evaluating Target Mode Winners on Validation...")
        candidate_pool_modes = {}
        for m_name in classical_models + dl_models:
            if (m_name, "log_ratio") in all_val_preds:
                m_lvl = evaluate_predictions(y_val_true, all_val_preds[(m_name, "raw_level")], y_train_history=df_feat.loc[train_mask, "price_lkr"])
                m_rat = evaluate_predictions(y_val_true, all_val_preds[(m_name, "log_ratio")], y_train_history=df_feat.loc[train_mask, "price_lkr"])
                
                chosen = "log_ratio" if m_rat["MASE"] < m_lvl["MASE"] else "raw_level"
                candidate_pool_modes[m_name] = chosen
                gain = (1 - min(m_rat["MASE"], m_lvl["MASE"]) / max(m_rat["MASE"], m_lvl["MASE"])) * 100.0
                
                # Test skills
                m_lvl_te = evaluate_predictions(y_test_true, all_test_preds[(m_name, "raw_level")], y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"])
                m_rat_te = evaluate_predictions(y_test_true, all_test_preds[(m_name, "log_ratio")], y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"])
                m_naive_te = evaluate_predictions(y_test_true, all_test_preds[("naive", "raw_level")], y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"])
                
                sk_lvl = compute_skill_vs_naive(m_lvl_te["MASE"], m_naive_te["MASE"])
                sk_rat = compute_skill_vs_naive(m_rat_te["MASE"], m_naive_te["MASE"])
                
                target_comp_records.append({
                    "model": m_name, "horizon": h,
                    "val_MASE_level": round(m_lvl["MASE"], 4), "val_sMAPE_level": round(m_lvl["sMAPE"], 2),
                    "val_MASE_ratio": round(m_rat["MASE"], 4), "val_sMAPE_ratio": round(m_rat["sMAPE"], 2),
                    "chosen_target_mode": chosen, "val_MASE_gain_pct": round(gain, 2),
                    "test_MASE_level": round(m_lvl_te["MASE"], 4), "test_sMAPE_level": round(m_lvl_te["sMAPE"], 2), "test_skill_level": round(sk_lvl, 2),
                    "test_MASE_ratio": round(m_rat_te["MASE"], 4), "test_sMAPE_ratio": round(m_rat_te["sMAPE"], 2), "test_skill_ratio": round(sk_rat, 2)
                })
            else:
                candidate_pool_modes[m_name] = "raw_level"
                
        # 6. Ensembles using chosen modes
        candidate_names = classical_models + dl_models
        model_val_mases = {}
        for cm in candidate_names:
            c_mode = candidate_pool_modes[cm]
            val_s = all_val_preds[(cm, c_mode)]
            res = evaluate_predictions(y_val_true, val_s, y_train_history=df_feat.loc[train_mask, "price_lkr"])
            model_val_mases[cm] = res["MASE"]
            
        sorted_candidates = sorted(model_val_mases.items(), key=lambda x: x[1])
        top3_names = [x[0] for x in sorted_candidates[:3]]
        print(f"  Top 3 Models for Ensemble (h={h}): {top3_names}")
        
        # Simple Average Top-3
        avg_ens = SimpleAverageEnsemble(top3_names)
        val_ens_p = avg_ens.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in top3_names})
        test_ens_p = avg_ens.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in top3_names})
        all_val_preds[("simple_average_top3", "raw_level")] = pd.Series(val_ens_p, index=y_val_true.index, name="pred_simple_average_top3")
        all_test_preds[("simple_average_top3", "raw_level")] = pd.Series(test_ens_p, index=y_test_true.index, name="pred_simple_average_top3")
        
        # Stacking Meta Learner
        clean_vl = pd.notna(y_val_true.values)
        stacker = StackingMetaLearner(candidate_names)
        stacker.fit({m: all_val_preds[(m, candidate_pool_modes[m])].values[clean_vl] for m in candidate_names}, y_val_true.values[clean_vl])
        val_stack_p = stacker.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in candidate_names})
        test_stack_p = stacker.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in candidate_names})
        all_val_preds[("stacking_meta_learner", "raw_level")] = pd.Series(val_stack_p, index=y_val_true.index, name="pred_stacking_meta_learner")
        all_test_preds[("stacking_meta_learner", "raw_level")] = pd.Series(test_stack_p, index=y_test_true.index, name="pred_stacking_meta_learner")
        
        # Best Per Category
        cat_ens = BestPerCategoryEnsemble()
        cat_ens.fit({m: all_val_preds[(m, candidate_pool_modes[m])].values[clean_vl] for m in candidate_names}, y_val_true.values[clean_vl], df_feat.loc[val_mask, "category"].values[clean_vl])
        val_cat_p = cat_ens.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in candidate_names}, df_feat.loc[val_mask, "category"])
        test_cat_p = cat_ens.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in candidate_names}, df_feat.loc[test_mask, "category"])
        all_val_preds[("best_per_category", "raw_level")] = pd.Series(val_cat_p, index=y_val_true.index, name="pred_best_per_category")
        all_test_preds[("best_per_category", "raw_level")] = pd.Series(test_cat_p, index=y_test_true.index, name="pred_best_per_category")
        
        # 7. Metrics, CIs, DM tests for ALL (model, mode) pairs
        naive_val_p = all_val_preds[("naive", "raw_level")]
        naive_test_p = all_test_preds[("naive", "raw_level")]
        m_naive_val = evaluate_predictions(y_val_true, naive_val_p, y_train_history=df_feat.loc[train_mask, "price_lkr"])
        m_naive_test = evaluate_predictions(y_test_true, naive_test_p, y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"])
        
        all_models_modes = list(all_val_preds.keys())
        
        for (m_name, mode) in all_models_modes:
            val_p = all_val_preds[(m_name, mode)]
            test_p = all_test_preds[(m_name, mode)]
            
            # Conformal calibration on val_cal_mask
            conformal = ScaleAwareConformalPredictor(alpha_levels=(0.20, 0.05))
            val_cal_pred = val_p.loc[val_cal_mask]
            conformal.calibrate(y_cal_true, val_cal_pred)
            test_intervals = conformal.predict_intervals(test_p)
            
            cov_test_80 = evaluate_interval_quality(y_test_true, test_intervals["lower_80"], test_intervals["upper_80"], y_pred=test_p, metadata_df=df_feat.loc[test_mask])
            cov_test_95 = evaluate_interval_quality(y_test_true, test_intervals["lower_95"], test_intervals["upper_95"], y_pred=test_p, metadata_df=df_feat.loc[test_mask])
            
            val_mets = evaluate_predictions(y_val_true, val_p, y_train_history=df_feat.loc[train_mask, "price_lkr"], y_prev=y_origin_val)
            test_mets = evaluate_predictions(y_test_true, test_p, y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"], y_prev=y_origin_test)
            
            sk_val = compute_skill_vs_naive(val_mets["MASE"], m_naive_val["MASE"])
            sk_test = compute_skill_vs_naive(test_mets["MASE"], m_naive_test["MASE"])
            
            # Bootstrap test CIs (250 resamples)
            boot_res = block_bootstrap_mase(
                y_test_true, test_p, y_naive_pred=naive_test_p,
                y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"],
                week_indices=df_feat.loc[test_mask, "week_index"],
                block_length=4, n_boot=250
            )
            
            # DM test vs Naive
            dm_stat, dm_pval = diebold_mariano_test(
                y_test_true, test_p, naive_test_p, h=h,
                week_indices=df_feat.loc[test_mask, "week_index"]
            )
            
            # Record Validation
            leaderboard_records.append({
                "model": m_name, "target_mode": mode, "horizon": h, "split": "validation",
                "MAE": val_mets["MAE"], "RMSE": val_mets["RMSE"], "MAPE": val_mets["MAPE"], "sMAPE": val_mets["sMAPE"],
                "MASE": val_mets["MASE"], "R2": val_mets["R2"], "Bias": val_mets["Bias"],
                "Directional_Accuracy": val_mets["Directional_Accuracy"],
                "Skill_vs_Naive": round(float(sk_val), 2) if pd.notna(sk_val) else np.nan,
                "n_obs": val_mets["n_obs"],
                "Coverage_80": np.nan, "Width_80_LKR": np.nan, "Width_80_Pct": np.nan,
                "Coverage_95": np.nan, "Width_95_LKR": np.nan, "Width_95_Pct": np.nan,
                "MASE_CI_95": np.nan, "Diff_Naive_CI_95": np.nan, "DM_stat_vs_Naive": np.nan, "DM_pval_vs_Naive": np.nan
            })
            
            # Record Test
            leaderboard_records.append({
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

        # Record per-vegetable performance for chosen mode
        all_unique_models = sorted(list(set([m for (m, _) in all_models_modes])))
        for m_name in all_unique_models:
            c_mode = candidate_pool_modes.get(m_name, "raw_level")
            val_p = all_val_preds[(m_name, c_mode)]
            test_p = all_test_preds[(m_name, c_mode)]
            for veg in df_feat["product_name"].unique():
                v_mask = df_feat["product_name"] == veg
                v_val_mask = val_mask & v_mask
                v_test_mask = test_mask & v_mask
                v_m_val = evaluate_predictions(
                    df_feat.loc[v_val_mask, target_col], val_p.loc[v_val_mask],
                    y_train_history=df_feat.loc[train_mask & v_mask, "price_lkr"],
                    y_prev=df_feat.loc[v_val_mask, "price_lkr"]
                )
                v_m_test = evaluate_predictions(
                    df_feat.loc[v_test_mask, target_col], test_p.loc[v_test_mask],
                    y_train_history=df_feat.loc[(train_mask | val_mask) & v_mask, "price_lkr"],
                    y_prev=df_feat.loc[v_test_mask, "price_lkr"]
                )
                by_veg_records.append({
                    "model": m_name, "horizon": h, "vegetable": veg,
                    "val_MAE": v_m_val["MAE"], "val_MASE": v_m_val["MASE"], "val_sMAPE": v_m_val["sMAPE"],
                    "test_MAE": v_m_test["MAE"], "test_RMSE": v_m_test["RMSE"],
                    "test_sMAPE": v_m_test["sMAPE"], "test_MASE": v_m_test["MASE"],
                    "test_R2": v_m_test["R2"], "test_DA": v_m_test["Directional_Accuracy"]
                })
            
        all_val_preds_by_h[h] = all_val_preds
        val_truth_by_h[h] = y_val_true
        train_hist_by_h[h] = df_feat.loc[train_mask, "price_lkr"]
        val_weeks_by_h[h] = df_feat.loc[val_mask, "week_index"]

        # Checkpoint after each horizon completes
        pd.DataFrame(leaderboard_records).to_csv("experiments/leaderboard.csv", index=False)
        pd.DataFrame(target_comp_records).to_csv("results/tables/target_formulation_comparison.csv", index=False)
        pd.DataFrame(by_veg_records).to_csv("experiments/leaderboard_by_vegetable.csv", index=False)
        print(f"\n>>> Horizon h={h} complete! Checkpointed to experiments/leaderboard.csv and leaderboard_by_vegetable.csv <<<\n")

    df_lead = pd.DataFrame(leaderboard_records)
    
    # 8. Apply Holm-Bonferroni correction on Test DM p-values within horizon
    df_lead["DM_pval_Holm_vs_Naive"] = np.nan
    test_mask_lead = df_lead["split"] == "test"
    for h in horizons:
        h_idx = df_lead[test_mask_lead & (df_lead["horizon"] == h)].index
        p_raw = df_lead.loc[h_idx, "DM_pval_vs_Naive"].values
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
        df_lead.loc[h_idx, "DM_pval_Holm_vs_Naive"] = holm_vals

    # 9. Automated Assertion Checks on Test Split
    print("\n" + "="*70 + "\nRUNNING AUTOMATED STATISTICAL ASSERTION CHECKS\n" + "="*70)
    test_rows = df_lead[df_lead["split"] == "test"]
    naive_mase_by_h = {h: df_lead[(df_lead["split"] == "test") & (df_lead["model"] == "naive") & (df_lead["horizon"] == h)]["MASE"].values[0] for h in horizons}
    
    check_failures = []
    for idx, row in test_rows.iterrows():
        m = row["model"]
        mode = row["target_mode"]
        h = row["horizon"]
        mase = row["MASE"]
        naive_mase = naive_mase_by_h[h]
        diff_point = round(mase - naive_mase, 4)
        
        ci_str = str(row["Diff_Naive_CI_95"])
        if ci_str and ci_str != "nan" and m != "naive":
            ci_low, ci_high = [float(x) for x in ci_str.strip("[]").split(",")]
            # Check (a): CI contains point MASE difference
            if not (ci_low - 0.008 <= diff_point <= ci_high + 0.008):
                msg = f"[Check a FAIL] {m} ({mode}) h={h}: Point diff {diff_point} not in CI [{ci_low}, {ci_high}]"
                check_failures.append(msg)
                print(msg)
                
            # Check (b): DM stat sign agrees with MASE difference sign
            dm_stat = row["DM_stat_vs_Naive"]
            if pd.notna(dm_stat) and abs(diff_point) > 0.01:
                if (diff_point < -0.01 and dm_stat > 0.2) or (diff_point > 0.01 and dm_stat < -0.2):
                    msg = f"[Check b FAIL] {m} ({mode}) h={h}: Diff sign {np.sign(diff_point)} != DM sign {np.sign(dm_stat)} (diff={diff_point}, dm={dm_stat})"
                    check_failures.append(msg)
                    print(msg)
                    
            # Check (c): Holm p >= raw p
            raw_p = row["DM_pval_vs_Naive"]
            holm_p = row["DM_pval_Holm_vs_Naive"]
            if pd.notna(raw_p) and pd.notna(holm_p):
                if holm_p < raw_p - 1e-6:
                    msg = f"[Check c FAIL] {m} ({mode}) h={h}: Holm p ({holm_p}) < raw p ({raw_p})"
                    check_failures.append(msg)
                    print(msg)

    if len(check_failures) == 0:
        print("ALL AUTOMATED CHECKS PASSED 100%! (Zero failures across all models and horizons)")
    else:
        print(f"WARNING: {len(check_failures)} checks failed!")

    # Save leaderboard.csv
    df_lead.to_csv("experiments/leaderboard.csv", index=False)
    print("Saved experiments/leaderboard.csv")
    
    # Save target formulation comparison
    df_tc = pd.DataFrame(target_comp_records)
    df_tc.to_csv("results/tables/target_formulation_comparison.csv", index=False)
    print("Saved results/tables/target_formulation_comparison.csv")
    
    # 10. Pre-registered Model Selection Rule over Final Candidate Set
    print("\n" + "="*70 + "\nAPPLYING PRE-REGISTERED 1-SE SIMPLICITY SELECTION RULE\n" + "="*70)
    baselines = ["naive", "drift", "moving_average_4", "moving_average_12", "seasonal_naive_48"]
    
    def get_tier(m):
        if m in ["linear_regression", "ridge", "lasso", "elastic_net", "auto_arima", "sarimax", "holt_winters_ets", "prophet"]:
            return (1, "Linear/Statistical")
        elif m in ["lightgbm", "xgboost", "catboost", "random_forest", "extra_trees", "gradient_boosting", "svr"]:
            return (2, "Tree/Ensemble ML")
        elif m in ["mlp", "lstm", "gru", "tcn_1d", "nbeats", "transformer", "nhits", "tft_lite"]:
            return (3, "Deep Learning")
        elif m in ["simple_average_top3", "stacking_meta_learner", "best_per_category"]:
            return (4, "Ensemble Paradigm")
        return (99, "Other")

    selection_records = []
    selected_manifest = {}
    
    for h in horizons:
        # Candidate set: exclude baselines
        sub = df_lead[(df_lead["horizon"] == h) & (df_lead["split"] == "validation")].copy()
        sub = sub[~sub["model"].isin(baselines)]
        
        # Filter each model to its chosen mode on validation
        valid_candidates = []
        for m in sub["model"].unique():
            m_rows = sub[sub["model"] == m]
            best_mode_row = m_rows.sort_values("MASE").iloc[0]
            valid_candidates.append(best_mode_row)
            
        cands = pd.DataFrame(valid_candidates)
        cands["tier"] = cands["model"].apply(lambda m: get_tier(m)[0])
        cands["tier_name"] = cands["model"].apply(lambda m: get_tier(m)[1])
        cands = cands.sort_values("MASE").reset_index(drop=True)
        
        best = cands.iloc[0]
        best_m = best["MASE"]
        
        # 1 SE from validation bootstrap CIs:
        # Bootstrap SE on validation predictions
        best_val_preds = all_val_preds_by_h[h][(best["model"], best["target_mode"])]
        naive_val_preds = all_val_preds_by_h[h][("naive", "raw_level")]
        boot_best = block_bootstrap_mase(
            val_truth_by_h[h], best_val_preds, y_naive_pred=naive_val_preds,
            y_train_history=train_hist_by_h[h],
            week_indices=val_weeks_by_h[h],
            block_length=4, n_boot=250
        )
        se_val = (boot_best["mase_ci_high"] - boot_best["mase_ci_low"]) / (2 * 1.96)
        thresh = best_m + se_val
        
        in_band = cands[cands["MASE"] <= thresh].sort_values(["tier", "MASE"]).reset_index(drop=True)
        chosen = in_band.iloc[0]
        
        # Test performance of chosen model
        test_chosen = df_lead[(df_lead["horizon"] == h) & (df_lead["split"] == "test") & (df_lead["model"] == chosen["model"]) & (df_lead["target_mode"] == chosen["target_mode"])].iloc[0]
        
        print(f"Horizon h={h:2d}:")
        print(f"  Best Val Model: {best['model']} ({best['target_mode']}, Tier {best['tier']}) - Val MASE={best_m:.4f}, SE={se_val:.4f}, 1-SE Band=[{best_m:.4f}, {thresh:.4f}]")
        print(f"  Candidate Models in Band ({len(in_band)} models): {[(r['model'], r['target_mode'], r['tier_name'], round(r['MASE'], 4)) for _, r in in_band.iterrows()]}")
        print(f"  >> SELECTED MODEL: {chosen['model']} ({chosen['target_mode']}, Tier {chosen['tier_name']}) - Val MASE={chosen['MASE']:.4f} | Test MASE={test_chosen['MASE']:.4f}, Skill={test_chosen['Skill_vs_Naive']}%, Holm-p={test_chosen['DM_pval_Holm_vs_Naive']}")
        
        selected_manifest[f"h{h}"] = {
            "model": chosen["model"],
            "target_mode": chosen["target_mode"],
            "tier": chosen["tier_name"],
            "val_mase": chosen["MASE"],
            "band": [round(best_m, 4), round(thresh, 4)],
            "test_mase": test_chosen["MASE"],
            "test_skill": test_chosen["Skill_vs_Naive"],
            "holm_p": test_chosen["DM_pval_Holm_vs_Naive"]
        }
        
        selection_records.append({
            "horizon": h,
            "best_model": best["model"],
            "best_target_mode": best["target_mode"],
            "best_val_mase": round(best_m, 4),
            "se_val": round(se_val, 4),
            "band_lower": round(best_m, 4),
            "band_upper": round(thresh, 4),
            "n_in_band": len(in_band),
            "selected_model": chosen["model"],
            "selected_target_mode": chosen["target_mode"],
            "selected_tier": chosen["tier_name"],
            "selected_val_mase": round(chosen["MASE"], 4),
            "selected_test_mase": round(test_chosen["MASE"], 4),
            "selected_test_skill": test_chosen["Skill_vs_Naive"],
            "selected_test_holm_p": test_chosen["DM_pval_Holm_vs_Naive"]
        })

    df_sel = pd.DataFrame(selection_records)
    df_sel.to_csv("results/tables/model_selection_bands.csv", index=False)
    print("\nSaved results/tables/model_selection_bands.csv")
    
    # Update run manifest
    manifest_path = Path("experiments/run_manifest.json")
    manifest = {}
    if manifest_path.exists():
        with open(manifest_path, "r") as f:
            manifest = json.load(f)
    manifest["selected_models_by_horizon"] = selected_manifest
    manifest["primary_selected_model"] = selected_manifest["h4"]["model"]
    manifest["primary_selected_target_mode"] = selected_manifest["h4"]["target_mode"]
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    print("Updated experiments/run_manifest.json")
    
    # 11. Compare Old vs New Leaderboard
    if df_old_lead is not None:
        print("\n" + "="*70 + "\nOLD vs NEW LEADERBOARD COMPARISON (Test Set)\n" + "="*70)
        for h in horizons:
            old_h = df_old_lead[(df_old_lead["split"] == "test") & (df_old_lead["horizon"] == h)]
            new_h = df_lead[(df_lead["split"] == "test") & (df_lead["horizon"] == h) & (df_lead["target_mode"] == "raw_level")]
            print(f"Horizon h={h}:")
            print(f"  Old test N_obs: {old_h['n_obs'].iloc[0]} -> New test N_obs: {new_h['n_obs'].iloc[0]}")
            old_naive = old_h[old_h["model"] == "naive"]["MASE"].values[0]
            new_naive = new_h[new_h["model"] == "naive"]["MASE"].values[0]
            print(f"  Naive Test MASE: Old={old_naive:.4f} -> New={new_naive:.4f}")
            old_lasso = old_h[old_h["model"] == "lasso"]["MASE"].values[0] if "lasso" in old_h["model"].values else np.nan
            new_lasso = new_h[new_h["model"] == "lasso"]["MASE"].values[0]
            print(f"  Lasso Level Test MASE: Old={old_lasso:.4f} -> New={new_lasso:.4f}")
            if "lasso" in df_lead["model"].values and len(df_lead[(df_lead["split"] == "test") & (df_lead["horizon"] == h) & (df_lead["model"] == "lasso") & (df_lead["target_mode"] == "log_ratio")]) > 0:
                new_lasso_rat = df_lead[(df_lead["split"] == "test") & (df_lead["horizon"] == h) & (df_lead["model"] == "lasso") & (df_lead["target_mode"] == "log_ratio")]["MASE"].values[0]
                print(f"  Lasso Log-Ratio Test MASE: {new_lasso_rat:.4f} (Skill: {df_lead[(df_lead['split'] == 'test') & (df_lead['horizon'] == h) & (df_lead['model'] == 'lasso') & (df_lead['target_mode'] == 'log_ratio')]['Skill_vs_Naive'].values[0]:+.2f}%)")

if __name__ == "__main__":
    run()
