import pandas as pd
import numpy as np
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.train import prepare_feature_matrices
from src.models.classical import get_classical_model
from src.models.statistical import AutoARIMARollingForecaster
from src.models.baselines import NaiveForecaster
from src.metrics import evaluate_predictions

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
h = 4
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
target_col = f"target_h{h}"

is_leafy_test = test_mask & (df_feat["category"] == "leafy vegetables")
y_true_leafy = df_feat.loc[is_leafy_test, target_col].values
y_hist = df_feat.loc[train_mask | val_mask, "price_lkr"]

# Fit Lasso on train | val in raw_level mode
X, y_raw, _ = prepare_feature_matrices(df_feat, target_col=target_col)
fit_mask = (train_mask | val_mask) & pd.notna(y_raw)
m_lasso_raw = get_classical_model("lasso")
m_lasso_raw.fit(X[fit_mask], y_raw[fit_mask])
pred_lasso_raw_leafy = m_lasso_raw.predict(X[is_leafy_test])

# Fit Lasso in log_ratio mode
# Delta = log(y_{t+h} / y_t)
y_ratio = np.log(df_feat[target_col] / df_feat["price_lkr"])
fit_mask_ratio = (train_mask | val_mask) & pd.notna(y_ratio) & np.isfinite(y_ratio)
m_lasso_ratio = get_classical_model("lasso")
m_lasso_ratio.fit(X[fit_mask_ratio], y_ratio[fit_mask_ratio])
pred_ratio = m_lasso_ratio.predict(X[is_leafy_test])
orig_price_leafy = df_feat.loc[is_leafy_test, "price_lkr"].values
pred_lasso_ratio_leafy = orig_price_leafy * np.exp(pred_ratio)

# Naive
naive_pred_leafy = orig_price_leafy

print("LEAFY GREENS TEST EVALUATION (h=4, N=384):")
mets_naive = evaluate_predictions(y_true_leafy, naive_pred_leafy, y_train_history=y_hist)
print(f"Naive: MAE={mets_naive['MAE']:.2f}, sMAPE={mets_naive['sMAPE']:.2f}%, R2={mets_naive['R2']:.4f}, MASE={mets_naive['MASE']:.4f}")

mets_raw = evaluate_predictions(y_true_leafy, pred_lasso_raw_leafy, y_train_history=y_hist)
print(f"Lasso (raw_level): MAE={mets_raw['MAE']:.2f}, sMAPE={mets_raw['sMAPE']:.2f}%, R2={mets_raw['R2']:.4f}, MASE={mets_raw['MASE']:.4f}")

mets_ratio = evaluate_predictions(y_true_leafy, pred_lasso_ratio_leafy, y_train_history=y_hist)
print(f"Lasso (log_ratio): MAE={mets_ratio['MAE']:.2f}, sMAPE={mets_ratio['sMAPE']:.2f}%, R2={mets_ratio['R2']:.4f}, MASE={mets_ratio['MASE']:.4f}")
