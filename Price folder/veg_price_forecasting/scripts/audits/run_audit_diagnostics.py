import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import lightgbm as lgb

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import evaluate_predictions, compute_skill_vs_naive

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)

target_cols = [c for c in df_feat.columns if c.startswith("target_")]
meta_cols = ["week_index", "year", "month", "week_of_month", "approx_date", "product_name", "category", "unit"]

own_lags = [c for c in df_feat.columns if c.startswith("lag_") or c.startswith("log_lag_")]
calendar_cols = ["sin_month", "cos_month", "sin_wom", "cos_wom", "sin_woy", "cos_woy"]

df_enc = df_feat.copy()
df_enc["veg_code"] = df_feat["product_name"].astype("category").cat.codes
df_enc["cat_code"] = df_feat["category"].astype("category").cat.codes
df_enc["unit_code"] = df_feat["unit"].astype("category").cat.codes

all_feature_cols = [c for c in df_enc.columns if c not in (target_cols + meta_cols)]

feature_sets = {
    "1. Own-Lags Only": own_lags,
    "2. Own-Lags + Calendar": own_lags + calendar_cols,
    "3. Full Features (Lags + Roll + Cross-Veg)": all_feature_cols
}

print("=== TEST B: FEATURE ABLATION (LEADERBOARD CONFIGURATION) ===")
# Evaluate Naive baseline on validation first
ablation_results = []
for h in [1, 4]:
    target_name = f"target_h{h}"
    y_train = df_enc.loc[train_mask, target_name]
    y_val = df_enc.loc[val_mask, target_name]
    valid_tr = pd.notna(y_train)
    valid_vl = pd.notna(y_val)
    
    y_origin_val = df_enc.loc[val_mask, "price_lkr"]
    y_train_history = df_enc.loc[train_mask, "price_lkr"]
    
    # Naive baseline
    naive_val_mets = evaluate_predictions(y_val, y_origin_val, y_train_history=y_train_history)
    mase_naive_val = naive_val_mets["MASE"]
    mae_naive_val = naive_val_mets["MAE"]
    print(f"\nHorizon h={h}: Naive Validation MAE = {mae_naive_val:.2f}, MASE = {mase_naive_val:.4f}")
    
    for fset_name, fcols in feature_sets.items():
        X_train = df_enc.loc[train_mask, fcols].ffill().bfill().fillna(0.0)
        X_val = df_enc.loc[val_mask, fcols].ffill().bfill().fillna(0.0)
        
        # Leaderboard Lasso: Pipeline with StandardScaler and alpha=0.1
        lasso = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.1, random_state=42, max_iter=2000))])
        lasso.fit(X_train[valid_tr], y_train[valid_tr])
        p_lasso_val = pd.Series(lasso.predict(X_val), index=y_val.index)
        mets_lasso = evaluate_predictions(y_val, p_lasso_val, y_train_history=y_train_history)
        skill_lasso = compute_skill_vs_naive(mets_lasso["MASE"], mase_naive_val)
        
        # Also run unscaled Lasso(alpha=0.5) to diagnose why old ablation had MAE 49.32
        lasso_unscaled = Lasso(alpha=0.5, random_state=42, max_iter=2000)
        lasso_unscaled.fit(X_train[valid_tr], y_train[valid_tr])
        p_lasso_unscaled = pd.Series(lasso_unscaled.predict(X_val), index=y_val.index)
        mets_unscaled = evaluate_predictions(y_val, p_lasso_unscaled, y_train_history=y_train_history)
        
        # LightGBM
        lgbm = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
        lgbm.fit(X_train[valid_tr], y_train[valid_tr])
        p_lgbm_val = pd.Series(lgbm.predict(X_val), index=y_val.index)
        mets_lgbm = evaluate_predictions(y_val, p_lgbm_val, y_train_history=y_train_history)
        skill_lgbm = compute_skill_vs_naive(mets_lgbm["MASE"], mase_naive_val)
        
        ablation_results.append({
            "horizon": h,
            "feature_set": fset_name,
            "n_features": len(fcols),
            "lasso_MAE": mets_lasso["MAE"],
            "lasso_MASE": mets_lasso["MASE"],
            "lasso_skill": skill_lasso,
            "unscaled_MAE": mets_unscaled["MAE"],
            "unscaled_MASE": mets_unscaled["MASE"],
            "lgbm_MAE": mets_lgbm["MAE"],
            "lgbm_MASE": mets_lgbm["MASE"],
            "lgbm_skill": skill_lgbm
        })

df_ab = pd.DataFrame(ablation_results)
print("\nAblation Results Summary:")
print(df_ab[["horizon", "feature_set", "n_features", "lasso_MAE", "lasso_MASE", "lasso_skill", "unscaled_MAE", "lgbm_MAE", "lgbm_skill"]])

print("\n=== TEST C: PLACEBO TEST (LEADERBOARD CONFIGURATION, ALL 4 HORIZONS) ===")
placebo_results = []
for h in [1, 4, 8, 12]:
    target_name = f"target_h{h}"
    y_tr_real = df_enc.loc[train_mask, target_name]
    y_tr_placebo = df_enc.loc[train_mask, target_name].shift(4)
    y_test_real = df_enc.loc[test_mask, target_name]
    
    y_origin_test = df_enc.loc[test_mask, "price_lkr"]
    y_train_history = df_enc.loc[train_mask, "price_lkr"]
    
    # Naive baseline on test
    naive_test_mets = evaluate_predictions(y_test_real, y_origin_test, y_train_history=y_train_history)
    mase_naive_test = naive_test_mets["MASE"]
    
    X_tr_full = df_enc.loc[train_mask, all_feature_cols].ffill().bfill().fillna(0.0)
    X_te_full = df_enc.loc[test_mask, all_feature_cols].ffill().bfill().fillna(0.0)
    
    valid_tr_real = pd.notna(y_tr_real)
    valid_tr_placebo = pd.notna(y_tr_placebo)
    
    # Leaderboard Lasso on real target
    lasso_real = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.1, random_state=42, max_iter=2000))])
    lasso_real.fit(X_tr_full[valid_tr_real], y_tr_real[valid_tr_real])
    p_real = pd.Series(lasso_real.predict(X_te_full), index=y_test_real.index)
    mets_real = evaluate_predictions(y_test_real, p_real, y_train_history=y_train_history)
    skill_real = compute_skill_vs_naive(mets_real["MASE"], mase_naive_test)
    
    # Leaderboard Lasso on placebo target
    lasso_placebo = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.1, random_state=42, max_iter=2000))])
    lasso_placebo.fit(X_tr_full[valid_tr_placebo], y_tr_placebo[valid_tr_placebo])
    p_placebo = pd.Series(lasso_placebo.predict(X_te_full), index=y_test_real.index)
    mets_placebo = evaluate_predictions(y_test_real, p_placebo, y_train_history=y_train_history)
    skill_placebo = compute_skill_vs_naive(mets_placebo["MASE"], mase_naive_test)
    
    placebo_results.append({
        "horizon": h,
        "naive_MASE": mase_naive_test,
        "real_MASE": mets_real["MASE"],
        "real_R2": mets_real["R2"],
        "real_skill": skill_real,
        "placebo_MASE": mets_placebo["MASE"],
        "placebo_R2": mets_placebo["R2"],
        "placebo_skill": skill_placebo
    })

df_pl = pd.DataFrame(placebo_results)
df_ab.to_csv("results/tables/ablation_study.csv", index=False)
df_pl.to_csv("results/tables/placebo_study.csv", index=False)
print("\nPlacebo Results Summary across Horizons:")
print(df_pl.to_string())
print("\nAblation Results Full Table:")
print(df_ab.to_string())
