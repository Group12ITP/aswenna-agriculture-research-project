import pandas as pd
import numpy as np
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks
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
    
    y_test_true = df_feat.loc[test_mask, target_col].values
    naive_pred = df_feat.loc[test_mask, "price_lkr"].values
    
    # Check valid test rows
    valid_test = pd.notna(y_test_true)
    y_test_clean = y_test_true[valid_test]
    naive_clean = naive_pred[valid_test]
    
    mae = np.mean(np.abs(y_test_clean - naive_clean))
    
    mase_unpurged = compute_mase(y_test_clean, naive_clean, df_feat.loc[unpurged_refit_mask, "price_lkr"])
    mase_purged = compute_mase(y_test_clean, naive_clean, df_feat.loc[refit_mask, "price_lkr"])
    
    scale_unp = mae / mase_unpurged
    scale_pur = mae / mase_purged
    
    print(f"Horizon h={h} (N={len(y_test_clean)}):")
    print(f"  Naive Test MAE: {mae:.4f}")
    print(f"  Unpurged (train+val to wk 416): scale={scale_unp:.4f}, MASE={mase_unpurged:.4f}")
    print(f"  Purged (train+val to wk {max_allowed}):   scale={scale_pur:.4f}, MASE={mase_purged:.4f}")
