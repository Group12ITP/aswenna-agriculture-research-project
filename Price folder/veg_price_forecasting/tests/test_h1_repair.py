import sys
from pathlib import Path
import numpy as np
import pandas as pd

from src.utils import load_config, set_seeds
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import (
    evaluate_predictions, compute_skill_vs_naive,
    block_bootstrap_mase, diebold_mariano_test,
    holm_bonferroni_correction
)

cfg = load_config()
set_seeds(42)

df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)

test_weeks = df_feat.loc[test_mask, "week_index"]
y_orig_test = df_feat.loc[test_mask, "price_lkr"]
y_tr_val_hist = df_feat.loc[train_mask | val_mask, "price_lkr"]

h = 1
target_col = f"target_h{h}"
y_test_true = df_feat.loc[test_mask, target_col]

# Check latest runs
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

model_test_preds = {}
for m in all_models:
    matches = sorted(runs_dir.glob(f"*_{m}_h{h}"))
    valid_runs = []
    for r in matches:
        pf = r / "predictions_test.csv"
        if pf.exists():
            df_chk = pd.read_csv(pf)
            if len(df_chk) >= 1400:
                valid_runs.append((r, len(df_chk)))
    if valid_runs:
        latest_run = valid_runs[-1][0]
        df_p = pd.read_csv(latest_run / "predictions_test.csv")
        # Ensure row alignment with test_mask
        # Check if df_p matches test_mask length
        if len(df_p) == len(y_test_true):
            model_test_preds[m] = pd.Series(df_p["y_pred"].values, index=y_test_true.index)
        else:
            print(f"Warning: len mismatch for {m}: {len(df_p)} vs {len(y_test_true)}")

naive_pred = model_test_preds["naive"]
mase_naive = evaluate_predictions(y_test_true, naive_pred, y_train_history=y_tr_val_hist)["MASE"]
print(f"Naive h=1 test MASE: {mase_naive:.4f}")

results = []
failures = []

for m in all_models:
    yp = model_test_preds.get(m)
    if yp is None:
        continue
    mets = evaluate_predictions(y_test_true, yp, y_train_history=y_tr_val_hist)
    mase_m = mets["MASE"]
    diff_point = mase_m - mase_naive
    
    # Block bootstrap
    boot = block_bootstrap_mase(
        y_test_true, yp, y_naive_pred=naive_pred,
        y_train_history=y_tr_val_hist, week_indices=test_weeks,
        block_length=4, n_boot=1000, seed=42
    )
    
    ci_low = boot["diff_naive_ci_low"]
    ci_high = boot["diff_naive_ci_high"]
    
    # DM test
    dm_stat, dm_pval = diebold_mariano_test(y_test_true, yp, naive_pred, h=h, week_indices=test_weeks)
    
    # Automated check (a): CI contains point estimate
    # Note: allow 0.005 slack for discretization/rounding
    ci_contains = (ci_low - 0.005 <= diff_point <= ci_high + 0.005) if m != "naive" else True
    
    # Automated check (b): DM sign agrees with diff_point
    if m == "naive" or abs(diff_point) < 1e-4:
        sign_agrees = True
    else:
        sign_agrees = (np.sign(dm_stat) == np.sign(diff_point))
        
    results.append({
        "model": m,
        "MASE": mase_m,
        "Diff_Naive": round(diff_point, 4),
        "CI_95": f"[{ci_low}, {ci_high}]",
        "CI_contains": ci_contains,
        "DM_stat": round(dm_stat, 4) if pd.notna(dm_stat) else 0.0,
        "DM_pval": round(dm_pval, 4) if pd.notna(dm_pval) else 1.0,
        "Sign_agrees": sign_agrees
    })
    
    if not ci_contains:
        failures.append(f"Check (a) FAIL: {m} diff={diff_point:.4f} not in [{ci_low}, {ci_high}]")
    if not sign_agrees:
        failures.append(f"Check (b) FAIL: {m} diff={diff_point:.4f} has DM_stat={dm_stat:.4f}")

df_res = pd.DataFrame(results)

# Holm correction
p_raw = df_res["DM_pval"].values
p_holm = holm_bonferroni_correction(p_raw)
df_res["DM_pval_Holm"] = [round(x, 4) for x in p_holm]

# Check (c): Holm p >= raw p
for i, r in df_res.iterrows():
    if r["DM_pval_Holm"] < r["DM_pval"] - 1e-6:
        failures.append(f"Check (c) FAIL: {r['model']} Holm p ({r['DM_pval_Holm']}) < raw p ({r['DM_pval']})")

print(df_res.to_string(index=False))

print("\n--- AUDIT SUMMARY ---")
print(f"Total models tested: {len(df_res)}")
print(f"Total failures: {len(failures)}")
if failures:
    for f in failures:
        print(" ", f)
else:
    print("ALL CHECKS PASSED PERFECTLY!")
