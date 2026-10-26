import pandas as pd
import numpy as np
import yaml
import warnings
warnings.filterwarnings('ignore')

from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.metrics import evaluate_predictions, compute_skill_vs_naive

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

_, df_long = load_and_preprocess_vegetables(cfg)
df_feat = build_vegetable_features(df_long, cfg, include_cross_veg=True)

print("="*80)
print("SPLIT INTEGRITY ANALYSIS: DEFINED BY TARGET DATE")
print("="*80)

# Total weeks: 1 to 464
# Test target range: 417 to 464 (48 weeks)
# Val target range: 369 to 416 (48 weeks)
# Train target range: <= 369 - h (ends >= h weeks before first val target)

for h in [1, 4, 8, 12]:
    print(f"\n>>> HORIZON h = {h} <<<")
    target_col = f"target_h{h}"
    target_week = df_feat["week_index"] + h
    
    # Old split (by origin date)
    old_tr_mask = (df_feat["approx_date"] <= "2024-08-25") & df_feat[target_col].notna()
    old_vl_mask = (df_feat["approx_date"] >= "2024-09-04") & (df_feat["approx_date"] <= "2025-08-25") & df_feat[target_col].notna()
    old_te_mask = (df_feat["approx_date"] >= "2025-09-04") & (df_feat["approx_date"] <= "2026-08-25") & df_feat[target_col].notna()
    
    print("--- OLD SPLIT (Origin Date) ---")
    print(f"  Train: origin [{df_feat.loc[old_tr_mask, 'week_index'].min()}, {df_feat.loc[old_tr_mask, 'week_index'].max()}], target [{df_feat.loc[old_tr_mask, 'week_index'].min() + h}, {df_feat.loc[old_tr_mask, 'week_index'].max() + h}], N={old_tr_mask.sum()}")
    print(f"  Val:   origin [{df_feat.loc[old_vl_mask, 'week_index'].min()}, {df_feat.loc[old_vl_mask, 'week_index'].max()}], target [{df_feat.loc[old_vl_mask, 'week_index'].min() + h}, {df_feat.loc[old_vl_mask, 'week_index'].max() + h}], N={old_vl_mask.sum()}")
    print(f"  Test:  origin [{df_feat.loc[old_te_mask, 'week_index'].min()}, {df_feat.loc[old_te_mask, 'week_index'].max()}], target [{df_feat.loc[old_te_mask, 'week_index'].min() + h}, {df_feat.loc[old_te_mask, 'week_index'].max() + h}], N={old_te_mask.sum()}")
    
    # New split (by Target Date)
    # Val targets: [369, 416]
    # Test targets: [417, 464]
    # Train targets: <= 369 - h
    new_tr_mask = (target_week <= (369 - h)) & df_feat[target_col].notna()
    new_vl_mask = (target_week >= 369) & (target_week <= 416) & df_feat[target_col].notna()
    new_te_mask = (target_week >= 417) & (target_week <= 464) & df_feat[target_col].notna()
    
    tr_orig_min, tr_orig_max = df_feat.loc[new_tr_mask, "week_index"].min(), df_feat.loc[new_tr_mask, "week_index"].max()
    tr_tgt_min, tr_tgt_max = (df_feat.loc[new_tr_mask, "week_index"] + h).min(), (df_feat.loc[new_tr_mask, "week_index"] + h).max()
    
    vl_orig_min, vl_orig_max = df_feat.loc[new_vl_mask, "week_index"].min(), df_feat.loc[new_vl_mask, "week_index"].max()
    vl_tgt_min, vl_tgt_max = (df_feat.loc[new_vl_mask, "week_index"] + h).min(), (df_feat.loc[new_vl_mask, "week_index"] + h).max()
    
    te_orig_min, te_orig_max = df_feat.loc[new_te_mask, "week_index"].min(), df_feat.loc[new_te_mask, "week_index"].max()
    te_tgt_min, te_tgt_max = (df_feat.loc[new_te_mask, "week_index"] + h).min(), (df_feat.loc[new_te_mask, "week_index"] + h).max()
    
    print("\n--- NEW SPLIT (Target Date) ---")
    print(f"  Train: origin [{tr_orig_min}, {tr_orig_max}], target [{tr_tgt_min}, {tr_tgt_max}], N={new_tr_mask.sum()}")
    print(f"  Val:   origin [{vl_orig_min}, {vl_orig_max}], target [{vl_tgt_min}, {vl_tgt_max}], N={new_vl_mask.sum()}")
    print(f"  Test:  origin [{te_orig_min}, {te_orig_max}], target [{te_tgt_min}, {te_tgt_max}], N={new_te_mask.sum()}")
    
    print(f"  Verification Check 1: first val target ({vl_tgt_min}) - train max target ({tr_tgt_max}) = {vl_tgt_min - tr_tgt_max} (>= h={h}) -> {vl_tgt_min - tr_tgt_max >= h}")
    print(f"  Verification Check 2: val targets end before first test target? val max target ({vl_tgt_max}) < first test target ({te_tgt_min}) -> {vl_tgt_max < te_tgt_min}")
    print(f"  Verification Check 3: train max target ({tr_tgt_max}) <= val min origin ({vl_orig_min}) -> {tr_tgt_max <= vl_orig_min}")
