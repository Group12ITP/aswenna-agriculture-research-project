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
import warnings
warnings.filterwarnings('ignore')

from src.utils import load_config, set_seeds, get_logger
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.models.baselines import (
    NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster, DriftForecaster,
    RollingMeanForecaster, SeasonalMean4YrForecaster, AR1CategoryMeanForecaster
)
from src.models.classical import get_classical_model
from src.models.deep_learning import (
    MLPNet, LSTMNet, GRUNet, TCNNet, NBeatsNet, TransformerNet, NHiTSNet, TFTLiteNet, device
)
from src.models.ensembles import SimpleAverageEnsemble, StackingMetaLearner, BestPerCategoryEnsemble
from src.metrics import evaluate_predictions, diebold_mariano_test
from src.train import prepare_feature_matrices

def train_dl_test_purged(arch, X_rf, y_rf, X_te_eval, epochs=6, lr=1e-3, batch_size=128):
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

def run_dm_vs_seasonal_mean():
    cfg = load_config()
    set_seeds(cfg.get("random_seed", 42))
    
    print("Loading data and engineering features...")
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    
    horizons = [4, 8, 12]
    
    ratio_models_ml = ["lasso", "ridge", "elastic_net", "lightgbm", "xgboost", "catboost", "extra_trees"]
    ratio_models_dl = ["mlp", "tcn_1d", "gru", "nbeats", "nhits"]
    
    all_dm_records = []
    selected_models_records = []
    
    selected_by_horizon = {
        4: ("auto_arima", "raw_level"),
        8: ("catboost", "log_ratio"),
        12: ("transformer", "raw_level")
    }
    
    for h in horizons:
        print(f"\n=======================================================")
        print(f"EVALUATING DM TESTS VS SEASONAL_MEAN_4YR AT h = {h}")
        print(f"=======================================================")
        train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
        target_col = f"target_h{h}"
        target_week = df_feat["week_index"] + h
        max_allowed_refit_target = 417 - h
        refit_mask = train_mask | (val_mask & (target_week <= max_allowed_refit_target))
        val_purged_idx = val_mask & (target_week <= max_allowed_refit_target)
        
        y_test_true = df_feat.loc[test_mask, target_col]
        y_val_true = df_feat.loc[val_mask, target_col]
        test_weeks = df_feat.loc[test_mask, "week_index"]
        
        all_test_preds = {}
        all_val_preds = {}
        
        # 1. Baselines
        baselines = cfg["models"]["baselines"] + ["rolling_52wk_mean", "seasonal_mean_4yr", "ar1_category_mean"]
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
                elif m_name == "seasonal_naive_48":
                    model = SeasonalNaiveForecaster(season_m=48)
                elif m_name == "moving_average_4":
                    model = MovingAverageForecaster(window=4)
                elif m_name == "moving_average_12":
                    model = MovingAverageForecaster(window=12)
                elif m_name == "drift":
                    model = DriftForecaster()
                elif m_name == "rolling_52wk_mean":
                    model = RollingMeanForecaster(window=52)
                elif m_name == "seasonal_mean_4yr":
                    model = SeasonalMean4YrForecaster(season_m=48, n_years=4)
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
            
        # 2. Statistical models
        stat_models = ["holt_winters_ets", "auto_arima", "sarimax", "prophet"]
        for m_name in stat_models:
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
                X_val, y_val = X[val_mask], y_target[val_mask]
                X_test = X[test_mask]
                
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
                
                # Test refit on purged data
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
                
        # 4. Deep Learning
        dl_models = cfg["models"]["deep_learning"]
        for arch in dl_models:
            modes = ["raw_level"]
            if arch in ratio_models_dl:
                modes.append("log_ratio")
                
            for mode in modes:
                y_target = y_raw if mode == "raw_level" else y_ratio
                valid_tr = pd.notna(y_target[train_mask])
                valid_rf = pd.notna(y_target[refit_mask])
                
                X_tr_mat = X[train_mask].values[valid_tr]
                y_tr_vec = y_target[train_mask].values[valid_tr]
                X_vl_eval = X[val_mask].values
                X_te_eval = X[test_mask].values
                
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
                    
                # Test fit on purged refit
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
                
        # 5. Ensembles
        candidate_pool_modes = {}
        for cm in classical_models + dl_models:
            if (cm, "log_ratio") in all_val_preds:
                m_lvl = evaluate_predictions(y_val_true, all_val_preds[(cm, "raw_level")], y_train_history=df_feat.loc[train_mask, "price_lkr"])
                m_rat = evaluate_predictions(y_val_true, all_val_preds[(cm, "log_ratio")], y_train_history=df_feat.loc[train_mask, "price_lkr"])
                candidate_pool_modes[cm] = "log_ratio" if m_rat["MASE"] < m_lvl["MASE"] else "raw_level"
            else:
                candidate_pool_modes[cm] = "raw_level"
                
        candidate_names = classical_models + dl_models
        model_val_mases = {}
        for cm in candidate_names:
            c_mode = candidate_pool_modes[cm]
            val_s = all_val_preds[(cm, c_mode)]
            res = evaluate_predictions(y_val_true, val_s, y_train_history=df_feat.loc[train_mask, "price_lkr"])
            model_val_mases[cm] = res["MASE"]
            
        sorted_candidates = sorted(model_val_mases.items(), key=lambda x: x[1])
        top3_names = [x[0] for x in sorted_candidates[:3]]
        
        avg_ens = SimpleAverageEnsemble(top3_names)
        test_ens_p = avg_ens.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in top3_names})
        all_test_preds[("simple_average_top3", "raw_level")] = pd.Series(test_ens_p, index=y_test_true.index, name="pred_simple_average_top3")
        
        clean_vl_purged = pd.notna(df_feat.loc[val_purged_idx, target_col].values)
        stacker = StackingMetaLearner(candidate_names)
        stacker.fit(
            {m: all_val_preds[(m, candidate_pool_modes[m])].loc[val_purged_idx].values[clean_vl_purged] for m in candidate_names},
            df_feat.loc[val_purged_idx, target_col].values[clean_vl_purged]
        )
        test_stack_p = stacker.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in candidate_names})
        all_test_preds[("stacking_meta_learner", "raw_level")] = pd.Series(test_stack_p, index=y_test_true.index, name="pred_stacking_meta_learner")
        
        cat_ens = BestPerCategoryEnsemble()
        cat_ens.fit(
            {m: all_val_preds[(m, candidate_pool_modes[m])].loc[val_purged_idx].values[clean_vl_purged] for m in candidate_names},
            df_feat.loc[val_purged_idx, target_col].values[clean_vl_purged],
            df_feat.loc[val_purged_idx, "category"].values[clean_vl_purged]
        )
        test_cat_p = cat_ens.predict({m: all_test_preds[(m, candidate_pool_modes[m])].values for m in candidate_names}, df_feat.loc[test_mask, "category"])
        all_test_preds[("best_per_category", "raw_level")] = pd.Series(test_cat_p, index=y_test_true.index, name="pred_best_per_category")
        
        # -------------------------------------------------------------
        # 6. Compute DM Tests vs Seasonal Mean 4-Year
        # -------------------------------------------------------------
        sm4yr_pred = all_test_preds[("seasonal_mean_4yr", "raw_level")]
        mets_sm4yr = evaluate_predictions(y_test_true, sm4yr_pred, y_train_history=df_feat.loc[refit_mask, "price_lkr"])
        sm4yr_mase = mets_sm4yr["MASE"]
        sm4yr_mae = mets_sm4yr["MAE"]
        
        print(f"seasonal_mean_4yr at h={h}: MAE = {sm4yr_mae:.2f} Rs, MASE = {sm4yr_mase:.4f}")
        
        horizon_records = []
        for (m_name, mode), test_p in all_test_preds.items():
            mets = evaluate_predictions(y_test_true, test_p, y_train_history=df_feat.loc[refit_mask, "price_lkr"])
            
            # DM test: candidate (yp1) vs seasonal_mean_4yr (yp2)
            # dm_stat < 0 => candidate has smaller error (better)
            # dm_stat > 0 => candidate has larger error (seasonal_mean_4yr is better)
            dm_stat, dm_pval = diebold_mariano_test(y_test_true, test_p, sm4yr_pred, h=h, week_indices=test_weeks)
            
            skill_vs_sm = (1.0 - mets["MASE"] / sm4yr_mase) * 100.0
            
            horizon_records.append({
                "horizon": h,
                "model": m_name,
                "target_mode": mode,
                "n_obs": mets["n_obs"],
                "MAE": round(mets["MAE"], 2),
                "sMAPE": round(mets["sMAPE"], 2),
                "MASE": round(mets["MASE"], 4),
                "SM4Yr_MASE": round(sm4yr_mase, 4),
                "Skill_vs_SM4Yr_pct": round(skill_vs_sm, 2),
                "DM_stat_vs_SM4Yr": dm_stat,
                "DM_pval_vs_SM4Yr": dm_pval,
                "is_selected": (m_name == selected_by_horizon[h][0] and mode == selected_by_horizon[h][1])
            })
            
        # Holm correction for this horizon
        m_tests = len([r for r in horizon_records if r["model"] != "seasonal_mean_4yr"])
        p_pairs = [(i, r["DM_pval_vs_SM4Yr"]) for i, r in enumerate(horizon_records) if r["model"] != "seasonal_mean_4yr" and pd.notna(r["DM_pval_vs_SM4Yr"])]
        p_pairs_sorted = sorted(p_pairs, key=lambda x: x[1])
        
        adj_p = {}
        running_max = 0.0
        for rank_idx, (orig_i, p_val) in enumerate(p_pairs_sorted):
            k = rank_idx + 1
            corr_p = min(1.0, (m_tests - k + 1) * p_val)
            running_max = max(running_max, corr_p)
            adj_p[orig_i] = round(min(1.0, running_max), 4)
            
        for i, r in enumerate(horizon_records):
            if r["model"] == "seasonal_mean_4yr":
                r["DM_pval_Holm_vs_SM4Yr"] = np.nan
                r["Better_Than_SM4Yr"] = "Benchmark"
            else:
                h_p = adj_p.get(i, np.nan)
                r["DM_pval_Holm_vs_SM4Yr"] = h_p
                if h_p < 0.05 and r["DM_stat_vs_SM4Yr"] < 0:
                    r["Better_Than_SM4Yr"] = "Significantly Better"
                elif h_p < 0.05 and r["DM_stat_vs_SM4Yr"] > 0:
                    r["Better_Than_SM4Yr"] = "Significantly Worse"
                else:
                    r["Better_Than_SM4Yr"] = "No Significant Diff"
                    
        all_dm_records.extend(horizon_records)
        
        # Check selected model
        sel_name, sel_mode = selected_by_horizon[h]
        sel_rec = [r for r in horizon_records if r["model"] == sel_name and r["target_mode"] == sel_mode]
        if sel_rec:
            selected_models_records.append(sel_rec[0])
            print(f"Selected Model ({sel_name} [{sel_mode}]): MASE = {sel_rec[0]['MASE']}, Skill vs SM4Yr = {sel_rec[0]['Skill_vs_SM4Yr_pct']}%, DM stat = {sel_rec[0]['DM_stat_vs_SM4Yr']}, p = {sel_rec[0]['DM_pval_vs_SM4Yr']}, Holm p = {sel_rec[0]['DM_pval_Holm_vs_SM4Yr']}, Status = {sel_rec[0]['Better_Than_SM4Yr']}")
            
    df_all_dm = pd.DataFrame(all_dm_records)
    out_all_csv = Path("results/tables/dm_tests_vs_seasonal_mean_4yr.csv")
    df_all_dm.to_csv(out_all_csv, index=False)
    print(f"\nSaved all DM tests vs seasonal_mean_4yr to {out_all_csv}")
    
    df_sel = pd.DataFrame(selected_models_records)
    out_sel_csv = Path("results/tables/selected_models_vs_seasonal_mean_4yr.csv")
    df_sel.to_csv(out_sel_csv, index=False)
    print(f"Saved selected models DM tests vs seasonal_mean_4yr to {out_sel_csv}")
    
    print("\nSummary of Selected Models vs seasonal_mean_4yr:")
    print(df_sel[["horizon", "model", "target_mode", "MASE", "SM4Yr_MASE", "Skill_vs_SM4Yr_pct", "DM_stat_vs_SM4Yr", "DM_pval_vs_SM4Yr", "DM_pval_Holm_vs_SM4Yr", "Better_Than_SM4Yr"]].to_string(index=False))

if __name__ == "__main__":
    run_dm_vs_seasonal_mean()
