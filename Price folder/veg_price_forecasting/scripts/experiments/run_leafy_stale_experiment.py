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
from src.train import prepare_feature_matrices

def run_leafy_stale_experiment():
    cfg = load_config()
    set_seeds(42)
    
    print("Loading data for Leafy Green Stale Training Experiment...")
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    
    h = 4
    target_col = f"target_h{h}"
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
    
    # Leafy greens filter
    leafy_mask = df_feat["category"] == "leafy vegetables"
    
    # Stale period filter in training data: 2020-09-01 to 2023-08-31
    stale_period_mask = (df_feat["approx_date"] >= "2020-09-01") & (df_feat["approx_date"] <= "2023-08-31")
    
    train_full = train_mask & leafy_mask
    train_no_stale = train_mask & leafy_mask & (~stale_period_mask)
    test_leafy = test_mask & leafy_mask
    
    print(f"Leafy Training Obs: Full = {train_full.sum()} rows, Without Stale Period = {train_no_stale.sum()} rows (Purged {train_full.sum() - train_no_stale.sum()} stale rows)")
    print(f"Leafy Test Obs:     {test_leafy.sum()} rows")
    
    y_test_true = df_feat.loc[test_leafy, target_col]
    y_orig_test = df_feat.loc[test_leafy, "price_lkr"]
    y_hist_full = df_feat.loc[train_full, "price_lkr"]
    
    # Naive baseline on test
    m_naive = evaluate_predictions(y_test_true, y_orig_test, y_train_history=y_hist_full)
    print(f"\nLeafy Test Naive Baseline (h=4, N={len(y_test_true)}):")
    print(f"  MAE = {m_naive['MAE']:.2f} Rs, sMAPE = {m_naive['sMAPE']:.2f}%, MASE = {m_naive['MASE']:.4f}, R2 = {m_naive['R2']:.4f}")
    
    # Feature matrix for leafy vegetables
    X_full, y_raw_full, feature_names = prepare_feature_matrices(df_feat, target_col=target_col)
    y_orig = df_feat["price_lkr"].clip(lower=1.0)
    y_ratio_full = np.log(np.clip(y_raw_full / y_orig, 1e-4, None))
    
    models_to_test = [
        ("Lasso (raw_level)", "raw_level", "lasso"),
        ("Lasso (log_ratio)", "log_ratio", "lasso"),
        ("LightGBM (raw_level)", "raw_level", "lightgbm"),
        ("LightGBM (log_ratio)", "log_ratio", "lightgbm"),
    ]
    
    experiment_records = []
    
    # Add naive baseline record
    experiment_records.append({
        "status": "EXPLORATORY",
        "split": "test",
        "model": "Naive Persistence",
        "target_mode": "raw_level",
        "training_regime": "Benchmark (No Training)",
        "train_n": 0,
        "test_n": len(y_test_true),
        "test_MAE": round(m_naive["MAE"], 2),
        "test_sMAPE": round(m_naive["sMAPE"], 2),
        "test_MASE": round(m_naive["MASE"], 4),
        "test_R2": round(m_naive["R2"], 4),
        "skill_vs_naive_pct": 0.0
    })
    
    for m_label, mode, m_type in models_to_test:
        y_target = y_raw_full if mode == "raw_level" else y_ratio_full
        
        for regime, tr_m in [("With Stale Period (Full History)", train_full), ("Without Stale Period (Filtered 2020-2023)", train_no_stale)]:
            clean_tr = tr_m & pd.notna(y_target) & np.isfinite(y_target)
            
            X_tr, y_tr = X_full[clean_tr], y_target[clean_tr]
            X_te = X_full[test_leafy]
            
            if m_type == "lasso":
                alpha = 3.3947 if mode == "raw_level" else 0.01
                model = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=alpha, random_state=42, max_iter=2000))])
                model.fit(X_tr, y_tr)
                p_raw = model.predict(X_te)
            elif m_type == "lightgbm":
                model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
                model.fit(X_tr, y_tr)
                p_raw = model.predict(X_te)
                
            if mode == "log_ratio":
                pred = y_orig_test * np.exp(p_raw)
            else:
                pred = p_raw
                
            pred = np.maximum(0.0, np.nan_to_num(pred, nan=0.0))
            
            mets = evaluate_predictions(y_test_true, pred, y_train_history=df_feat.loc[tr_m, "price_lkr"])
            sk = compute_skill_vs_naive(mets["MASE"], m_naive["MASE"])
            
            print(f"  {m_label:<25} | {regime:<42} | Test MAE: {mets['MAE']:.2f} Rs | sMAPE: {mets['sMAPE']:.2f}% | MASE: {mets['MASE']:.4f} | R2: {mets['R2']:.4f} | Skill: {sk:+.2f}%")
            
            experiment_records.append({
                "status": "EXPLORATORY",
                "split": "test",
                "model": m_label,
                "target_mode": mode,
                "training_regime": regime,
                "train_n": clean_tr.sum(),
                "test_n": len(y_test_true),
                "test_MAE": round(mets["MAE"], 2),
                "test_sMAPE": round(mets["sMAPE"], 2),
                "test_MASE": round(mets["MASE"], 4),
                "test_R2": round(mets["R2"], 4),
                "skill_vs_naive_pct": round(sk, 2)
            })
            
    df_exp = pd.DataFrame(experiment_records)
    out_csv = Path("results/tables/leafy_stale_training_experiment.csv")
    df_exp.to_csv(out_csv, index=False)
    print(f"\nSaved Leafy Green Stale Training Experiment to {out_csv}")
    return df_exp

if __name__ == "__main__":
    run_leafy_stale_experiment()
