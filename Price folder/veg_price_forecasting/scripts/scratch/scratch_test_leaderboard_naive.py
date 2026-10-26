import pandas as pd
import numpy as np
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
from src.metrics import evaluate_predictions

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)

for h in [1, 4]:
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
    target_col = f"target_h{h}"
    
    y_val_true = df_feat.loc[val_mask, target_col]
    val_preds_list = []
    for veg in df_feat["product_name"].unique():
        v_df = df_feat[df_feat["product_name"] == veg].sort_values("week_index")
        for idx in v_df.index[val_mask.loc[v_df.index]]:
            curr_w = v_df.loc[idx, "week_index"]
            hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
            val_preds_list.append((idx, float(hist[-1])))
    naive_val_p = pd.Series({idx: p for idx, p in val_preds_list})
    
    y_origin_val = df_feat.loc[val_mask, "price_lkr"]
    y_train_hist = df_feat.loc[train_mask, "price_lkr"]
    
    mets = evaluate_predictions(y_val_true, naive_val_p, y_train_history=y_train_hist, y_prev=y_origin_val)
    print(f"h={h}: evaluate_predictions naive: MAE={mets['MAE']}, MASE={mets['MASE']}, N={mets['n_obs']}")
