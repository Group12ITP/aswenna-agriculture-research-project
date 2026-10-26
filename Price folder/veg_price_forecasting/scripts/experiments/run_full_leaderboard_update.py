import sys
from pathlib import Path
import numpy as np
import pandas as pd

from src.utils import load_config, set_seeds, get_logger
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import (
    evaluate_predictions, compute_skill_vs_naive,
    block_bootstrap_mase, diebold_mariano_test,
    holm_bonferroni_correction
)

logger = get_logger("full_leaderboard_update")

def update_all():
    cfg = load_config()
    set_seeds(42)
    
    print("Loading data and building features...")
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)
    
    val_weeks = df_feat.loc[val_mask, "week_index"]
    test_weeks = df_feat.loc[test_mask, "week_index"]
    
    y_orig_val = df_feat.loc[val_mask, "price_lkr"]
    y_orig_test = df_feat.loc[test_mask, "price_lkr"]
    
    y_tr_hist = df_feat.loc[train_mask, "price_lkr"]
    y_tr_val_hist = df_feat.loc[train_mask | val_mask, "price_lkr"]
    
    horizons = [1, 4, 8, 12]
    runs_dir = Path("experiments/runs")
    
    all_models = [
        "naive", "seasonal_naive_48", "moving_average_4", "moving_average_12", "drift",
        "holt_winters_ets", "auto_arima", "sarimax", "prophet",
        "linear_regression", "ridge", "lasso", "elastic_net",
        "random_forest", "extra_trees", "gradient_boosting",
        "xgboost", "lightgbm", "catboost", "svr",
        "mlp", "lstm", "gru", "tcn_1d", "nbeats", "transformer", "nhits", "tft_lite",
        "simple_average_top3", "stacking_meta_learner", "best_per_category"
    ]
    
    # Load old leaderboard to retrieve existing validation rows if needed
    df_lead_old = pd.read_csv("experiments/leaderboard.csv")
    
    leaderboard_records = []
    
    for h in horizons:
        print(f"\n{'='*30} Processing Horizon h={h} {'='*30}")
        target_col = f"target_h{h}"
        y_val_true = df_feat.loc[val_mask, target_col]
        y_test_true = df_feat.loc[test_mask, target_col]
        
        # 1. Locate latest full test run for each model
        model_test_preds = {}
        model_test_intervals = {}
        
        for m in all_models:
            matches = sorted(runs_dir.glob(f"*_{m}_h{h}"))
            valid_runs = []
            for r in matches:
                pf = r / "predictions_test.csv"
                if pf.exists():
                    try:
                        df_chk = pd.read_csv(pf)
                        if len(df_chk) >= 1400:
                            valid_runs.append((r, len(df_chk)))
                    except Exception:
                        pass
            if valid_runs:
                latest_run = valid_runs[-1][0]
                df_p = pd.read_csv(latest_run / "predictions_test.csv")
                if len(df_p) == len(y_test_true):
                    model_test_preds[m] = pd.Series(df_p["y_pred"].values, index=y_test_true.index)
                    model_test_intervals[m] = {
                        "lower_80": df_p.get("lower_80", pd.Series(np.nan, index=df_p.index)).values,
                        "upper_80": df_p.get("upper_80", pd.Series(np.nan, index=df_p.index)).values,
                        "lower_95": df_p.get("lower_95", pd.Series(np.nan, index=df_p.index)).values,
                        "upper_95": df_p.get("upper_95", pd.Series(np.nan, index=df_p.index)).values,
                    }
                else:
                    print(f"Warning: length mismatch for {m} h={h}: {len(df_p)} vs {len(y_test_true)}")
            else:
                print(f"Warning: No valid run found for {m} h={h}")
                
        # Naive test prediction
        naive_test_p = model_test_preds["naive"]
        m_naive_test = evaluate_predictions(y_test_true, naive_test_p, y_train_history=y_tr_val_hist)
        mase_naive_test = m_naive_test["MASE"]
        
        # Validation subset from old leaderboard
        lead_val_sub = df_lead_old[(df_lead_old["horizon"] == h) & (df_lead_old["split"] == "validation")].set_index("model")
        lead_test_sub = df_lead_old[(df_lead_old["horizon"] == h) & (df_lead_old["split"] == "test")].set_index("model")
        
        for m in all_models:
            # --- VALIDATION RECORD ---
            if m in lead_val_sub.index:
                v_row = lead_val_sub.loc[m]
                leaderboard_records.append({
                    "model": m,
                    "horizon": h,
                    "split": "validation",
                    "MAE": v_row["MAE"],
                    "RMSE": v_row["RMSE"],
                    "MAPE": v_row["MAPE"],
                    "sMAPE": v_row["sMAPE"],
                    "MASE": v_row["MASE"],
                    "R2": v_row["R2"],
                    "Bias": v_row["Bias"],
                    "Directional_Accuracy": v_row["Directional_Accuracy"],
                    "Skill_vs_Naive": v_row["Skill_vs_Naive"],
                    "n_obs": v_row["n_obs"],
                    "Coverage_80": np.nan,
                    "Width_80_LKR": np.nan,
                    "Width_80_Pct": np.nan,
                    "Coverage_95": np.nan,
                    "Width_95_LKR": np.nan,
                    "Width_95_Pct": np.nan,
                    "MASE_CI_95": v_row["MASE_CI_95"],
                    "Diff_Naive_CI_95": np.nan,
                    "DM_stat_vs_Naive": np.nan,
                    "DM_pval_vs_Naive": np.nan,
                    "DM_pval_Holm_vs_Naive": np.nan
                })
                
            # --- TEST RECORD ---
            test_p = model_test_preds.get(m)
            if test_p is not None:
                t_mets = evaluate_predictions(y_test_true, test_p, y_train_history=y_tr_val_hist)
                skill_te = compute_skill_vs_naive(t_mets["MASE"], mase_naive_test)
                diff_point = t_mets["MASE"] - mase_naive_test
                
                # Week-block bootstrap
                boot_test = block_bootstrap_mase(
                    y_test_true, test_p, y_naive_pred=naive_test_p,
                    y_train_history=y_tr_val_hist, week_indices=test_weeks,
                    block_length=4, n_boot=1000, seed=42
                )
                
                # DM test
                dm_stat, dm_pval = diebold_mariano_test(y_test_true, test_p, naive_test_p, h=h, week_indices=test_weeks)
                
                # Conformal coverage & widths
                ints = model_test_intervals.get(m, {})
                l80, u80 = ints.get("lower_80"), ints.get("upper_80")
                l95, u95 = ints.get("lower_95"), ints.get("upper_95")
                
                if l80 is not None and pd.notna(l80).any():
                    val_y = y_test_true.values
                    orig_y = y_orig_test.values
                    cov_80 = round(float(np.mean((val_y >= l80) & (val_y <= u80)) * 100.0), 2)
                    w80_lkr = round(float(np.mean(u80 - l80)), 2)
                    w80_pct = round(float(np.mean((u80 - l80) / orig_y) * 100.0), 2)
                    cov_95 = round(float(np.mean((val_y >= l95) & (val_y <= u95)) * 100.0), 2)
                    w95_lkr = round(float(np.mean(u95 - l95)), 2)
                    w95_pct = round(float(np.mean((u95 - l95) / orig_y) * 100.0), 2)
                elif m in lead_test_sub.index:
                    t_row = lead_test_sub.loc[m]
                    cov_80 = t_row.get("Coverage_80")
                    w80_lkr = t_row.get("Width_80_LKR")
                    w80_pct = t_row.get("Width_80_Pct")
                    cov_95 = t_row.get("Coverage_95")
                    w95_lkr = t_row.get("Width_95_LKR")
                    w95_pct = t_row.get("Width_95_Pct")
                else:
                    cov_80, w80_lkr, w80_pct = np.nan, np.nan, np.nan
                    cov_95, w95_lkr, w95_pct = np.nan, np.nan, np.nan
                    
                leaderboard_records.append({
                    "model": m,
                    "horizon": h,
                    "split": "test",
                    "MAE": t_mets["MAE"],
                    "RMSE": t_mets["RMSE"],
                    "MAPE": t_mets["MAPE"],
                    "sMAPE": t_mets["sMAPE"],
                    "MASE": t_mets["MASE"],
                    "R2": t_mets["R2"],
                    "Bias": t_mets["Bias"],
                    "Directional_Accuracy": t_mets["Directional_Accuracy"],
                    "Skill_vs_Naive": round(float(skill_te), 2),
                    "n_obs": t_mets["n_obs"],
                    "Coverage_80": cov_80,
                    "Width_80_LKR": w80_lkr,
                    "Width_80_Pct": w80_pct,
                    "Coverage_95": cov_95,
                    "Width_95_LKR": w95_lkr,
                    "Width_95_Pct": w95_pct,
                    "MASE_CI_95": f"[{boot_test.get('mase_ci_low')}, {boot_test.get('mase_ci_high')}]",
                    "Diff_Naive_CI_95": f"[{boot_test.get('diff_naive_ci_low')}, {boot_test.get('diff_naive_ci_high')}]",
                    "DM_stat_vs_Naive": round(dm_stat, 4) if pd.notna(dm_stat) else 0.0,
                    "DM_pval_vs_Naive": round(dm_pval, 4) if pd.notna(dm_pval) else 1.0,
                    "DM_pval_Holm_vs_Naive": np.nan
                })
                
    df_lead_new = pd.DataFrame(leaderboard_records)
    
    # Apply Holm correction per horizon
    test_mask_lead = df_lead_new["split"] == "test"
    for h in horizons:
        h_idx = df_lead_new[test_mask_lead & (df_lead_new["horizon"] == h)].index
        p_raw = df_lead_new.loc[h_idx, "DM_pval_vs_Naive"].dropna().values
        if len(p_raw) > 0:
            adj_p = holm_bonferroni_correction(p_raw)
            df_lead_new.loc[h_idx, "DM_pval_Holm_vs_Naive"] = [round(x, 4) for x in adj_p]
            
    # Automated Assertions
    print("\nRunning automated consistency checks across all test records...")
    test_recs = df_lead_new[df_lead_new["split"] == "test"]
    failures = []
    
    for idx, r in test_recs.iterrows():
        m = r["model"]
        h_val = r["horizon"]
        mase_m = r["MASE"]
        naive_mase = test_recs[(test_recs["horizon"] == h_val) & (test_recs["model"] == "naive")]["MASE"].values[0]
        diff_pt = mase_m - naive_mase
        
        # (a) CI contains point difference
        ci_str = str(r["Diff_Naive_CI_95"]).strip("[]")
        if "," in ci_str:
            c_low, c_high = [float(x) for x in ci_str.split(",")]
            if not (c_low - 0.005 <= diff_pt <= c_high + 0.005):
                failures.append(f"FAIL (a): Horizon {h_val} Model {m} diff={diff_pt:.4f} not in [{c_low}, {c_high}]")
                
        # (b) DM stat sign agrees with MASE difference
        dm_st = r["DM_stat_vs_Naive"]
        if pd.notna(dm_st) and m != "naive" and abs(diff_pt) >= 1e-4:
            if np.sign(dm_st) != np.sign(diff_pt):
                failures.append(f"FAIL (b): Horizon {h_val} Model {m} DM_stat ({dm_st:+.4f}) disagrees with diff ({diff_pt:+.4f})")
                
        # (c) Holm p >= raw p
        raw_p = r["DM_pval_vs_Naive"]
        holm_p = r["DM_pval_Holm_vs_Naive"]
        if pd.notna(raw_p) and pd.notna(holm_p):
            if holm_p < raw_p - 1e-6:
                failures.append(f"FAIL (c): Horizon {h_val} Model {m} Holm p ({holm_p}) < raw p ({raw_p})")
                
    if failures:
        print(f"AUTOMATED CHECKS FAILED: {len(failures)} issues detected:")
        for f in failures:
            print("  ", f)
        raise AssertionError(f"Build Failed: {len(failures)} automated check failures in leaderboard statistics.")
    else:
        print("ALL AUTOMATED CHECKS PASSED: 100% CI containment, DM sign consistency, and Holm monotonicity verified!")
        
    df_lead_new.to_csv("experiments/leaderboard.csv", index=False)
    print("Saved experiments/leaderboard.csv successfully.")
    
    # By-horizon aggregated leaderboard
    df_by_horizon = df_lead_new.groupby(["model", "horizon", "split"])[
        ["MAE", "RMSE", "sMAPE", "MASE", "R2", "Directional_Accuracy", "Skill_vs_Naive"]
    ].mean().reset_index()
    df_by_horizon.to_csv("experiments/leaderboard_by_horizon.csv", index=False)
    print("Saved experiments/leaderboard_by_horizon.csv successfully.")

if __name__ == "__main__":
    update_all()
