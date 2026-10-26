import yaml
import pandas as pd
import numpy as np
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.train import prepare_feature_matrices, tune_classical_model
from src.models.classical import get_classical_model
from src.metrics import evaluate_predictions

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

_, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg)
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg)

h = 4
target_col = f"target_h{h}"
X, y, _ = prepare_feature_matrices(df_feat, target_col=target_col)
X_train, y_train = X[train_mask], y[train_mask]
X_val, y_val = X[val_mask], y[val_mask]

# Optuna tune
best_params = tune_classical_model("lasso", X_train, y_train, horizon=h, n_trials=15)
print(f"Optuna tuned params for level Lasso at h=4: {best_params}")

# Evaluate with tuned alpha
model_tuned = get_classical_model("lasso", params=best_params)
model_tuned.fit(X_train[pd.notna(y_train)], y_train[pd.notna(y_train)])
p_val_tuned = model_tuned.predict(X_val)
m_tuned = evaluate_predictions(y_val, p_val_tuned, y_train_history=df_feat.loc[train_mask, "price_lkr"])
print(f"Validation MASE with tuned params: {m_tuned['MASE']:.4f}, sMAPE: {m_tuned['sMAPE']:.2f}")

# Evaluate with fixed alpha=0.1
model_01 = get_classical_model("lasso", params={"alpha": 0.1})
model_01.fit(X_train[pd.notna(y_train)], y_train[pd.notna(y_train)])
p_val_01 = model_01.predict(X_val)
m_01 = evaluate_predictions(y_val, p_val_01, y_train_history=df_feat.loc[train_mask, "price_lkr"])
print(f"Validation MASE with fixed alpha=0.1: {m_01['MASE']:.4f}, sMAPE: {m_01['sMAPE']:.2f}")
