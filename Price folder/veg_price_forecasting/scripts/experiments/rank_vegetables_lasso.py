import pandas as pd
import numpy as np

by_veg = pd.read_csv("experiments/leaderboard_by_vegetable.csv")
h4_veg = by_veg[by_veg["horizon"] == 4].copy()

lasso = h4_veg[h4_veg["model"] == "lasso"].set_index("vegetable")
naive = h4_veg[h4_veg["model"] == "naive"].set_index("vegetable")

df_rank = pd.DataFrame(index=lasso.index)
df_rank["test_MAE"] = lasso["test_MAE"].round(2)
df_rank["test_sMAPE"] = lasso["test_sMAPE"].round(2)
df_rank["test_MASE"] = lasso["test_MASE"].round(4)
df_rank["naive_MASE"] = naive["test_MASE"].round(4)
df_rank["test_R2"] = lasso["test_R2"].round(4)
df_rank["skill_vs_naive"] = ((1.0 - df_rank["test_MASE"] / df_rank["naive_MASE"]) * 100.0).round(2)

# Load data to compute test standard deviation
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.splits import get_split_masks

cfg = load_config()
_, df_long = load_and_preprocess_vegetables(cfg)
_, _, test_mask = get_split_masks(df_long, cfg, horizon=4)
te_df = df_long[test_mask]
veg_stats = te_df.groupby("product_name")["price_lkr"].agg(["std", "mean"]).reset_index()
veg_stats["cv"] = (veg_stats["std"] / veg_stats["mean"]).round(3)
veg_stats = veg_stats.set_index("product_name")

df_rank["test_std"] = veg_stats["std"].round(2)
df_rank["is_low_variance"] = df_rank["test_std"] < 15.0

df_sorted = df_rank.sort_values("skill_vs_naive", ascending=False)
print("=" * 90)
print("ALL 32 VEGETABLES RANKED BY SKILL VS NAIVE (Selected Model: Lasso, h=4)")
print("=" * 90)
print(df_sorted.to_string())

df_sorted.to_csv("results/tables/vegetable_skill_ranking_lasso_h4.csv")
print("\nSaved to results/tables/vegetable_skill_ranking_lasso_h4.csv")
