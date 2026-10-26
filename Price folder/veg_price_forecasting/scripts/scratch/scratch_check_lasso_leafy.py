import pandas as pd
import numpy as np
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

X, y_raw, _ = prepare_feature_matrices(df_feat, target_col=target_col)
is_leafy_test = test_mask & (df_feat["category"] == "leafy vegetables")
y_true_leafy = df_feat.loc[is_leafy_test, target_col].values
y_hist = df_feat.loc[train_mask | val_mask, "price_lkr"]
fit_mask = (train_mask | val_mask) & pd.notna(y_raw)

# Try alpha=6.20
m_62 = get_classical_model("lasso", params={"alpha": 6.20})
m_62.fit(X[fit_mask], y_raw[fit_mask])
p_62 = m_62.predict(X[is_leafy_test])
mets_62 = evaluate_predictions(y_true_leafy, p_62, y_train_history=y_hist)
print(f"Lasso (raw_level, alpha=6.20): MAE={mets_62['MAE']:.2f}, sMAPE={mets_62['sMAPE']:.2f}%, MASE={mets_62['MASE']:.4f}")

# Try alpha=0.1
m_01 = get_classical_model("lasso", params={"alpha": 0.1})
m_01.fit(X[fit_mask], y_raw[fit_mask])
p_01 = m_01.predict(X[is_leafy_test])
mets_01 = evaluate_predictions(y_true_leafy, p_01, y_train_history=y_hist)
print(f"Lasso (raw_level, alpha=0.10): MAE={mets_01['MAE']:.2f}, sMAPE={mets_01['sMAPE']:.2f}%, MASE={mets_01['MASE']:.4f}")
