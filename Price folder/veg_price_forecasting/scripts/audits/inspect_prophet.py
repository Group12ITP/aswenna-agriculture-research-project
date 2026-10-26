import sys
from pathlib import Path
import numpy as np
import pandas as pd
from prophet import Prophet

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import evaluate_predictions

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)

# Check dates and price levels across splits
print("--- SPLIT DATE RANGES ---")
print("Train:", df_feat.loc[train_mask, "approx_date"].min(), "to", df_feat.loc[train_mask, "approx_date"].max())
print("Val:  ", df_feat.loc[val_mask, "approx_date"].min(), "to", df_feat.loc[val_mask, "approx_date"].max())
print("Test: ", df_feat.loc[test_mask, "approx_date"].min(), "to", df_feat.loc[test_mask, "approx_date"].max())

# Mean and median prices
for split_name, mask in [("Train", train_mask), ("Val", val_mask), ("Test", test_mask)]:
    mean_p = df_feat.loc[mask, "price_lkr"].mean()
    median_p = df_feat.loc[mask, "price_lkr"].median()
    print(f"{split_name} price: Mean = {mean_p:.2f} Rs, Median = {median_p:.2f} Rs")

# Examine Prophet predictions in leaderboard
lead = pd.read_csv("experiments/leaderboard.csv")
p_rows = lead[lead["model"] == "prophet"]
print("\n--- PROPHET LEADERBOARD ROWS ---")
print(p_rows[["horizon", "split", "MAE", "sMAPE", "MASE", "R2", "Bias", "Skill_vs_Naive"]])

# Check per-vegetable Prophet bias and error on validation vs test
by_veg = pd.read_csv("experiments/leaderboard_by_vegetable.csv")
p_veg = by_veg[by_veg["model"] == "prophet"]
print("\nProphet h=4 by veg sample:")
print(p_veg[p_veg["horizon"] == 4][["vegetable", "val_MAE", "val_MASE", "test_MAE", "test_MASE", "test_sMAPE"]].head(10))
