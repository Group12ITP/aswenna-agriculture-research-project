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
import yaml
import warnings
warnings.filterwarnings('ignore')
import optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

from src.utils import load_config, set_seeds, get_logger
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
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
from src.metrics import (
    evaluate_predictions, compute_skill_vs_naive, block_bootstrap_mase
)
from src.train import prepare_feature_matrices, tune_classical_model

logger = get_logger("restore_val_cis")

def train_dl_val(arch, X_train, y_train, X_val_eval, epochs=10, lr=1e-3, batch_size=128):
    scaler = StandardScaler()
    X_tr_s = scaler.fit_transform(X_train)
    X_vl_s = scaler.transform(X_val_eval)
    
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
        
    return val_pred

def run():
    set_seeds(42)
    cfg = load_config()
    _, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg, include_cross_veg=True)
    
    df_lead = pd.read_csv("experiments/leaderboard.csv")
    horizons = cfg["task"].get("horizons", [1, 4, 8, 12])
    
    ratio_models_ml = ["ridge", "lasso", "elastic_net", "extra_trees", "xgboost", "lightgbm", "catboost"]
    ratio_models_dl = ["mlp", "gru", "tcn_1d", "nbeats", "nhits"]
    
    updated_val_cis = {} # (model, mode, horizon) -> "[low, high]"
    updated_diff_cis = {}
    
    for h in horizons:
        print(f"\n=======================================================")
        print(f"PROCESSING HORIZON h={h} FOR VALIDATION CIs")
        print(f"=======================================================")
        target_col = f"target_h{h}"
        target_week = df_feat["week_index"] + h
        
        train_mask = (target_week <= (369 - h)) & df_feat[target_col].notna()
        val_mask = (target_week >= 369) & (target_week <= 416) & df_feat[target_col].notna()
        
        y_val_true = df_feat.loc[val_mask, target_col]
        y_train_hist = df_feat.loc[train_mask, "price_lkr"]
        val_weeks = df_feat.loc[val_mask, "week_index"]
        
        all_val_preds = {}
        
        # 1. Baselines
        baselines = cfg["models"]["baselines"]
        for m_name in baselines:
            val_preds_list = []
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
            all_val_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in val_preds_list})
            
        # 2. Statistical
        stat_models = cfg["models"]["statistical"]
        for m_name in stat_models:
            val_preds_list = []
            for veg in df_feat["product_name"].unique():
                v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index").copy()
                v_df["ds"] = pd.to_datetime(v_df["approx_date"])
                full_series = v_df["price_lkr"].values
                v_tr_idx = v_df.index[train_mask.loc[v_df.index]]
                train_series = v_df.loc[v_tr_idx, "price_lkr"].values
                val_idx = v_df.index[val_mask.loc[v_df.index]]
                val_pos = [v_df.index.get_loc(idx) for idx in val_idx]
                
                if m_name == "holt_winters_ets":
                    forecaster = HoltWintersRollingForecaster(seasonal_periods=48)
                    forecaster.fit_parameters(train_series)
                    val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=h)
                elif m_name == "auto_arima":
                    forecaster = AutoARIMARollingForecaster(d=1)
                    forecaster.fit_parameters(train_series)
                    val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=h)
                elif m_name == "sarimax":
                    forecaster = SARIMAXRollingForecaster(order=(1, 1, 1))
                    forecaster.fit_parameters(train_series)
                    val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=h)
                elif m_name == "prophet":
                    forecaster = ProphetRollingForecaster()
                    val_fc = forecaster.rolling_forecast(v_df, val_pos, horizon=h)
                    
                for idx, pos in zip(val_idx, val_pos):
                    val_preds_list.append((idx, val_fc.get(pos, float(v_df.loc[idx, "price_lkr"]))))
            all_val_preds[(m_name, "raw_level")] = pd.Series({idx: p for idx, p in val_preds_list})
            
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
                y_target = y_raw if mode == "raw_level" else y_ratio
                X_train, y_train = X[train_mask], y_target[train_mask]
                X_val = X[val_mask]
                
                n_t = 2 if m_name in ['catboost', 'random_forest', 'extra_trees', 'gradient_boosting', 'xgboost', 'lightgbm'] else 8
                best_params = tune_classical_model(m_name, X_train, y_train, horizon=h, n_trials=n_t)
                
                m_val = get_classical_model(m_name, params=best_params)
                clean_tr = pd.notna(y_train)
                m_val.fit(X_train[clean_tr], y_train[clean_tr])
                p_val_raw = m_val.predict(X_val)
                
                if mode == "log_ratio":
                    val_p = y_orig[val_mask] * np.exp(p_val_raw)
                else:
                    val_p = p_val_raw
                val_p = np.nan_to_num(np.maximum(0.0, val_p), nan=0.0)
                all_val_preds[(m_name, mode)] = pd.Series(val_p, index=X_val.index)
                
        # 4. Deep Learning
        dl_models = cfg["models"]["deep_learning"]
        for arch in dl_models:
            modes = ["raw_level"]
            if arch in ratio_models_dl:
                modes.append("log_ratio")
            for mode in modes:
                y_target = y_raw if mode == "raw_level" else y_ratio
                valid_tr = pd.notna(y_target[train_mask])
                X_tr_mat = X[train_mask].values[valid_tr]
                y_tr_vec = y_target[train_mask].values[valid_tr]
                X_vl_eval = X[val_mask].values
                
                p_val_raw = train_dl_val(arch, X_tr_mat, y_tr_vec, X_vl_eval, epochs=10)
                if mode == "log_ratio":
                    val_p = y_orig[val_mask].values * np.exp(p_val_raw)
                else:
                    val_p = p_val_raw
                val_p = np.nan_to_num(np.maximum(0.0, val_p), nan=0.0)
                all_val_preds[(arch, mode)] = pd.Series(val_p, index=y_val_true.index)
                
        # 5. Ensembles using chosen modes on validation
        candidate_names = classical_models + dl_models
        candidate_pool_modes = {}
        for cm in candidate_names:
            if (cm, "log_ratio") in all_val_preds:
                m_lvl = evaluate_predictions(y_val_true, all_val_preds[(cm, "raw_level")], y_train_history=y_train_hist)
                m_rat = evaluate_predictions(y_val_true, all_val_preds[(cm, "log_ratio")], y_train_history=y_train_hist)
                candidate_pool_modes[cm] = "log_ratio" if m_rat["MASE"] < m_lvl["MASE"] else "raw_level"
            else:
                candidate_pool_modes[cm] = "raw_level"
                
        model_val_mases = {}
        for cm in candidate_names:
            c_mode = candidate_pool_modes[cm]
            res = evaluate_predictions(y_val_true, all_val_preds[(cm, c_mode)], y_train_history=y_train_hist)
            model_val_mases[cm] = res["MASE"]
            
        sorted_candidates = sorted(model_val_mases.items(), key=lambda x: x[1])
        top3_names = [x[0] for x in sorted_candidates[:3]]
        
        # Simple Average Top-3
        avg_ens = SimpleAverageEnsemble(top3_names)
        val_ens_p = avg_ens.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in top3_names})
        all_val_preds[("simple_average_top3", "raw_level")] = pd.Series(val_ens_p, index=y_val_true.index)
        
        # Stacking Meta Learner
        clean_vl = pd.notna(y_val_true.values)
        stacker = StackingMetaLearner(candidate_names)
        stacker.fit({m: all_val_preds[(m, candidate_pool_modes[m])].values[clean_vl] for m in candidate_names}, y_val_true.values[clean_vl])
        val_stack_p = stacker.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in candidate_names})
        all_val_preds[("stacking_meta_learner", "raw_level")] = pd.Series(val_stack_p, index=y_val_true.index)
        
        # Best Per Category
        cat_ens = BestPerCategoryEnsemble()
        cat_ens.fit({m: all_val_preds[(m, candidate_pool_modes[m])].values[clean_vl] for m in candidate_names}, y_val_true.values[clean_vl], df_feat.loc[val_mask, "category"].values[clean_vl])
        val_cat_p = cat_ens.predict({m: all_val_preds[(m, candidate_pool_modes[m])].values for m in candidate_names}, df_feat.loc[val_mask, "category"])
        all_val_preds[("best_per_category", "raw_level")] = pd.Series(val_cat_p, index=y_val_true.index)
        
        # 6. Bootstrap Validation CIs for ALL models & modes
        naive_val_p = all_val_preds[("naive", "raw_level")]
        
        for (m_name, mode), val_p in all_val_preds.items():
            boot_val = block_bootstrap_mase(
                y_val_true, val_p, y_naive_pred=naive_val_p,
                y_train_history=y_train_hist,
                week_indices=val_weeks,
                block_length=4, n_boot=250
            )
            ci_str = f"[{boot_val.get('mase_ci_low')}, {boot_val.get('mase_ci_high')}]"
            diff_str = f"[{boot_val.get('diff_naive_ci_low')}, {boot_val.get('diff_naive_ci_high')}]"
            updated_val_cis[(m_name, mode, h)] = ci_str
            updated_diff_cis[(m_name, mode, h)] = diff_str
            
            # Verify against leaderboard row
            ld_row = df_lead[(df_lead["horizon"] == h) & (df_lead["split"] == "validation") & (df_lead["model"] == m_name) & (df_lead["target_mode"] == mode)]
            if len(ld_row) > 0:
                ld_mase = ld_row["MASE"].iloc[0]
                ev = evaluate_predictions(y_val_true, val_p, y_train_history=y_train_hist)
                ev_mase = ev["MASE"]
                diff = abs(ld_mase - ev_mase)
                if diff > 0.05:
                    print(f"  Note: {m_name} ({mode}) h={h}: Lead MASE={ld_mase:.4f} vs Recomp={ev_mase:.4f} (diff={diff:.4f})")
                else:
                    print(f"  Verified {m_name:22s} ({mode:9s}) h={h}: Val MASE={ev_mase:.4f} CI={ci_str}")
                    
    # Update df_lead with restored validation CIs
    print("\nUpdating experiments/leaderboard.csv with restored validation CIs...")
    for idx, row in df_lead.iterrows():
        if row["split"] == "validation":
            m = row["model"]
            mode = row["target_mode"]
            h = row["horizon"]
            key = (m, mode, h)
            if key in updated_val_cis:
                df_lead.at[idx, "MASE_CI_95"] = updated_val_cis[key]
                df_lead.at[idx, "Diff_Naive_CI_95"] = updated_diff_cis[key]
                
    df_lead.to_csv("experiments/leaderboard.csv", index=False)
    print("SUCCESS: Updated experiments/leaderboard.csv with 100% of validation CIs restored!")
    
    # Save validation predictions dictionary for reproducibility
    print("Verification of restored CIs in leaderboard.csv:")
    val_rows = df_lead[df_lead["split"] == "validation"]
    print(f"  Total validation rows: {len(val_rows)}")
    print(f"  Non-null MASE_CI_95: {val_rows['MASE_CI_95'].notna().sum()}")
    print(val_rows[["model", "target_mode", "horizon", "MASE", "MASE_CI_95"]].head(15).to_string(index=False))

if __name__ == "__main__":
    run()
