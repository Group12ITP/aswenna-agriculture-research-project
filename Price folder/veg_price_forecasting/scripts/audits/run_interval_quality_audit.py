import sys
from pathlib import Path
proj_root = Path(__file__).resolve().parent.parent
if str(proj_root) not in sys.path:
    sys.path.insert(0, str(proj_root))

import logging
import numpy as np
import pandas as pd

from src.utils import load_config, set_seeds, get_logger
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.train import prepare_feature_matrices
from src.intervals import ScaleAwareConformalPredictor, ConformalizedQuantileRegression, evaluate_interval_quality

logger = get_logger("interval_audit")

def run_interval_audit():
    cfg = load_config()
    set_seeds(42)
    
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)
    
    # Split val into tuning (first 24 weeks) and calibration (last 24 weeks)
    unique_val_weeks = np.sort(df_feat.loc[val_mask, "week_index"].unique())
    val_cal_weeks = unique_val_weeks[len(unique_val_weeks)//2:]
    val_cal_mask = val_mask & df_feat["week_index"].isin(val_cal_weeks)
    val_tune_mask = val_mask & (~df_feat["week_index"].isin(val_cal_weeks))
    
    horizons = [1, 4, 8, 12]
    
    # 1. Evaluate Conformalized Quantile Regression (CQR) vs Scale-Aware Conformal Prediction
    cqr_comparison_records = []
    
    for h in horizons:
        target_col = f"target_h{h}"
        X, y, feature_cols = prepare_feature_matrices(df_feat, target_col=target_col)
        
        X_tr = X[train_mask]
        y_tr = y[train_mask]
        X_cal = X[val_cal_mask]
        y_cal = y[val_cal_mask]
        X_te = X[test_mask]
        y_te = y[test_mask]
        
        # Fit CQR
        cqr = ConformalizedQuantileRegression(alpha=0.20, n_estimators=120, random_state=42)
        cqr.fit(X_tr, y_tr)
        cqr.calibrate(X_cal, y_cal)
        lower_cqr, upper_cqr = cqr.predict_intervals(X_te)
        
        cov_cqr = evaluate_interval_quality(y_te, lower_cqr, upper_cqr, metadata_df=df_feat.loc[test_mask])
        
        # Load winning / benchmark model predictions on test to compare Scale-Aware Conformal
        # Use LightGBM run
        for p in sorted(Path("experiments/runs").glob(f"*_lightgbm_h{h}")):
            if (p / "predictions_test.csv").exists():
                df_run = pd.read_csv(p / "predictions_test.csv")
                if len(df_run) >= 1500:
                    cov_scale_aware = evaluate_interval_quality(
                        df_run["y_true"], df_run["lower_80"], df_run["upper_80"],
                        y_pred=df_run["y_pred"], metadata_df=df_feat.loc[test_mask]
                    )
                    break
                    
        cqr_comparison_records.append({
            "horizon": h,
            "method": "Conformalized Quantile Reg (CQR)",
            "coverage_80": cov_cqr["coverage_pct"],
            "width_80_lkr": cov_cqr["mean_width_lkr"],
            "width_80_pct": cov_cqr["mean_width_pct"],
            "calibration_status": "Calibrated" if 77 <= cov_cqr["coverage_pct"] <= 88 else ("Under-covered" if cov_cqr["coverage_pct"] < 77 else "Over-wide")
        })
        cqr_comparison_records.append({
            "horizon": h,
            "method": "Scale-Aware Conformal (LightGBM)",
            "coverage_80": cov_scale_aware["coverage_pct"],
            "width_80_lkr": cov_scale_aware["mean_width_lkr"],
            "width_80_pct": cov_scale_aware["mean_width_pct"],
            "calibration_status": "Calibrated" if 77 <= cov_scale_aware["coverage_pct"] <= 88 else ("Under-covered" if cov_scale_aware["coverage_pct"] < 77 else "Over-wide")
        })
        
    df_cqr_comp = pd.DataFrame(cqr_comparison_records)
    tbl_path = Path("results/tables")
    tbl_path.mkdir(parents=True, exist_ok=True)
    df_cqr_comp.to_csv(tbl_path / "cqr_vs_scale_aware_intervals.csv", index=False)
    print("=== CQR vs SCALE-AWARE CONFORMAL INTERVALS ===")
    print(df_cqr_comp.to_string())
    
    # 2. Comprehensive Model Interval Calibration Audit with Miscalibration Flags
    lead = pd.read_csv("experiments/leaderboard.csv")
    test_rows = lead[lead["split"] == "test"].copy()
    
    interval_audit_records = []
    for _, r in test_rows.iterrows():
        m = r["model"]
        h = int(r["horizon"])
        cov80 = r.get("Coverage_80")
        w80_lkr = r.get("Width_80_LKR")
        w80_pct = r.get("Width_80_Pct")
        
        if pd.notna(cov80):
            if cov80 < 77.0:
                status = "Miscalibrated (Under-coverage < 77%)"
            elif cov80 > 88.0:
                status = "Miscalibrated (Over-wide > 88%)"
            else:
                status = "Well-Calibrated (77-88%)"
                
            interval_audit_records.append({
                "model": m,
                "horizon": h,
                "coverage_80": round(cov80, 2),
                "width_80_lkr": round(w80_lkr, 2) if pd.notna(w80_lkr) else np.nan,
                "width_80_pct": round(w80_pct, 2) if pd.notna(w80_pct) else np.nan,
                "calibration_flag": status
            })
            
    df_interval_audit = pd.DataFrame(interval_audit_records)
    df_interval_audit.to_csv(tbl_path / "interval_calibration_audit.csv", index=False)
    print("\nSaved interval calibration audit to results/tables/interval_calibration_audit.csv")
    
    # Check Prophet specifically at all horizons
    print("\nProphet Interval Calibration Summary:")
    print(df_interval_audit[df_interval_audit["model"] == "prophet"])
    
    # 3. Per-Category Interval Quality at Primary Horizon h=4
    # Compute per-category coverage for winning model (sarimax or best per category)
    # Check run path for sarimax_h4 and lightgbm_h4
    cat_interval_records = []
    for m in ["sarimax", "lightgbm", "prophet", "naive"]:
        for p in sorted(Path("experiments/runs").glob(f"*_{m}_h4")):
            pred_f = p / "predictions_test.csv"
            if pred_f.exists():
                df_p = pd.read_csv(pred_f)
                if len(df_p) >= 1500:
                    cov_res = evaluate_interval_quality(
                        df_p["y_true"], df_p["lower_80"], df_p["upper_80"],
                        y_pred=df_p["y_pred"], metadata_df=df_feat.loc[test_mask]
                    )
                    by_c = cov_res.get("by_category", {})
                    for cat, c_dict in by_c.items():
                        c_cov = c_dict["coverage_pct"]
                        c_flag = "Well-Calibrated" if 77 <= c_cov <= 88 else ("Under-covered" if c_cov < 77 else "Over-wide")
                        cat_interval_records.append({
                            "model": m,
                            "horizon": 4,
                            "category": cat,
                            "coverage_80": c_cov,
                            "width_80_pct": c_dict["width_pct"],
                            "calibration_flag": c_flag
                        })
                    break
                    
    df_cat_intervals = pd.DataFrame(cat_interval_records)
    df_cat_intervals.to_csv(tbl_path / "interval_by_category_h4.csv", index=False)
    print("\nPer-Category Interval Quality at h=4:")
    print(df_cat_intervals.to_string())
    
    # 4. Final Deliverable: For each vegetable and horizon: lower_80 / expected / upper_80
    final_rows = []
    # Use selected winning model for each horizon
    # At h=4, winning model is sarimax
    for h in horizons:
        # Load run for selected model
        selected_m = "sarimax" # Pre-registered selection winner
        for p in sorted(Path("experiments/runs").glob(f"*_{selected_m}_h{h}")):
            pred_f = p / "predictions_test.csv"
            if pred_f.exists():
                df_p = pd.read_csv(pred_f)
                if len(df_p) >= 1500:
                    for _, row in df_p.iterrows():
                        final_rows.append({
                            "product_name": row["product_name"],
                            "approx_date": row["approx_date"],
                            "horizon": h,
                            "model": selected_m,
                            "expected": round(float(row["y_pred"]), 2),
                            "lower_80": round(float(row["lower_80"]), 2),
                            "upper_80": round(float(row["upper_80"]), 2),
                            "lower_95": round(float(row["lower_95"]), 2),
                            "upper_95": round(float(row["upper_95"]), 2),
                            "y_true": round(float(row["y_true"]), 2) if pd.notna(row["y_true"]) else np.nan
                        })
                    break
                    
    df_final = pd.DataFrame(final_rows)
    final_out = Path("results/final_forecasts_with_intervals.csv")
    df_final.to_csv(final_out, index=False)
    print(f"\nSuccessfully generated final deliverable: {final_out} with {len(df_final)} forecast records.")
    print("Sample forecasts:")
    print(df_final.head(10).to_string())

if __name__ == "__main__":
    run_interval_audit()
