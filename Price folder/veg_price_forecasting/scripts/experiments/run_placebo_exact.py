import sys
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.linear_model import Lasso
import warnings
warnings.filterwarnings('ignore')

from src.utils import load_config, set_seeds
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.train import prepare_feature_matrices

def run_placebo():
    cfg = load_config()
    set_seeds(42)
    
    print("Loading data for exact Placebo Study recomputation...")
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    
    # Leaderboard tuned alphas for raw_level Lasso
    tuned_alphas = {
        1: 1.5359,
        4: 3.3947,
        8: 4.4937,
        12: 0.6522
    }
    
    horizons = [1, 4, 8, 12]
    placebo_records = []
    
    for h in horizons:
        train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
        target_col = f"target_h{h}"
        alpha = tuned_alphas[h]
        
        # Build feature matrix
        X_full, y_raw_full, feature_names = prepare_feature_matrices(df_feat, target_col=target_col)
        
        # Shift target by +4 weeks within each vegetable series for placebo target
        # Shifting the target by +4 weeks means y_placebo[t] = y_true[t+4]
        y_placebo_full = df_feat.groupby("product_name")[target_col].shift(-4)
        
        y_test_true = df_feat.loc[test_mask, target_col]
        y_orig_test = df_feat.loc[test_mask, "price_lkr"]
        y_train_hist = df_feat.loc[train_mask, "price_lkr"]
        
        # Naive baseline on test
        m_naive = evaluate_predictions(y_test_true, y_orig_test, y_train_history=y_train_hist)
        naive_mase = m_naive["MASE"]
        
        X_tr = X_full[train_mask]
        X_te = X_full[test_mask]
        
        y_tr_real = y_raw_full[train_mask]
        y_tr_placebo = y_placebo_full[train_mask]
        
        clean_real = pd.notna(y_tr_real) & np.isfinite(y_tr_real)
        clean_plac = pd.notna(y_tr_placebo) & np.isfinite(y_tr_placebo)
        
        # 1. Real Lasso
        lasso_real = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=alpha, random_state=42, max_iter=2000))])
        lasso_real.fit(X_tr[clean_real], y_tr_real[clean_real])
        p_real = pd.Series(lasso_real.predict(X_te), index=y_test_true.index)
        p_real = np.maximum(0.0, p_real)
        m_real = evaluate_predictions(y_test_true, p_real, y_train_history=y_train_hist)
        sk_real = compute_skill_vs_naive(m_real["MASE"], naive_mase)
        
        # 2. Placebo Lasso
        lasso_plac = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=alpha, random_state=42, max_iter=2000))])
        lasso_plac.fit(X_tr[clean_plac], y_tr_placebo[clean_plac])
        p_plac = pd.Series(lasso_plac.predict(X_te), index=y_test_true.index)
        p_plac = np.maximum(0.0, p_plac)
        m_plac = evaluate_predictions(y_test_true, p_plac, y_train_history=y_train_hist)
        sk_plac = compute_skill_vs_naive(m_plac["MASE"], naive_mase)
        
        skill_ratio = (sk_plac / sk_real * 100.0) if sk_real > 0 else 0.0
        
        print(f"\nHorizon h={h} (alpha={alpha:.4f}, N_test={len(y_test_true)}):")
        print(f"  Naive Test MASE:    {naive_mase:.4f}")
        print(f"  Real Lasso MASE:    {m_real['MASE']:.4f} (R2={m_real['R2']:.4f}, Skill={sk_real:+.2f}%)")
        print(f"  Placebo Lasso MASE: {m_plac['MASE']:.4f} (R2={m_plac['R2']:.4f}, Skill={sk_plac:+.2f}%)")
        print(f"  Placebo / Real Skill Ratio: {skill_ratio:.1f}%")
        
        placebo_records.append({
            "horizon": h,
            "alpha": round(alpha, 4),
            "naive_MASE": round(naive_mase, 4),
            "real_MASE": round(m_real["MASE"], 4),
            "real_R2": round(m_real["R2"], 4),
            "real_skill_vs_naive": round(sk_real, 2),
            "placebo_MASE": round(m_plac["MASE"], 4),
            "placebo_R2": round(m_plac["R2"], 4),
            "placebo_skill_vs_naive": round(sk_plac, 2),
            "placebo_skill_retention_pct": round(skill_ratio, 1)
        })
        
    df_pl = pd.DataFrame(placebo_records)
    out_csv = Path("results/tables/placebo_study.csv")
    df_pl.to_csv(out_csv, index=False)
    print(f"\nSaved exact placebo study to {out_csv}")
    return df_pl

if __name__ == "__main__":
    run_placebo()
