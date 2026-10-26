import pandas as pd
import numpy as np
import yaml
import warnings
warnings.filterwarnings('ignore')
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.splits import get_split_masks

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

df_wide, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)

train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)

print("="*70)
print("CURRENT SPLIT BEHAVIOR (split on origin date):")
print("="*70)

for h in [1, 4, 8, 12]:
    print(f"\n--- Horizon h = {h} ---")
    target_col = f"target_h{h}"
    
    # Non-null targets only
    tr = df_feat[train_mask & df_feat[target_col].notna()]
    va = df_feat[val_mask & df_feat[target_col].notna()]
    te = df_feat[test_mask & df_feat[target_col].notna()]
    
    tr_orig_min, tr_orig_max = tr["week_index"].min(), tr["week_index"].max()
    tr_tgt_min, tr_tgt_max = (tr["week_index"] + h).min(), (tr["week_index"] + h).max()
    
    va_orig_min, va_orig_max = va["week_index"].min(), va["week_index"].max()
    va_tgt_min, va_tgt_max = (va["week_index"] + h).min(), (va["week_index"] + h).max()
    
    te_orig_min, te_orig_max = te["week_index"].min(), te["week_index"].max()
    te_tgt_min, te_tgt_max = (te["week_index"] + h).min(), (te["week_index"] + h).max()
    
    print(f"TRAIN: min(orig)={tr_orig_min}, max(orig)={tr_orig_max} | min(target)={tr_tgt_min}, max(target)={tr_tgt_max}")
    print(f"VAL:   min(orig)={va_orig_min}, max(orig)={va_orig_max} | min(target)={va_tgt_min}, max(target)={va_tgt_max}")
    print(f"TEST:  min(orig)={te_orig_min}, max(orig)={te_orig_max} | min(target)={te_tgt_min}, max(target)={te_tgt_max}")
    
    gap_val_tr_tgt = va_tgt_min - tr_tgt_max
    print(f"Check 1: Train targets end >= h ({h}) weeks before first val target? (first_val_target - train_max_target = {gap_val_tr_tgt}) -> {gap_val_tr_tgt >= h}")
    gap_te_va_tgt = te_tgt_min - va_tgt_max
    print(f"Check 2: Val targets end before first test target? (first_test_target - val_max_target = {gap_te_va_tgt}) -> {gap_te_va_tgt > 0}")
    print(f"Check 3: Overlap between train targets and val origins? train_max_target ({tr_tgt_max}) <= va_orig_min ({va_orig_min}) -> {tr_tgt_max <= va_orig_min}")
    print(f"Check 4: Overlap between val targets and test origins? val_max_target ({va_tgt_max}) <= te_orig_min ({te_orig_min}) -> {va_tgt_max <= te_orig_min}")
