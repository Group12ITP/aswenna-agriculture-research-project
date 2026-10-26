import sys
from pathlib import Path
import numpy as np
import pandas as pd
from prophet import Prophet

from src.utils import load_config
from src.data import load_and_preprocess_vegetables

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)

# Find prophet run path for h=4 with full 32 vegetables
run_path = None
for p in sorted(Path("experiments/runs").glob("*_prophet_h4")):
    if (p / "predictions_test.csv").exists():
        df_check = pd.read_csv(p / "predictions_test.csv")
        if len(df_check) >= 1500:
            run_path = p
            break

lead_preds = pd.read_csv(run_path / "predictions_test.csv")
# Only consider valid evaluated origins where y_true is not null
valid_lead = lead_preds[lead_preds["y_true"].notna()]

rng = np.random.default_rng(42)
all_vegs = df_long["product_name"].unique()

mismatches = []
total_tested = 0
h = 4

for veg in all_vegs:
    v_df = df_long[df_long["product_name"] == veg].sort_values("week_index").reset_index(drop=True)
    v_df["ds"] = pd.to_datetime(v_df["approx_date"])
    
    # Valid test origins where t + h is within v_df
    test_mask = (v_df["approx_date"] >= "2025-09-04") & (v_df["approx_date"] <= "2026-08-25")
    valid_test_indices = [idx for idx in v_df.index[test_mask] if idx + h < len(v_df)]
    
    # Sample 5 random valid test origins
    sampled = rng.choice(valid_test_indices, size=5, replace=False)
    
    for orig in sampled:
        total_tested += 1
        orig_date = v_df.loc[orig, "approx_date"]
        
        # Truncate: All data after origin deleted from disk/inputs
        truncated_df = v_df.iloc[:orig + 1].copy()
        
        first_t = v_df.index[test_mask][0]
        
        df_p = truncated_df.copy()
        df_p["y_log"] = np.log(df_p["price_lkr"].ffill().bfill().clip(lower=1.0))
        
        # Fit Prophet on history up to first_t
        tr_df = df_p.iloc[:first_t][["ds", "y_log"]].rename(columns={"y_log": "y"})
        forecaster = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        forecaster.fit(tr_df)
        
        # Predict ds for origin t and future target t + h
        future_date = v_df.loc[orig + h, "ds"]
        eval_ds = pd.DataFrame({"ds": [v_df.loc[orig, "ds"], future_date]})
        fc = forecaster.predict(eval_ds)
        pred_base_orig = fc.loc[0, "yhat"]
        pred_base_target = fc.loc[1, "yhat"]
        
        actual_z_orig = df_p.loc[orig, "y_log"]
        res_t = actual_z_orig - pred_base_orig
        rho = 0.88 ** h
        fc_log = pred_base_target + res_t * rho
        pred_truncated = max(0.0, float(np.exp(fc_log)))
        
        match_row = lead_preds[(lead_preds["product_name"] == veg) & (lead_preds["approx_date"] == orig_date)]
        if len(match_row) > 0:
            lead_pred_val = match_row["y_pred"].values[0]
            diff = abs(pred_truncated - lead_pred_val)
            if diff > 1e-4:
                mismatches.append((veg, orig_date, pred_truncated, lead_pred_val, diff))

print(f"Prophet Evaluated Origins Truncation Test:")
print(f"Total tested: {total_tested}")
print(f"Total mismatches (> 1e-4): {len(mismatches)}")
if len(mismatches) == 0:
    print("ALL 160 EVALUATED ORIGINS MATCH WITH ZERO ERROR!")
