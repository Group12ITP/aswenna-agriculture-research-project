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
from src.models.baselines import NaiveForecaster
from src.models.classical import get_classical_model
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.train import prepare_feature_matrices

def run_placebo_leaderboard():
    cfg = load_config()
    set_seeds(42)
    
    print("Loading data for exact Leaderboard Placebo Study...")
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    
    tuned_alphas = {1: 1.5359, 4: 3.3947, 8: 4.4937, 12: 0.6522}
    horizons = [1, 4, 8, 12]
    placebo_records = []
    
    for h in horizons:
        train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
        target_col = f"target_h{h}"
        alpha = tuned_alphas[h]
        
        target_week = df_feat["week_index"] + h
        max_allowed_refit = 417 - h
        refit_mask = train_mask | (val_mask & (target_week <= max_allowed_refit))
        
        # Build feature matrix
        X, y_raw, feature_names = prepare_feature_matrices(df_feat, target_col=target_col)
        
        # Naive predictions on test
        test_preds_list = []
        for veg in df_feat["product_name"].unique():
            v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
            train_prices = v_df.loc[train_mask.loc[v_df.index], "price_lkr"].values
            model = NaiveForecaster()
            model.fit(train_prices)
            for idx in v_df.index[test_mask.loc[v_df.index]]:
                curr_w = v_df.loc[idx, "week_index"]
                hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
                test_preds_list.append((idx, model.predict(horizon=h, y_history=hist)))
        naive_test_p = pd.Series({idx: p for idx, p in test_preds_list}, name="pred_naive")
        
        y_test_true = df_feat.loc[test_mask, target_col]
        y_origin_test = df_feat.loc[test_mask, "price_lkr"]
        y_refit_hist = df_feat.loc[refit_mask, "price_lkr"]
        
        m_naive = evaluate_predictions(y_test_true, naive_test_p, y_train_history=y_refit_hist, y_prev=y_origin_test)
        naive_mase = m_naive["MASE"]
        
        # Train / Refit data
        X_rf = X[refit_mask]
        y_rf_real = y_raw[refit_mask]
        X_test = X[test_mask]
        
        # Placebo target: shift target by +4 weeks within product_name
        df_feat_rf = df_feat.loc[refit_mask].copy()
        y_rf_placebo = df_feat.groupby("product_name")[target_col].shift(-4).loc[refit_mask]
        
        clean_rf_real = pd.notna(y_rf_real)
        clean_rf_plac = pd.notna(y_rf_placebo)
        
        # 1. Real Leaderboard Lasso
        m_real = get_classical_model("lasso", params={"alpha": alpha})
        m_real.fit(X_rf[clean_rf_real], y_rf_real[clean_rf_real])
        p_real = pd.Series(m_real.predict(X_test), index=y_test_true.index)
        p_real = np.nan_to_num(np.maximum(0.0, p_real), nan=0.0)
        mets_real = evaluate_predictions(y_test_true, p_real, y_train_history=y_refit_hist, y_prev=y_origin_test)
        sk_real = compute_skill_vs_naive(mets_real["MASE"], naive_mase)
        
        # 2. Placebo Lasso
        m_plac = get_classical_model("lasso", params={"alpha": alpha})
        m_plac.fit(X_rf[clean_rf_plac], y_rf_placebo[clean_rf_plac])
        p_plac = pd.Series(m_plac.predict(X_test), index=y_test_true.index)
        p_plac = np.nan_to_num(np.maximum(0.0, p_plac), nan=0.0)
        mets_plac = evaluate_predictions(y_test_true, p_plac, y_train_history=y_refit_hist, y_prev=y_origin_test)
        sk_plac = compute_skill_vs_naive(mets_plac["MASE"], naive_mase)
        
        retention = (sk_plac / sk_real * 100.0) if sk_real > 0 else 0.0
        
        print(f"\nHorizon h={h} (alpha={alpha:.4f}, N_test={len(y_test_true)}):")
        print(f"  Naive Test MASE:    {naive_mase:.4f}")
        print(f"  Real Lasso MASE:    {mets_real['MASE']:.4f} (R2={mets_real['R2']:.4f}, Skill={sk_real:+.2f}%)")
        print(f"  Placebo Lasso MASE: {mets_plac['MASE']:.4f} (R2={mets_plac['R2']:.4f}, Skill={sk_plac:+.2f}%)")
        print(f"  Placebo / Real Skill Ratio: {retention:.1f}%")
        
        placebo_records.append({
            "horizon": h,
            "alpha": round(alpha, 4),
            "naive_MASE": round(naive_mase, 4),
            "real_MASE": round(mets_real["MASE"], 4),
            "real_R2": round(mets_real["R2"], 4),
            "real_skill_vs_naive": round(sk_real, 2),
            "placebo_MASE": round(mets_plac["MASE"], 4),
            "placebo_R2": round(mets_plac["R2"], 4),
            "placebo_skill_vs_naive": round(sk_plac, 2),
            "placebo_skill_retention_pct": round(retention, 1)
        })
        
    df_pl = pd.DataFrame(placebo_records)
    out_csv = Path("results/tables/placebo_study.csv")
    df_pl.to_csv(out_csv, index=False)
    print(f"\nSaved exact leaderboard placebo study to {out_csv}")
    return df_pl

if __name__ == "__main__":
    run_placebo_leaderboard()
