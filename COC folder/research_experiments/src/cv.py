"""
cv.py - Cross-validation splitters (LOSO and Forward-Chaining) for IT4010 COC.
"""

from typing import List, Tuple, Dict, Any
import numpy as np
import pandas as pd


def get_loso_splits(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """
    Generates Leave-One-Season-Year-Out (LOSO) splits.
    For each unique Year_Start, records in that year are held out as test,
    and all other years serve as training.
    """
    years = sorted(df["Year_Start"].unique())
    splits = []

    for year in years:
        train_idx = df[df["Year_Start"] != year].index.to_numpy()
        test_idx = df[df["Year_Start"] == year].index.to_numpy()
        splits.append({
            "fold_name": f"LOSO_{year}",
            "held_out_year": int(year),
            "train_idx": train_idx,
            "test_idx": test_idx,
            "train_size": len(train_idx),
            "test_size": len(test_idx)
        })

    return splits


def get_forward_chaining_splits(df: pd.DataFrame, horizons: List[int] = None) -> List[Dict[str, Any]]:
    """
    Generates Forward-Chaining (Rolling-Origin) splits.
    Train on years < T, test on year T.
    Default horizons: [2022, 2023, 2024, 2025].
    """
    if horizons is None:
        horizons = [2022, 2023, 2024, 2025]

    splits = []
    for test_year in horizons:
        train_idx = df[df["Year_Start"] < test_year].index.to_numpy()
        test_idx = df[df["Year_Start"] == test_year].index.to_numpy()
        if len(train_idx) == 0 or len(test_idx) == 0:
            continue
        splits.append({
            "fold_name": f"FC_{test_year}",
            "test_year": int(test_year),
            "train_idx": train_idx,
            "test_idx": test_idx,
            "train_size": len(train_idx),
            "test_size": len(test_idx)
        })

    return splits


def get_inner_temporal_split(df_train: pd.DataFrame, val_ratio: float = 0.15) -> Tuple[np.ndarray, np.ndarray]:
    """
    Splits the training fold temporally for early stopping or hyperparameter validation.
    Holds out the latest season_order_keys as validation.
    """
    sorted_df = df_train.sort_values(by="season_order_key")
    n_val = max(1, int(len(sorted_df) * val_ratio))
    val_indices = sorted_df.iloc[-n_val:].index.to_numpy()
    train_indices = sorted_df.iloc[:-n_val].index.to_numpy()
    return train_indices, val_indices
