import pandas as pd
import numpy as np
from sklearn.linear_model import Lasso
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.train import prepare_feature_matrices

cfg = load_config()
_, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg)
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg)

h = 4
target_col = f"target_h{h}"
X, y_lvl, _ = prepare_feature_matrices(df_feat, target_col=target_col)
y_orig = df_feat["price_lkr"].clip(lower=1.0)
y_future = df_feat[target_col].clip(lower=1.0)
y_rat = np.log(y_future / y_orig)

mask_tr = train_mask & pd.notna(y_lvl) & pd.notna(y_rat)
mask_te = test_mask & pd.notna(y_lvl) & pd.notna(y_rat)

mod_lvl = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.1, random_state=42))])
mod_lvl.fit(X[mask_tr], y_lvl[mask_tr])
p_lvl_te = np.clip(mod_lvl.predict(X[mask_te]), 0, None)

mod_rat = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.01, random_state=42))])
mod_rat.fit(X[mask_tr], y_rat[mask_tr])
p_rat_te = y_orig[mask_te] * np.exp(mod_rat.predict(X[mask_te]))

is_leafy_te = (df_feat.loc[mask_te, "category"] == "Leafy Vegetables").values
y_te_true = y_lvl[mask_te].values
naive_te = y_orig[mask_te].values

# Baseline training history for true MASE
scale_train = np.mean(np.abs(y_lvl[mask_tr].values[48:] - y_lvl[mask_tr].values[:-48]))

mae_lvl_leafy = np.mean(np.abs(y_te_true[is_leafy_te] - p_lvl_te[is_leafy_te]))
mae_rat_leafy = np.mean(np.abs(y_te_true[is_leafy_te] - p_rat_te[is_leafy_te]))
mae_naive_leafy = np.mean(np.abs(y_te_true[is_leafy_te] - naive_te[is_leafy_te]))

print(f"\nLeafy Greens Test Evaluation (h=4):")
print(f"  Level Lasso MAE: {mae_lvl_leafy:.2f} Rs (Skill vs Naive: {(1 - mae_lvl_leafy/mae_naive_leafy)*100:+.2f}%)")
print(f"  Ratio Lasso MAE: {mae_rat_leafy:.2f} Rs (Skill vs Naive: {(1 - mae_rat_leafy/mae_naive_leafy)*100:+.2f}%)")
print(f"  Naive MAE:       {mae_naive_leafy:.2f} Rs")
print(f"  Level MASE (normalized to naive): {mae_lvl_leafy/mae_naive_leafy:.4f}")
print(f"  Ratio MASE (normalized to naive): {mae_rat_leafy/mae_naive_leafy:.4f}")
