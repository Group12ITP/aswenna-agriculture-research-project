import numpy as np
import pandas as pd
import yaml
import warnings
warnings.filterwarnings('ignore')

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.models.statistical import ProphetRollingForecaster
from src.models.baselines import NaiveForecaster

cfg = load_config()
_, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg, include_cross_veg=True)

h = 4
target_col = f"target_h{h}"
target_week = df_feat["week_index"] + h

train_mask = (target_week <= (369 - h)) & df_feat[target_col].notna()
val_mask = (target_week >= 369) & (target_week <= 416) & df_feat[target_col].notna()
test_mask = (target_week >= 417) & (target_week <= 464) & df_feat[target_col].notna()

# Test evaluation of Prophet and Naive using ProphetRollingForecaster and NaiveForecaster
val_preds_prophet = []
test_preds_prophet = []
val_preds_naive = []
test_preds_naive = []

for veg in df_feat["product_name"].unique():
    v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index").copy()
    v_df["ds"] = pd.to_datetime(v_df["approx_date"])
    full_series = v_df["price_lkr"].values
    
    val_idx = v_df.index[val_mask.loc[v_df.index]]
    test_idx = v_df.index[test_mask.loc[v_df.index]]
    val_pos = [v_df.index.get_loc(idx) for idx in val_idx]
    test_pos = [v_df.index.get_loc(idx) for idx in test_idx]
    
    # Naive
    naive_m = NaiveForecaster()
    naive_m.fit(v_df.loc[train_mask.loc[v_df.index], "price_lkr"].values)
    for idx in val_idx:
        curr_w = v_df.loc[idx, "week_index"]
        hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
        val_preds_naive.append((idx, naive_m.predict(horizon=h, y_history=hist)))
    for idx in test_idx:
        curr_w = v_df.loc[idx, "week_index"]
        hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
        test_preds_naive.append((idx, naive_m.predict(horizon=h, y_history=hist)))
        
    # Prophet
    forecaster = ProphetRollingForecaster()
    val_fc = forecaster.rolling_forecast(v_df, val_pos, horizon=h)
    test_fc = forecaster.rolling_forecast(v_df, test_pos, horizon=h)
    
    for idx, pos in zip(val_idx, val_pos):
        val_preds_prophet.append((idx, val_fc.get(pos, float(v_df.loc[idx, "price_lkr"]))))
    for idx, pos in zip(test_idx, test_pos):
        test_preds_prophet.append((idx, test_fc.get(pos, float(v_df.loc[idx, "price_lkr"]))))

s_val_naive = pd.Series({idx: p for idx, p in val_preds_naive})
s_test_naive = pd.Series({idx: p for idx, p in test_preds_naive})
s_val_prophet = pd.Series({idx: p for idx, p in val_preds_prophet})
s_test_prophet = pd.Series({idx: p for idx, p in test_preds_prophet})

y_val_true = df_feat.loc[val_mask, target_col]
y_test_true = df_feat.loc[test_mask, target_col]

m_val_n = evaluate_predictions(y_val_true, s_val_naive, y_train_history=df_feat.loc[train_mask, "price_lkr"])
m_test_n = evaluate_predictions(y_test_true, s_test_naive, y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"])

m_val_p = evaluate_predictions(y_val_true, s_val_prophet, y_train_history=df_feat.loc[train_mask, "price_lkr"])
m_test_p = evaluate_predictions(y_test_true, s_test_prophet, y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"])

sk_val = compute_skill_vs_naive(m_val_p["MASE"], m_val_n["MASE"])
sk_test = compute_skill_vs_naive(m_test_p["MASE"], m_test_n["MASE"])

print("EVALUATION MATCH RESULTS:")
print(f"Validation: Naive MASE={m_val_n['MASE']}, Prophet MASE={m_val_p['MASE']}, Skill={sk_val:.2f}%, Bias={m_val_p['Bias']:+.2f} Rs")
print(f"Test:       Naive MASE={m_test_n['MASE']}, Prophet MASE={m_test_p['MASE']}, Skill={sk_test:.2f}%, Bias={m_test_p['Bias']:+.2f} Rs, n={m_test_p['n_obs']}")

df_lead = pd.read_csv("experiments/leaderboard.csv")
lead_p_val = df_lead[(df_lead["model"]=="prophet") & (df_lead["horizon"]==4) & (df_lead["split"]=="validation")].iloc[0]
lead_p_te = df_lead[(df_lead["model"]=="prophet") & (df_lead["horizon"]==4) & (df_lead["split"]=="test")].iloc[0]

print(f"Leaderboard Val: MASE={lead_p_val['MASE']}, Bias={lead_p_val['Bias']}")
print(f"Leaderboard Te:  MASE={lead_p_te['MASE']}, Bias={lead_p_te['Bias']}, Skill={lead_p_te['Skill_vs_Naive']}%, n={lead_p_te['n_obs']}")
