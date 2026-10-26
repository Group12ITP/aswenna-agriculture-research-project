import json
import logging
from pathlib import Path
import numpy as np
import pandas as pd

from .utils import load_config, compute_file_hash, get_logger

logger = get_logger("src.data")

GLOBAL_MISSING_WEEKS = [
    (2019, 4, 3), (2019, 4, 4), (2020, 8, 1),
    (2021, 4, 2), (2022, 4, 2), (2022, 5, 2), (2023, 4, 2)
]

def verify_raw_data_integrity(data_raw_dir):
    """Verify raw files against SHA-256 hashes in hashes.json."""
    raw_path = Path(data_raw_dir)
    hash_file = raw_path / "hashes.json"
    if not hash_file.exists():
        logger.warning(f"No hashes.json found in {data_raw_dir}. Skipping hash verification.")
        return True
    with open(hash_file, "r", encoding="utf-8") as f:
        expected = json.load(f)
    for fname, meta in expected.items():
        fpath = raw_path / fname
        if not fpath.exists():
            raise FileNotFoundError(f"Expected raw file {fname} not found in {data_raw_dir}")
        curr_hash = compute_file_hash(fpath)
        if curr_hash != meta["sha256"]:
            raise ValueError(f"Integrity check failed for {fname}! Expected {meta['sha256']}, got {curr_hash}")
    logger.info("Raw data SHA-256 integrity check verified successfully.")
    return True

def compute_stale_runs(series, threshold=4):
    """
    Flag consecutive runs of identical non-null values with length >= threshold causally.
    At index t, is_stale is True if and only if the backward streak of identical
    non-null values up to and including t is >= threshold.
    Never uses forward or centered windows.
    """
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

def load_and_preprocess_vegetables(cfg=None):
    """
    Load raw vegetable datasets, apply spelling fixes, construct stale flags,
    and prepare standardized long and wide dataframes.
    """
    if cfg is None:
        cfg = load_config()
        
    raw_dir = Path(cfg["paths"]["data_raw"])
    verify_raw_data_integrity(raw_dir)
    
    wide_path = raw_dir / "vegetables_wide.csv"
    long_path = raw_dir / "vegetables_long.csv"
    
    df_wide = pd.read_csv(wide_path)
    df_long = pd.read_csv(long_path)
    
    spelling_fixes = cfg.get("spelling_fixes", {})
    
    # Apply spelling fixes to column headers in wide format
    new_cols = {col: spelling_fixes.get(col, col) for col in df_wide.columns}
    df_wide = df_wide.rename(columns=new_cols)
    
    # Apply spelling fixes to product_name in long format
    df_long["product_name"] = df_long["product_name"].replace(spelling_fixes)
    
    # Sort chronologically
    df_wide = df_wide.sort_values("week_index").reset_index(drop=True)
    df_long = df_long.sort_values(["product_name", "week_index"]).reset_index(drop=True)
    
    # Compute is_stale_run per vegetable
    stale_threshold = cfg["features"].get("stale_run_threshold_weeks", 4)
    stale_flags = {}
    for veg, group in df_long.groupby("product_name"):
        stale_s = compute_stale_runs(group["price_lkr"], threshold=stale_threshold)
        stale_flags[veg] = stale_s.values
        
    df_long["is_stale_run"] = False
    for veg in df_long["product_name"].unique():
        mask = df_long["product_name"] == veg
        df_long.loc[mask, "is_stale_run"] = stale_flags[veg]
        
    logger.info(f"Loaded {len(df_wide)} weeks and {len(df_long)} long records for {len(df_long['product_name'].unique())} vegetables.")
    return df_wide, df_long
