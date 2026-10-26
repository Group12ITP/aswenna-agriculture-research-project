import sys
from pathlib import Path
import numpy as np
import pandas as pd
from prophet import Prophet

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.models.statistical import ProphetRollingForecaster
from src.splits import get_split_masks

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)

# Load existing prophet test predictions from runs or leaderboard_by_vegetable
run_path = None
# Find prophet run path for h=4 with full 32 vegetables
for p in sorted(Path("experiments/runs").glob("*_prophet_h4")):
    if (p / "predictions_test.csv").exists():
        df_check = pd.read_csv(p / "predictions_test.csv")
        if len(df_check) >= 1500:
            run_path = p
            break

print(f"Found Prophet h=4 run path: {run_path}")
lead_preds = pd.read_csv(run_path / "predictions_test.csv")
print(f"Loaded {len(lead_preds)} test predictions from {run_path / 'predictions_test.csv'}")

# Verify exact match under disk-level truncation for 5 random test origins per vegetable
rng = np.random.default_rng(42)
all_vegs = df_long["product_name"].unique()

horizons = [1, 4, 8, 12]
mismatches = []
total_tested = 0

for h in [4]: # Test primary horizon first
    for veg in all_vegs:
        v_df = df_long[df_long["product_name"] == veg].sort_values("week_index").reset_index(drop=True)
        v_df["ds"] = pd.to_datetime(v_df["approx_date"])
        
        # Test split indices
        # In config, test is 2025-09-04 to 2026-08-25
        test_mask = (v_df["approx_date"] >= "2025-09-04") & (v_df["approx_date"] <= "2026-08-25")
        test_indices = v_df.index[test_mask].tolist()
        
        # Pick 5 random test origins
        sampled_origins = rng.choice(test_indices, size=min(5, len(test_indices)), replace=False)
        
        for orig in sampled_origins:
            total_tested += 1
            orig_date = v_df.loc[orig, "approx_date"]
            
            # TRUNCATE: Delete all data after origin from inputs
            truncated_df = v_df.iloc[:orig + 1].copy()
            
            # We need the future date ds for orig + h (calendar grid)
            # The future calendar date is known from the reporting calendar
            future_date = v_df.loc[min(orig + h, len(v_df)-1), "ds"] if orig + h < len(v_df) else v_df.loc[orig, "ds"] + pd.Timedelta(weeks=h)
            
            # Run Prophet rolling forecast logic on truncated data
            # Target indices for test: first_t is test_pos[0] = test_indices[0]
            first_t = test_indices[0]
            
            df_p = truncated_df.copy()
            df_p["y_log"] = np.log(df_p["price_lkr"].ffill().bfill().clip(lower=1.0))
            
            # Model fit on history up to first_t
            tr_df = df_p.iloc[:first_t][["ds", "y_log"]].rename(columns={"y_log": "y"})
            forecaster = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
            forecaster.fit(tr_df)
            
            # Predict timeline including orig and orig + h
            eval_ds = pd.DataFrame({"ds": [v_df.loc[orig, "ds"], future_date]})
            fc = forecaster.predict(eval_ds)
            pred_base_orig = fc.loc[0, "yhat"]
            pred_base_target = fc.loc[1, "yhat"]
            
            actual_z_orig = df_p.loc[orig, "y_log"]
            res_t = actual_z_orig - pred_base_orig
            rho = 0.88 ** h
            fc_log = pred_base_target + res_t * rho
            pred_truncated = max(0.0, float(np.exp(fc_log)))
            
            # Compare with leaderboard prediction
            match_row = lead_preds[(lead_preds["product_name"] == veg) & (lead_preds["approx_date"] == orig_date)]
            if len(match_row) > 0:
                lead_pred_val = match_row["y_pred"].values[0]
                diff = abs(pred_truncated - lead_pred_val)
                if diff > 1e-3:
                    mismatches.append((veg, orig_date, pred_truncated, lead_pred_val, diff))
            else:
                print(f"Warning: No match found for {veg} on {orig_date}")

print(f"\n--- HARD TRUNCATION TEST RESULTS ---")
print(f"Total origins tested: {total_tested}")
print(f"Total mismatches (> 1e-3): {len(mismatches)}")
if mismatches:
    print("Mismatches sample:", mismatches[:5])
else:
    print("ALL TRUNCATION FORECASTS ARE IDENTICAL TO LEADERBOARD!")
