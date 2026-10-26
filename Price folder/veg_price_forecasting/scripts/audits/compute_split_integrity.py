import pandas as pd
import numpy as np
from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks

cfg = load_config()
df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)

rows = []
for h in [1, 4, 8, 12]:
    target_col = f"target_h{h}"
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg, horizon=h)
    
    # Non-null targets only
    tr = df_feat[train_mask & df_feat[target_col].notna()]
    va = df_feat[val_mask & df_feat[target_col].notna()]
    te = df_feat[test_mask & df_feat[target_col].notna()]
    
    tr_orig_min, tr_orig_max = int(tr["week_index"].min()), int(tr["week_index"].max())
    tr_tgt_min, tr_tgt_max = int((tr["week_index"] + h).min()), int((tr["week_index"] + h).max())
    
    va_orig_min, va_orig_max = int(va["week_index"].min()), int(va["week_index"].max())
    va_tgt_min, va_tgt_max = int((va["week_index"] + h).min()), int((va["week_index"] + h).max())
    
    te_orig_min, te_orig_max = int(te["week_index"].min()), int(te["week_index"].max())
    te_tgt_min, te_tgt_max = int((te["week_index"] + h).min()), int((te["week_index"] + h).max())
    
    # Purge gap: between train max target and val min target
    purge_gap_tr_va = va_tgt_min - tr_tgt_max
    # Purge gap: between val max target and test min target
    purge_gap_va_te = te_tgt_min - va_tgt_max
    
    rows.append({
        "horizon": h,
        "split": "Train",
        "n_obs": len(tr),
        "min_origin_week": tr_orig_min,
        "max_origin_week": tr_orig_max,
        "min_target_week": tr_tgt_min,
        "max_target_week": tr_tgt_max,
        "purge_gap_to_next": f"{purge_gap_tr_va} wks (>= h={h})"
    })
    rows.append({
        "horizon": h,
        "split": "Validation",
        "n_obs": len(va),
        "min_origin_week": va_orig_min,
        "max_origin_week": va_orig_max,
        "min_target_week": va_tgt_min,
        "max_target_week": va_tgt_max,
        "purge_gap_to_next": f"{purge_gap_va_te} wk (target disjoint)"
    })
    rows.append({
        "horizon": h,
        "split": "Test",
        "n_obs": len(te),
        "min_origin_week": te_orig_min,
        "max_origin_week": te_orig_max,
        "min_target_week": te_tgt_min,
        "max_target_week": te_tgt_max,
        "purge_gap_to_next": "N/A (terminal split)"
    })

df_split = pd.DataFrame(rows)
df_split.to_csv("results/tables/split_integrity_summary.csv", index=False)
print("SPLIT INTEGRITY TABLE:")
print(df_split.to_string(index=False))
