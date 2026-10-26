import pandas as pd
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.train import prepare_feature_matrices
from src.models.classical import get_classical_model
from src.metrics import evaluate_predictions

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
h = 4
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
target_col = f"target_h{h}"

X, y, _ = prepare_feature_matrices(df_feat, target_col=target_col)
is_leafy_test = test_mask & (df_feat["category"] == "leafy vegetables")

# 1. Naive persistence
y_test_leafy = df_feat.loc[is_leafy_test, target_col]
naive_leafy = df_feat.loc[is_leafy_test, "price_lkr"] # origin price
m_naive = evaluate_predictions(y_test_leafy, naive_leafy)
print("Naive on test leafy:", m_naive["MAE"], m_naive["sMAPE"], m_naive["R2"])

# 2. Lasso raw_level vs log_ratio
# In run_retrain_target_splits.py, Lasso was fit on train | val_tune or train | val
# Let's inspect test predictions for Lasso raw_level and log_ratio
