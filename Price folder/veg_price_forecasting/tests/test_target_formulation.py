import numpy as np
import pandas as pd
from sklearn.linear_model import Lasso, Ridge, ElasticNet
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import lightgbm as lgb

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.train import prepare_feature_matrices
from src.metrics import evaluate_predictions, compute_skill_vs_naive

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)

for h in [1, 4]:
    target_col = f"target_h{h}"
    X, y, feature_cols = prepare_feature_matrices(df_feat, target_col=target_col)
    
    y_origin_tr = df_feat.loc[train_mask, "price_lkr"]
    y_origin_vl = df_feat.loc[val_mask, "price_lkr"]
    y_origin_te = df_feat.loc[test_mask, "price_lkr"]
    
    y_tr_true = y[train_mask]
    y_vl_true = y[val_mask]
    y_te_true = y[test_mask]
    
    # Ratios
    r_tr = np.log(np.clip(y_tr_true / y_origin_tr.clip(lower=1.0), 1e-4, None))
    r_vl = np.log(np.clip(y_vl_true / y_origin_vl.clip(lower=1.0), 1e-4, None))
    r_te = np.log(np.clip(y_te_true / y_origin_te.clip(lower=1.0), 1e-4, None))
    
    valid_tr = pd.notna(y_tr_true) & pd.notna(r_tr)
    valid_vl = pd.notna(y_vl_true) & pd.notna(r_vl)
    
    # 1. Level Lasso vs Log-Ratio Lasso
    lasso_lvl = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.1, random_state=42, max_iter=2000))])
    lasso_lvl.fit(X[train_mask][valid_tr], y_tr_true[valid_tr])
    p_lvl = pd.Series(lasso_lvl.predict(X[val_mask]), index=y_vl_true.index)
    m_lvl = evaluate_predictions(y_vl_true, p_lvl, y_train_history=df_feat.loc[train_mask, "price_lkr"])
    
    lasso_rat = Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=0.01, random_state=42, max_iter=2000))])
    lasso_rat.fit(X[train_mask][valid_tr], r_tr[valid_tr])
    p_rat = pd.Series(y_origin_vl * np.exp(lasso_rat.predict(X[val_mask])), index=y_vl_true.index)
    m_rat = evaluate_predictions(y_vl_true, p_rat, y_train_history=df_feat.loc[train_mask, "price_lkr"])
    
    # 2. Level LightGBM vs Log-Ratio LightGBM
    lgb_lvl = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
    lgb_lvl.fit(X[train_mask][valid_tr], y_tr_true[valid_tr])
    p_lgb_lvl = pd.Series(lgb_lvl.predict(X[val_mask]), index=y_vl_true.index)
    m_lgb_lvl = evaluate_predictions(y_vl_true, p_lgb_lvl, y_train_history=df_feat.loc[train_mask, "price_lkr"])
    
    lgb_rat = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, num_leaves=31, random_state=42, verbose=-1, n_jobs=-1)
    lgb_rat.fit(X[train_mask][valid_tr], r_tr[valid_tr])
    p_lgb_rat = pd.Series(y_origin_vl * np.exp(lgb_rat.predict(X[val_mask])), index=y_vl_true.index)
    m_lgb_rat = evaluate_predictions(y_vl_true, p_lgb_rat, y_train_history=df_feat.loc[train_mask, "price_lkr"])
    
    print(f"\n--- HORIZON h={h} ---")
    print(f"Lasso Level:     MAE={m_lvl['MAE']:.2f}, MASE={m_lvl['MASE']:.4f}, sMAPE={m_lvl['sMAPE']:.2f}%")
    print(f"Lasso Log-Ratio: MAE={m_rat['MAE']:.2f}, MASE={m_rat['MASE']:.4f}, sMAPE={m_rat['sMAPE']:.2f}%")
    print(f"LGBM Level:      MAE={m_lgb_lvl['MAE']:.2f}, MASE={m_lgb_lvl['MASE']:.4f}, sMAPE={m_lgb_lvl['sMAPE']:.2f}%")
    print(f"LGBM Log-Ratio:  MAE={m_lgb_rat['MAE']:.2f}, MASE={m_lgb_rat['MASE']:.4f}, sMAPE={m_lgb_rat['sMAPE']:.2f}%")
