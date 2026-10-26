import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Lasso
import lightgbm as lgb
import warnings
warnings.filterwarnings('ignore')

from src.utils import load_config, set_seeds
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.train import prepare_feature_matrices, tune_classical_model
from src.models.classical import get_classical_model

def run_ablation():
    cfg = load_config()
    set_seeds(cfg.get("random_seed", 42))
    
    print("Loading data for ablation study...")
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    
    # Define exact feature groups
    lags = [1, 2, 3, 4, 8, 12, 26, 48]
    own_lags = [f"lag_{k}" for k in lags]
    
    # Clean cyclical calendar features (strictly seasonal, NO week_index or linear trends)
    cyclical_calendar = ["sin_month", "cos_month", "sin_wom", "cos_wom", "sin_woy", "cos_woy"]
    
    # Flawed calendar including week_index (for explicit diagnostic reproduction)
    flawed_calendar = cyclical_calendar + ["week_index"]
    
    horizons = [1, 4]
    ablation_records = []
    
    for h in horizons:
        train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
        target_col = f"target_h{h}"
        
        # EXACT LEADERBOARD VALIDATION SAMPLE: N=1528 (dropping 8 unobserved target rows)
        y_val_all = df_feat.loc[val_mask, target_col]
        valid_val_idx = y_val_all.dropna().index
        
        y_val_true = df_feat.loc[valid_val_idx, target_col]
        y_orig_val = df_feat.loc[valid_val_idx, "price_lkr"]
        y_train_hist = df_feat.loc[train_mask, "price_lkr"]
        
        # Exact leaderboard feature matrix
        X_full, y_raw_full, feature_names = prepare_feature_matrices(df_feat, target_col=target_col)
        y_orig = df_feat["price_lkr"].clip(lower=1.0)
        y_ratio_full = np.log(np.clip(y_raw_full / y_orig, 1e-4, None))
        
        m_naive = evaluate_predictions(y_val_true, y_orig_val, y_train_history=y_train_hist)
        print(f"\n{'='*70}\nHORIZON h={h} LEADERBOARD VALIDATION (N={len(y_val_true)}):\n{'='*70}")
        print(f"  Naive Baseline: MAE = {m_naive['MAE']:.2f} Rs, MASE = {m_naive['MASE']:.4f}")
        
        # Test configurations
        configurations = [
            ("1. Own-Lags (raw_level)", own_lags, "raw_level"),
            ("1. Own-Lags (log_ratio)", own_lags, "log_ratio"),
            ("2. Own-Lags + Cyclical Calendar (raw_level) [Clean]", own_lags + cyclical_calendar, "raw_level"),
            ("2. Own-Lags + Calendar with week_index (raw_level) [Flawed Trend]", own_lags + flawed_calendar, "raw_level"),
            ("2. Own-Lags + Cyclical Calendar (log_ratio) [Clean]", own_lags + cyclical_calendar, "log_ratio"),
            ("3. Full Features (raw_level) [Leaderboard]", list(X_full.columns), "raw_level"),
            ("3. Full Features (log_ratio) [Leaderboard]", list(X_full.columns), "log_ratio"),
        ]
        
        for cfg_name, fcols, mode in configurations:
            # Build X and y for this configuration
            if cfg_name.startswith("3. Full"):
                X_mat = X_full[fcols].copy()
            else:
                X_mat = df_feat[fcols].ffill().bfill().fillna(0.0).copy()
                
            y_target = y_raw_full if mode == "raw_level" else y_ratio_full
            
            clean_tr = train_mask & pd.notna(y_target) & np.isfinite(y_target)
            X_tr, y_tr = X_mat.loc[clean_tr], y_target.loc[clean_tr]
            X_vl = X_mat.loc[valid_val_idx]
            
            # --- LASSO ---
            # Default / tuned alpha: alpha=6.20 for raw_level (or CV-tuned), alpha=0.01 for log_ratio
            if cfg_name.startswith("3. Full"):
                alpha = 6.20 if mode == "raw_level" else 0.01
            elif "Flawed" in cfg_name:
                alpha = 0.1
            else:
                alpha = 1.0 if mode == "raw_level" else 0.01
                
            lasso = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=alpha, random_state=42, max_iter=2000))])
            lasso.fit(X_tr, y_tr)
            p_vl_lasso_raw = lasso.predict(X_vl)
            
            # --- LIGHTGBM ---
            lgbm = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
            lgbm.fit(X_tr, y_tr)
            p_vl_lgb_raw = lgbm.predict(X_vl)
            
            if mode == "log_ratio":
                pred_lasso = y_orig_val * np.exp(p_vl_lasso_raw)
                pred_lgbm = y_orig_val * np.exp(p_vl_lgb_raw)
            else:
                pred_lasso = p_vl_lasso_raw
                pred_lgbm = p_vl_lgb_raw
                
            pred_lasso = np.maximum(0.0, np.nan_to_num(pred_lasso, nan=0.0))
            pred_lgbm = np.maximum(0.0, np.nan_to_num(pred_lgbm, nan=0.0))
            
            m_l = evaluate_predictions(y_val_true, pred_lasso, y_train_history=y_train_hist)
            m_g = evaluate_predictions(y_val_true, pred_lgbm, y_train_history=y_train_hist)
            
            sk_l = compute_skill_vs_naive(m_l["MASE"], m_naive["MASE"])
            sk_g = compute_skill_vs_naive(m_g["MASE"], m_naive["MASE"])
            
            print(f"  {cfg_name:<55} | Lasso MASE: {m_l['MASE']:.4f} ({sk_l:+.2f}%) | LGB MASE: {m_g['MASE']:.4f} ({sk_g:+.2f}%) | alpha: {alpha}")
            
            ablation_records.append({
                "horizon": h,
                "feature_configuration": cfg_name,
                "features": len(fcols),
                "evaluation_sample": f"Validation (N={len(y_val_true)})",
                "naive_mae": round(m_naive["MAE"], 2),
                "naive_mase": round(m_naive["MASE"], 4),
                "lasso_mae": round(m_l["MAE"], 2),
                "lasso_mase": round(m_l["MASE"], 4),
                "lasso_skill_vs_naive": round(sk_l, 2),
                "lightgbm_mae": round(m_g["MAE"], 2),
                "lightgbm_mase": round(m_g["MASE"], 4),
                "lightgbm_skill_vs_naive": round(sk_g, 2),
                "lasso_alpha": alpha
            })
            
    df_ab = pd.DataFrame(ablation_records)
    out_path = Path("results/tables/ablation_study.csv")
    df_ab.to_csv(out_path, index=False)
    print(f"\nSaved exact leaderboard ablation study to {out_path}")
    return df_ab

if __name__ == "__main__":
    run_ablation()
