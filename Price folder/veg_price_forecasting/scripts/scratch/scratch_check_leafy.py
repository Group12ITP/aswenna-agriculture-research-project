import pandas as pd
import numpy as np
import yaml

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.metrics import evaluate_predictions, compute_skill_vs_naive

cfg = load_config()
_, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg, include_cross_veg=True)

h = 4
target_col = f"target_h{h}"
target_week = df_feat["week_index"] + h

train_mask = (target_week <= (369 - h)) & df_feat[target_col].notna()
val_mask = (target_week >= 369) & (target_week <= 416) & df_feat[target_col].notna()
test_mask = (target_week >= 417) & (target_week <= 464) & df_feat[target_col].notna()

# Check leaderboard_by_vegetable.csv
df_by_veg = pd.read_csv("experiments/leaderboard_by_vegetable.csv")
leafy_vegs = df_feat[df_feat["category"] == "leafy vegetables"]["product_name"].unique()
print("Leafy vegetables:", leafy_vegs)

lasso_veg = df_by_veg[(df_by_veg["model"] == "lasso") & (df_by_veg["horizon"] == 4)]
leafy_lasso = lasso_veg[lasso_veg["vegetable"].isin(leafy_vegs)]
print("\nLeafy Lasso in leaderboard_by_vegetable.csv (chosen mode):")
print(leafy_lasso[["vegetable", "test_MAE", "test_MASE", "test_sMAPE"]])
print("Mean test_MAE:", leafy_lasso["test_MAE"].mean())
print("Mean test_MASE:", leafy_lasso["test_MASE"].mean())

# Check leafy_vegetables_clean_audit.csv and leafy_stale_vs_clean.csv
if (pd.Series("results/tables/leafy_stale_vs_clean.csv").apply(lambda p: pd.io.common.file_exists(p))).iloc[0]:
    print("\nresults/tables/leafy_stale_vs_clean.csv:")
    print(pd.read_csv("results/tables/leafy_stale_vs_clean.csv"))
