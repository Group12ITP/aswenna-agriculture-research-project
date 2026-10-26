import pandas as pd
import numpy as np
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Lasso
import lightgbm as lgb

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.models.baselines import NaiveForecaster

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)

own_lags = [c for c in df_feat.columns if c.startswith("lag_")]
calendar_cols = [c for c in df_feat.columns if "sin" in c or "cos" in c or c.startswith("month_") or c.startswith("week_")]
all_feature_cols = [c for c in df_feat.columns if not (c.startswith("target_") or c in ["week_index", "year", "month", "week_of_month", "approx_date", "product_name", "category", "unit"])]

# Add categorical encodings
df_enc = df_feat.copy()
df_enc["veg_code"] = df_feat["product_name"].astype("category").cat.codes
df_enc["cat_code"] = df_feat["category"].astype("category").cat.codes
df_enc["unit_code"] = df_feat["unit"].astype("category").cat.codes
all_features_full = all_feature_cols + ["veg_code", "cat_code", "unit_code"]

feature_configs = [
    ("1. Own-Lags (raw_level)", own_lags, "raw_level"),
    ("1. Own-Lags (log_ratio)", own_lags, "log_ratio"),
    ("2. Own-Lags + Calendar (raw_level)", own_lags + calendar_cols, "raw_level"),
    ("3. Full Features (raw_level)", all_features_full, "raw_level"),
    ("3. Full Features (log_ratio)", all_features_full, "log_ratio"),
]

records = []

for h in [1, 4]:
    train_mask, val_mask, test_mask = get_split_masks(df_enc, cfg=cfg, horizon=h)
    target_col = f"target_h{h}"
    
    # We evaluate on validation split (N=1528) to match the pre-registered model selection
    y_eval = df_enc.loc[val_mask, target_col]
    y_orig = df_enc.loc[val_mask, "price_lkr"]
    y_hist = df_enc.loc[train_mask, "price_lkr"]
    
    # Naive baseline
    m_naive = evaluate_predictions(y_eval, y_orig, y_train_history=y_hist)
    print(f"\nHorizon h={h} Validation (N={len(y_eval)}): Naive MAE = {m_naive['MAE']:.2f}, MASE = {m_naive['MASE']:.4f}")
    
    for name, fcols, mode in feature_configs:
        X_tr = df_enc.loc[train_mask, fcols].ffill().bfill().fillna(0.0)
        X_vl = df_enc.loc[val_mask, fcols].ffill().bfill().fillna(0.0)
        
        if mode == "raw_level":
            y_tr = df_enc.loc[train_mask, target_col]
            valid_tr = pd.notna(y_tr)
            
            # Lasso
            lasso = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.1, random_state=42, max_iter=2000))])
            lasso.fit(X_tr[valid_tr], y_tr[valid_tr])
            pred_lasso = pd.Series(lasso.predict(X_vl), index=y_eval.index)
            
            # LightGBM
            lgbm = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
            lgbm.fit(X_tr[valid_tr], y_tr[valid_tr])
            pred_lgbm = pd.Series(lgbm.predict(X_vl), index=y_eval.index)
            
        else: # log_ratio
            y_tr_ratio = np.log(df_enc.loc[train_mask, target_col] / df_enc.loc[train_mask, "price_lkr"])
            valid_tr = pd.notna(y_tr_ratio) & np.isfinite(y_tr_ratio)
            
            # Lasso
            lasso = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.01, random_state=42, max_iter=2000))])
            lasso.fit(X_tr[valid_tr], y_tr_ratio[valid_tr])
            p_ratio_lasso = lasso.predict(X_vl)
            pred_lasso = pd.Series(y_orig.values * np.exp(p_ratio_lasso), index=y_eval.index)
            
            # LightGBM
            lgbm = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
            lgbm.fit(X_tr[valid_tr], y_tr_ratio[valid_tr])
            p_ratio_lgbm = lgbm.predict(X_vl)
            pred_lgbm = pd.Series(y_orig.values * np.exp(p_ratio_lgbm), index=y_eval.index)
            
        pred_lasso = np.maximum(0.0, pred_lasso)
        pred_lgbm = np.maximum(0.0, pred_lgbm)
        
        m_lasso = evaluate_predictions(y_eval, pred_lasso, y_train_history=y_hist)
        m_lgbm = evaluate_predictions(y_eval, pred_lgbm, y_train_history=y_hist)
        
        sk_lasso = compute_skill_vs_naive(m_lasso["MASE"], m_naive["MASE"])
        sk_lgbm = compute_skill_vs_naive(m_lgbm["MASE"], m_naive["MASE"])
        
        records.append({
            "horizon": h,
            "feature_set": name,
            "n_features": len(fcols),
            "eval_sample": f"Validation (N={len(y_eval)})",
            "naive_MAE": round(m_naive["MAE"], 2),
            "naive_MASE": round(m_naive["MASE"], 4),
            "lasso_MAE": round(m_lasso["MAE"], 2),
            "lasso_MASE": round(m_lasso["MASE"], 4),
            "lasso_skill": round(sk_lasso, 2),
            "lgbm_MAE": round(m_lgbm["MAE"], 2),
            "lgbm_MASE": round(m_lgbm["MASE"], 4),
            "lgbm_skill": round(sk_lgbm, 2)
        })

df_abl = pd.DataFrame(records)
print("\n=== RECOMPUTED ABLATION STUDY ===")
print(df_abl[["horizon", "feature_set", "n_features", "naive_MAE", "naive_MASE", "lasso_MAE", "lasso_MASE", "lasso_skill", "lgbm_MAE", "lgbm_MASE", "lgbm_skill"]].to_string(index=False))
