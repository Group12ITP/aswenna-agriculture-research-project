import numpy as np
import pandas as pd
import yaml
import warnings
warnings.filterwarnings('ignore')
from prophet import Prophet

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.models.baselines import NaiveForecaster
from src.models.statistical import ProphetRollingForecaster

cfg = load_config()
_, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg, include_cross_veg=True)

print("="*80)
print("PROPHET FORENSIC AUDIT: ANNUAL REFITS & TREND SLOPES")
print("="*80)

# Annual cutoffs: Each August from 2019 to 2025
date_df = df_feat[["week_index", "year", "month", "week_of_month", "approx_date"]].drop_duplicates().sort_values("week_index")

cutoffs = []
for yr in range(2019, 2026):
    aug_rows = date_df[(date_df["year"] == yr) & (date_df["month"] == 8)]
    if len(aug_rows) > 0:
        last_aug = aug_rows.iloc[-1]
        cutoffs.append((yr, last_aug["week_index"], last_aug["approx_date"]))

print("Annual Cutoffs (August of each year):")
for yr, wk, dt in cutoffs:
    print(f"  {yr}: week_index {wk}, date {dt}")

annual_results = []
h = 4
target_col = f"target_h{h}"

for yr, wk_cutoff, dt_cutoff in cutoffs:
    eval_target_weeks = range(wk_cutoff + 1, min(465, wk_cutoff + 49))
    
    print(f"\nEvaluating Year following Aug {yr} (Cutoff week {wk_cutoff})...")
    prophet_preds = []
    naive_preds = []
    actuals = []
    
    for veg in df_feat["product_name"].unique():
        v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index").copy()
        v_df["ds"] = pd.to_datetime(v_df["approx_date"])
        
        # Training prices up to cutoff
        tr_mask = v_df["week_index"] <= (wk_cutoff - h)
        if tr_mask.sum() == 0:
            tr_mask = v_df["week_index"] <= wk_cutoff
        train_prices = v_df.loc[tr_mask, "price_lkr"].values
        
        # Target evaluation rows
        eval_rows = v_df[(v_df["week_index"] + h).isin(eval_target_weeks) & v_df[target_col].notna()]
        if len(eval_rows) == 0:
            continue
            
        eval_idx = eval_rows.index
        eval_pos = [v_df.index.get_loc(idx) for idx in eval_idx]
        
        # Naive Forecaster
        naive_m = NaiveForecaster()
        naive_m.fit(train_prices)
        for idx in eval_idx:
            curr_w = v_df.loc[idx, "week_index"]
            hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
            naive_preds.append((idx, naive_m.predict(horizon=h, y_history=hist)))
            actuals.append((idx, v_df.loc[idx, target_col]))
            
        # Prophet Forecaster
        forecaster = ProphetRollingForecaster()
        fc = forecaster.rolling_forecast(v_df, eval_pos, horizon=h)
        for idx, pos in zip(eval_idx, eval_pos):
            prophet_preds.append((idx, fc.get(pos, float(v_df.loc[idx, "price_lkr"]))))

    s_act = pd.Series({idx: a for idx, a in actuals})
    s_naive = pd.Series({idx: p for idx, p in naive_preds})
    s_prophet = pd.Series({idx: p for idx, p in prophet_preds})
    
    # Scale: for cutoff 416 (test year), use the standardized test scaling denominator
    if wk_cutoff == 416:
        train_val_mask = (df_feat["week_index"] + h <= 416) & df_feat[target_col].notna()
        hist_prices = df_feat.loc[train_val_mask, "price_lkr"]
    else:
        hist_prices = df_feat[df_feat["week_index"] <= wk_cutoff]["price_lkr"].values
        
    m_p = evaluate_predictions(s_act, s_prophet, y_train_history=hist_prices)
    m_n = evaluate_predictions(s_act, s_naive, y_train_history=hist_prices)
    skill = compute_skill_vs_naive(m_p["MASE"], m_n["MASE"])
    
    print(f"  Aug {yr} - Aug {yr+1}: N={len(s_act)} | Prophet MAE={m_p['MAE']}, Naive MAE={m_n['MAE']}, Prophet MASE={m_p['MASE']:.4f}, Naive MASE={m_n['MASE']:.4f}, Skill={skill:+.2f}%, Bias={m_p['Bias']:+.2f} Rs")
    annual_results.append({
        "period": f"Aug {yr} - Aug {yr+1}",
        "cutoff_year": yr,
        "cutoff_week": wk_cutoff,
        "n_obs": len(s_act),
        "prophet_MAE": round(m_p["MAE"], 2),
        "naive_MAE": round(m_n["MAE"], 2),
        "prophet_MASE": round(m_p["MASE"], 4),
        "naive_MASE": round(m_n["MASE"], 4),
        "skill_vs_naive_pct": round(skill, 2),
        "prophet_bias_lkr": round(m_p["Bias"], 2)
    })

df_annual = pd.DataFrame(annual_results)
df_annual.to_csv("results/tables/prophet_annual_refits.csv", index=False)
print("\nSaved annual refits to results/tables/prophet_annual_refits.csv")

# Now compute terminal trend slope for Validation fit (cutoff week 368) vs Test fit (cutoff week 416)
print("\n" + "="*80)
print("FITTED TERMINAL TREND SLOPES: VALIDATION FIT (wk 368) vs TEST FIT (wk 416)")
print("="*80)

slopes = []
for veg in df_feat["product_name"].unique():
    v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index").copy()
    v_df["ds"] = pd.to_datetime(v_df["approx_date"])
    v_df["y_log"] = np.log(v_df["price_lkr"].ffill().bfill().clip(lower=1.0))
    
    # Val fit: <= 368
    tr_val = v_df[v_df["week_index"] <= 368][["ds", "y_log"]].rename(columns={"y_log": "y"})
    m_val = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    m_val.fit(tr_val)
    fc_val = m_val.predict(tr_val[["ds"]])
    trend_val = fc_val["trend"].values
    slope_val = (trend_val[-1] - trend_val[-12]) / 12.0
    k_val = m_val.params["k"][0][0] if "k" in m_val.params else np.nan
    
    # Test fit: <= 416
    tr_test = v_df[v_df["week_index"] <= 416][["ds", "y_log"]].rename(columns={"y_log": "y"})
    m_test = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    m_test.fit(tr_test)
    fc_test = m_test.predict(tr_test[["ds"]])
    trend_test = fc_test["trend"].values
    slope_test = (trend_test[-1] - trend_test[-12]) / 12.0
    k_test = m_test.params["k"][0][0] if "k" in m_test.params else np.nan
    
    slopes.append({
        "vegetable": veg,
        "val_terminal_slope_weekly": slope_val,
        "test_terminal_slope_weekly": slope_test,
        "slope_diff": slope_test - slope_val,
        "k_val": k_val,
        "k_test": k_test
    })

df_slopes = pd.DataFrame(slopes)
df_slopes.to_csv("results/tables/prophet_terminal_slopes.csv", index=False)
print(f"Mean Val Terminal Weekly Slope:  {df_slopes['val_terminal_slope_weekly'].mean():.6f}")
print(f"Mean Test Terminal Weekly Slope: {df_slopes['test_terminal_slope_weekly'].mean():.6f}")
print(f"Median Val Terminal Slope:       {df_slopes['val_terminal_slope_weekly'].median():.6f}")
print(f"Median Test Terminal Slope:      {df_slopes['test_terminal_slope_weekly'].median():.6f}")
print("Saved slopes to results/tables/prophet_terminal_slopes.csv")
