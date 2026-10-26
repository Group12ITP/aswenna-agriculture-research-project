import pandas as pd
import numpy as np

raw_df = pd.read_csv("data/raw/vegetables_long.csv")

def old_compute_stale(series, threshold=4):
    is_stale = np.zeros(len(series), dtype=bool)
    values = series.values
    n = len(values)
    i = 0
    while i < n:
        if pd.isna(values[i]):
            i += 1
            continue
        j = i + 1
        while j < n and pd.notna(values[j]) and values[j] == values[i]:
            j += 1
        run_len = j - i
        if run_len >= threshold:
            is_stale[i:j] = True
        i = j
    return pd.Series(is_stale, index=series.index)

def causal_compute_stale(series, threshold=4):
    is_stale = np.zeros(len(series), dtype=bool)
    values = series.values
    n = len(values)
    current_run = 0
    prev_val = None
    for i in range(n):
        val = values[i]
        if pd.isna(val):
            current_run = 0
            prev_val = None
        else:
            if prev_val is not None and val == prev_val:
                current_run += 1
            else:
                current_run = 1
                prev_val = val
        if current_run >= threshold:
            is_stale[i] = True
    return pd.Series(is_stale, index=series.index)

diffs = 0
diffs_test = 0
for veg, grp in raw_df.groupby("product_name"):
    s = grp["price_lkr"]
    old_res = old_compute_stale(s)
    causal_res = causal_compute_stale(s)
    diff_mask = old_res != causal_res
    diffs += diff_mask.sum()
    test_mask = (grp["approx_date"] >= "2025-09-04") & (grp["approx_date"] <= "2026-08-25")
    diffs_test += (diff_mask & test_mask).sum()

print("Total stale run differences across full dataset:", diffs)
print("Total stale run differences on TEST split:", diffs_test)
