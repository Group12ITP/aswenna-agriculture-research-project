"""
statistical_tests.py - Hypothesis testing, Diebold-Mariano, bootstrap CIs, and multiplicity correction.
"""

from typing import Tuple, List, Dict
import numpy as np
import pandas as pd
from scipy import stats


def paired_wilcoxon_test(errors_model: np.ndarray, errors_champion: np.ndarray) -> Dict[str, float]:
    """
    Performs Wilcoxon signed-rank test on absolute errors:
    H0: Median absolute error difference == 0
    H1: Two-sided difference
    """
    abs_diff = np.abs(errors_model) - np.abs(errors_champion)
    # Exclude exact zeros
    non_zero = abs_diff[abs_diff != 0]
    if len(non_zero) < 10:
        return {"statistic": np.nan, "p_value": 1.0, "mean_diff": float(np.mean(abs_diff))}

    res = stats.wilcoxon(abs_diff, alternative="two-sided")
    return {
        "statistic": float(res.statistic),
        "p_value": float(res.pvalue),
        "mean_diff": float(np.mean(abs_diff))
    }


def diebold_mariano_test(errors_model: np.ndarray, errors_benchmark: np.ndarray, h: int = 1) -> Dict[str, float]:
    """
    Computes Diebold-Mariano test statistic for forecast accuracy comparison.
    h: forecast horizon (default 1)
    """
    d = (errors_model ** 2) - (errors_benchmark ** 2)
    n = len(d)
    if n < 5:
        return {"dm_stat": np.nan, "p_value": 1.0}

    mean_d = np.mean(d)
    # Autocovariance
    gamma_0 = np.var(d, ddof=0)
    gamma_sum = 0.0
    for lag in range(1, h):
        if lag < n:
            gamma = np.mean((d[lag:] - mean_d) * (d[:-lag] - mean_d))
            gamma_sum += 2.0 * gamma

    v_d = (gamma_0 + gamma_sum) / n
    if v_d <= 0:
        dm_stat = 0.0
    else:
        dm_stat = mean_d / np.sqrt(v_d)

    p_value = 2.0 * (1.0 - stats.norm.cdf(np.abs(dm_stat)))
    return {"dm_stat": float(dm_stat), "p_value": float(p_value)}


def bootstrap_mae_ci(y_true: np.ndarray, y_pred: np.ndarray, n_boot: int = 1000, alpha: float = 0.05, seed: int = 42) -> Tuple[float, float, float]:
    """Computes non-parametric bootstrap 95% confidence intervals for MAE."""
    rng = np.random.default_rng(seed)
    n = len(y_true)
    abs_errors = np.abs(y_true - y_pred)
    boot_maes = []

    for _ in range(n_boot):
        sample_errs = rng.choice(abs_errors, size=n, replace=True)
        boot_maes.append(np.mean(sample_errs))

    point_est = float(np.mean(abs_errors))
    lower = float(np.percentile(boot_maes, 100.0 * (alpha / 2.0)))
    upper = float(np.percentile(boot_maes, 100.0 * (1.0 - alpha / 2.0)))
    return point_est, lower, upper


def apply_holm_bonferroni(p_values: List[float]) -> List[float]:
    """Applies Holm-Bonferroni step-down correction to control FWER."""
    n = len(p_values)
    indexed_p = sorted(enumerate(p_values), key=lambda x: x[1])
    corrected = [0.0] * n

    running_max = 0.0
    for rank, (orig_idx, p) in enumerate(indexed_p):
        multiplier = n - rank
        adj_p = min(1.0, p * multiplier)
        running_max = max(running_max, adj_p)
        corrected[orig_idx] = running_max

    return corrected
