import pandas as pd
import numpy as np
import yaml

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.metrics import evaluate_predictions, compute_skill_vs_naive
from src.models.statistical import ProphetRollingForecaster

cfg = load_config()
_, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg, include_cross_veg=True)

h = 4
target_col = f"target_h{h}"
target_week = df_feat["week_index"] + h

train_mask = (target_week <= (369 - h)) & df_feat[target_col].notna()
val_mask = (target_week >= 369) & (target_week <= 416) & df_feat[target_col].notna()
test_mask = (target_week >= 417) & (target_week <= 464) & df_feat[target_col].notna()

y_test_true = df_feat.loc[test_mask, target_col]
y_origin_test = df_feat.loc[test_mask, "price_lkr"]

# 1. Leaderboard values for test
df_lead = pd.read_csv("experiments/leaderboard.csv")
lead_prophet = df_lead[(df_lead["model"]=="prophet") & (df_lead["horizon"]==4) & (df_lead["split"]=="test")].iloc[0]
lead_naive = df_lead[(df_lead["model"]=="naive") & (df_lead["horizon"]==4) & (df_lead["split"]=="test")].iloc[0]

print("Leaderboard h=4 Test:")
print(f"  Naive:   MAE={lead_naive['MAE']}, MASE={lead_naive['MASE']}, Bias={lead_naive['Bias']}, n={lead_naive['n_obs']}")
print(f"  Prophet: MAE={lead_prophet['MAE']}, MASE={lead_prophet['MASE']}, Bias={lead_prophet['Bias']}, Skill={lead_prophet['Skill_vs_Naive']}%, n={lead_prophet['n_obs']}")

# 2. Check Naive on test_mask:
m_naive_test = evaluate_predictions(
    y_test_true, y_origin_test,
    y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"],
    y_prev=y_origin_test
)
print("\nRecomputed Naive on test_mask:")
print(f"  MAE={m_naive_test['MAE']}, MASE={m_naive_test['MASE']}, Bias={m_naive_test['Bias']}, n={m_naive_test['n_obs']}")

# 3. Check what run_prophet_annual_audit did for cutoff 416:
# In run_prophet_annual_audit:
# eval_target_weeks = range(417, 465) (417 to 464)
# eval_origin_weeks = [tw - 4 for tw in eval_target_weeks] = [413 to 460]
# But notice: in run_prophet_annual_audit, how was df_feat built?
# line 15: df_feat = build_vegetable_features(df_long, cfg, include_cross_veg=False) !!!
# AND notice how naive_preds was populated!
# Let's check!
