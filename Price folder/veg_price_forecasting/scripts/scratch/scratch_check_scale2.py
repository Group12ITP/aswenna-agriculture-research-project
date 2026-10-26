import pandas as pd
import numpy as np
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)

for h in [1, 4]:
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
    target_col = f"target_h{h}"
    
    # Check naive prediction in leaderboard
    y_val = df_feat.loc[val_mask, target_col]
    # what is naive? price_lkr
    y_orig = df_feat.loc[val_mask, "price_lkr"]
    
    valid = pd.notna(y_val) & pd.notna(y_orig)
    err = np.abs(y_val[valid] - y_orig[valid])
    print(f"h={h}: mean abs err on val = {err.mean():.4f}, N={valid.sum()}")
