import pandas as pd
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
h = 4
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)

test_df = df_feat.loc[test_mask]
leafy_test = test_df[test_df["category"] == "leafy vegetables"]
print("Leafy test count:", len(leafy_test))
print("is_stale_run value counts in test leafy:")
print(leafy_test["is_stale_run"].value_counts(dropna=False))
print("\nUnique dates in test leafy:", leafy_test["approx_date"].min(), "to", leafy_test["approx_date"].max())
print("is_stale_run in train leafy:", df_feat.loc[train_mask & (df_feat["category"]=="leafy vegetables"), "is_stale_run"].value_counts())
print("is_stale_run in val leafy:", df_feat.loc[val_mask & (df_feat["category"]=="leafy vegetables"), "is_stale_run"].value_counts())
