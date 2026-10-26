import pandas as pd
import numpy as np
import yaml

with open("config.yaml", "r") as f:
    cfg = yaml.safe_load(f)

# Load master long
df_long = pd.read_csv("data/raw/vegetables_long.csv")
print(f"Total rows in df_long: {len(df_long)}")
print(f"Week index min: {df_long['week_index'].min()}, max: {df_long['week_index'].max()}")

# Look at config splits
print("Config splits:", cfg["splits"])

train_end = cfg["splits"]["train_end_date"]
val_start = cfg["splits"]["val_start_date"]
val_end = cfg["splits"]["val_end_date"]
test_start = cfg["splits"]["test_start_date"]
test_end = cfg["splits"]["test_end_date"]

# Dates to week_index mapping
dates_df = df_long[["week_index", "approx_date"]].drop_duplicates().sort_values("week_index")
print("\nKey date boundaries in data:")
for name, d in [("train_end", train_end), ("val_start", val_start), ("val_end", val_end), ("test_start", test_start), ("test_end", test_end)]:
    match = dates_df[dates_df["approx_date"] == d]
    if len(match):
        print(f"  {name}: {d} -> week_index {match['week_index'].values[0]}")
    else:
        closest = dates_df[dates_df["approx_date"] <= d]
        print(f"  {name}: {d} -> not exact, closest <= is {closest.iloc[-1]['approx_date']} (week {closest.iloc[-1]['week_index']})")

# Let's inspect how train_mask, val_mask, test_mask were defined on origin date
dates = df_long["approx_date"]
train_mask = (dates <= train_end)
val_mask = (dates >= val_start) & (dates <= val_end)
test_mask = (dates >= test_start) & (dates <= test_end)

print(f"\nCurrent origin splits by approx_date:")
print(f"  Train: origin weeks {df_long.loc[train_mask, 'week_index'].min()} to {df_long.loc[train_mask, 'week_index'].max()}")
print(f"  Val:   origin weeks {df_long.loc[val_mask, 'week_index'].min()} to {df_long.loc[val_mask, 'week_index'].max()}")
print(f"  Test:  origin weeks {df_long.loc[test_mask, 'week_index'].min()} to {df_long.loc[test_mask, 'week_index'].max()}")

# Now for each horizon h in [1, 4, 8, 12]:
# If split is defined by origin week t:
# Target week is t + h!
print("\n--- CURRENT SPLIT (by ORIGIN week) ---")
for h in [1, 4, 8, 12]:
    print(f"Horizon h={h}:")
    t_train_orig_min, t_train_orig_max = df_long.loc[train_mask, 'week_index'].min(), df_long.loc[train_mask, 'week_index'].max()
    t_val_orig_min, t_val_orig_max = df_long.loc[val_mask, 'week_index'].min(), df_long.loc[val_mask, 'week_index'].max()
    t_test_orig_min, t_test_orig_max = df_long.loc[test_mask, 'week_index'].min(), df_long.loc[test_mask, 'week_index'].max()
    
    t_train_tgt_min, t_train_tgt_max = t_train_orig_min + h, t_train_orig_max + h
    t_val_tgt_min, t_val_tgt_max = t_val_orig_min + h, t_val_orig_max + h
    t_test_tgt_min, t_test_tgt_max = t_test_orig_min + h, t_test_orig_max + h
    
    print(f"  Train: origin [{t_train_orig_min}, {t_train_orig_max}], target [{t_train_tgt_min}, {t_train_tgt_max}]")
    print(f"  Val:   origin [{t_val_orig_min}, {t_val_orig_max}], target [{t_val_tgt_min}, {t_val_tgt_max}]")
    print(f"  Test:  origin [{t_test_orig_min}, {t_test_orig_max}], target [{t_test_tgt_min}, {t_test_tgt_max}]")
    print(f"  Train max target ({t_train_tgt_max}) vs Val min target ({t_val_tgt_min}) -> diff = {t_val_tgt_min - t_train_tgt_max}")
    print(f"  Train max target ({t_train_tgt_max}) vs Val min origin ({t_val_orig_min}) -> diff = {t_val_orig_min - t_train_tgt_max}")
    print(f"  Val max target ({t_val_tgt_max}) vs Test min target ({t_test_tgt_min}) -> diff = {t_test_tgt_min - t_val_tgt_max}")
    print(f"  Val max target ({t_val_tgt_max}) vs Test min origin ({t_test_orig_min}) -> diff = {t_test_orig_min - t_val_tgt_max}")
