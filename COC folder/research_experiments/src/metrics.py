"""
metrics.py - Evaluation metrics across LKR and log scales, economic regimes, and crops.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score


def compute_core_metrics(y_true: np.ndarray, y_pred: np.ndarray, coverage: float = 1.0) -> Dict[str, float]:
    """
    Computes all standard regression metrics on original scale and log scale.
    Guards against negative or zero predictions.
    """
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)

    # Clean clipped predictions
    y_pred_clipped = np.clip(y_pred, a_min=1.0, a_max=None)

    # Original Scale Metrics
    mae = float(mean_absolute_error(y_true, y_pred_clipped))
    rmse = float(root_mean_squared_error(y_true, y_pred_clipped))
    r2 = float(r2_score(y_true, y_pred_clipped))

    # Percentage Metrics
    abs_pct_errors = np.abs((y_true - y_pred_clipped) / np.clip(y_true, 1.0, None)) * 100.0
    mape = float(np.mean(abs_pct_errors))
    mdape = float(np.median(abs_pct_errors))

    # Symmetric MAPE
    smape_denom = (np.abs(y_true) + np.abs(y_pred_clipped)) / 2.0
    smape = float(np.mean(np.abs(y_true - y_pred_clipped) / np.clip(smape_denom, 1.0, None)) * 100.0)

    # Log-scale Metrics
    y_true_log = np.log1p(y_true)
    y_pred_log = np.log1p(y_pred_clipped)
    log_rmse = float(root_mean_squared_error(y_true_log, y_pred_log))
    log_mae = float(mean_absolute_error(y_true_log, y_pred_log))

    return {
        "MAE": round(mae, 2),
        "RMSE": round(rmse, 2),
        "MAPE": round(mape, 2),
        "sMAPE": round(smape, 2),
        "MdAPE": round(mdape, 2),
        "R2": round(r2, 4),
        "Log_RMSE": round(log_rmse, 4),
        "Log_MAE": round(log_mae, 4),
        "Coverage": round(coverage, 4)
    }


def compute_regime_metrics(df_eval: pd.DataFrame, pred_col: str = "predicted", true_col: str = "actual") -> Dict[str, Dict[str, float]]:
    """Computes metrics stratified by economic regimes (Stable, Crisis, Post-Crisis)."""
    regimes = ["Stable", "Crisis", "Post-Crisis"]
    results = {}
    for r in regimes:
        sub = df_eval[df_eval["economic_regime"] == r]
        if len(sub) > 0:
            results[r] = compute_core_metrics(sub[true_col].values, sub[pred_col].values)
        else:
            results[r] = {m: np.nan for m in ["MAE", "RMSE", "MAPE", "sMAPE", "MdAPE", "R2", "Log_RMSE"]}
    return results


def compute_top_crop_metrics(df_eval: pd.DataFrame, pred_col: str = "predicted", true_col: str = "actual", top_crops: List[str] = None) -> Dict[str, Dict[str, float]]:
    """Computes metrics for top individual crops."""
    if top_crops is None:
        top_crops = ["Paddy", "Big Onion", "Potato", "Chilli", "Maize"]

    results = {}
    for crop in top_crops:
        sub = df_eval[df_eval["Crop"] == crop]
        if len(sub) > 0:
            results[crop] = compute_core_metrics(sub[true_col].values, sub[pred_col].values)
        else:
            results[crop] = {m: np.nan for m in ["MAE", "RMSE", "MAPE", "sMAPE", "MdAPE", "R2", "Log_RMSE"]}
    return results


def compute_per_year_metrics(df_eval: pd.DataFrame, pred_col: str = "predicted", true_col: str = "actual") -> pd.DataFrame:
    """Computes metrics year by year."""
    records = []
    for year, grp in df_eval.groupby("Year_Start"):
        m = compute_core_metrics(grp[true_col].values, grp[pred_col].values)
        m["Year_Start"] = int(year)
        m["Test_Rows"] = len(grp)
        records.append(m)
    return pd.DataFrame(records).sort_values(by="Year_Start").reset_index(drop=True)
