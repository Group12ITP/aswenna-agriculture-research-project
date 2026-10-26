import pandas as pd
import numpy as np
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.models.baselines import NaiveForecaster
from src.metrics import compute_mase, evaluate_predictions

cfg = load_config("config.yaml")
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)

for h in [1, 4, 8, 12]:
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
    target_col = f"target_h{h}"
    target_week = df_feat["week_index"] + h
    max_allowed = 417 - h
    refit_mask = train_mask | (val_mask & (target_week <= max_allowed))
    unpurged_refit_mask = train_mask | val_mask
    
    # Generate Naive predictions exactly as in run_purged_test_pipeline.py
    test_preds_list = []
    for veg in df_feat["product_name"].unique():
        v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
        train_prices = v_df.loc[train_mask.loc[v_df.index], "price_lkr"].values
        model = NaiveForecaster()
        model.fit(train_prices)
        for idx in v_df.index[test_mask.loc[v_df.index]]:
            curr_w = v_df.loc[idx, "week_index"]
            hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
            test_preds_list.append((idx, model.predict(horizon=h, y_history=hist)))
            
    naive_test_p = pd.Series({idx: p for idx, p in test_preds_list}, name="pred_naive")
    y_test_true = df_feat.loc[test_mask, target_col]
    
    # Evaluate with unpurged train history (weeks 1 to 416)
    m_unp = evaluate_predictions(y_test_true, naive_test_p, y_train_history=df_feat.loc[unpurged_refit_mask, "price_lkr"])
    # Evaluate with purged train history (weeks 1 to 417-h)
    m_pur = evaluate_predictions(y_test_true, naive_test_p, y_train_history=df_feat.loc[refit_mask, "price_lkr"])
    
    print(f"Horizon h={h}:")
    print(f"  Unpurged history: MAE={m_unp['MAE']:.4f}, MASE={m_unp['MASE']:.4f}, scale={m_unp['MAE']/m_unp['MASE']:.4f}")
    print(f"  Purged history:   MAE={m_pur['MAE']:.4f}, MASE={m_pur['MASE']:.4f}, scale={m_pur['MAE']/m_pur['MASE']:.4f}")
