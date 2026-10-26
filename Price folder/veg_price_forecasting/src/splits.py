import logging
import numpy as np
import pandas as pd
from .utils import load_config, get_logger

logger = get_logger("src.splits")

def get_split_masks(df, cfg=None, horizon=None):
    """
    Generate boolean masks for chronological Train, Validation, and Test splits.
    If horizon is specified, splits are strictly defined by TARGET week to eliminate lookahead:
      - Train targets end >= h weeks before first val target: target_week <= 369 - horizon
      - Validation targets: weeks 369 to 416 (2024-09-04 to 2025-08-25, 48 weeks)
      - Test targets: weeks 417 to 464 (2025-09-04 to 2026-08-25, 48 weeks)
      - Guarantees val targets end strictly before test targets (416 < 417).
    If horizon is None, falls back to origin date boundaries.
    """
    if cfg is None:
        cfg = load_config()
        
    if horizon is not None:
        target_week = df["week_index"] + horizon
        train_mask = (target_week <= (369 - horizon))
        val_mask = (target_week >= 369) & (target_week <= 416)
        test_mask = (target_week >= 417) & (target_week <= 464)
        return train_mask, val_mask, test_mask
        
    train_end = cfg["splits"]["train_end_date"]
    val_start = cfg["splits"]["val_start_date"]
    val_end = cfg["splits"]["val_end_date"]
    test_start = cfg["splits"]["test_start_date"]
    test_end = cfg["splits"]["test_end_date"]
    
    dates = df["approx_date"]
    train_mask = (dates <= train_end)
    val_mask = (dates >= val_start) & (dates <= val_end)
    test_mask = (dates >= test_start) & (dates <= test_end)
    
    return train_mask, val_mask, test_mask

class ExpandingWindowCV:
    """
    Expanding-window walk-forward time-series cross-validator with a purge gap >= horizon.
    Guarantees no future leakage between train and fold validation.
    """
    def __init__(self, initial_train_weeks=192, step_weeks=44, gap_weeks=12, val_weeks=24):
        self.initial_train_weeks = initial_train_weeks
        self.step_weeks = step_weeks
        self.gap_weeks = gap_weeks
        self.val_weeks = val_weeks
        
    def split(self, df_train_period, horizon=4):
        """
        Yields (train_indices, val_indices) over unique sorted week_indices.
        Gap is enforced as max(self.gap_weeks, horizon).
        """
        unique_weeks = np.sort(df_train_period["week_index"].unique())
        total_weeks = len(unique_weeks)
        effective_gap = max(self.gap_weeks, horizon)
        
        start_val = self.initial_train_weeks + effective_gap
        while start_val + self.val_weeks <= total_weeks:
            val_weeks_slice = unique_weeks[start_val : start_val + self.val_weeks]
            train_weeks_slice = unique_weeks[: start_val - effective_gap]
            
            train_idx = df_train_period[df_train_period["week_index"].isin(train_weeks_slice)].index.values
            val_idx = df_train_period[df_train_period["week_index"].isin(val_weeks_slice)].index.values
            
            yield train_idx, val_idx
            start_val += self.step_weeks
