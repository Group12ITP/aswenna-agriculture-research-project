import logging
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .utils import get_logger

logger = get_logger("src.metrics")

def compute_mape(y_true, y_pred):
    """Mean Absolute Percentage Error (handles zeros by clipping denominator)."""
    denom = np.clip(np.abs(y_true), a_min=1.0, a_max=None)
    return np.mean(np.abs((y_true - y_pred) / denom)) * 100.0

def compute_smape(y_true, y_pred):
    """Symmetric Mean Absolute Percentage Error (0% to 200%)."""
    denom = (np.abs(y_true) + np.abs(y_pred)) / 2.0
    denom = np.clip(denom, a_min=1.0, a_max=None)
    return np.mean(np.abs(y_pred - y_true) / denom) * 100.0

def compute_mase(y_true, y_pred, y_train_history, seasonal_m=48):
    """
    Mean Absolute Scaled Error relative to in-sample seasonal naive baseline.
    If historical span < seasonal_m, falls back to non-seasonal lag-1 naive scale.
    """
    train_clean = pd.Series(y_train_history).dropna().values
    if len(train_clean) > seasonal_m:
        scale = np.mean(np.abs(train_clean[seasonal_m:] - train_clean[:-seasonal_m]))
    elif len(train_clean) > 1:
        scale = np.mean(np.abs(train_clean[1:] - train_clean[:-1]))
    else:
        scale = 1.0
        
    scale = max(scale, 1e-4)
    mae = np.mean(np.abs(y_true - y_pred))
    return float(mae / scale)

def compute_directional_accuracy(y_true, y_pred, y_prev):
    """
    Directional Accuracy: Percentage of times model correctly predicts the sign of price change
    from origin week t (y_prev) to forecast week t+h (y_true).
    """
    true_dir = np.sign(y_true - y_prev)
    pred_dir = np.sign(y_pred - y_prev)
    return float(np.mean(true_dir == pred_dir) * 100.0)

def compute_skill_vs_naive(mase_model, mase_naive):
    """
    Skill score relative to naive baseline: (1 - MASE_model / MASE_naive) * 100%.
    Positive value indicates outperformance over naive persistence.
    """
    if pd.isna(mase_model) or pd.isna(mase_naive) or mase_naive <= 1e-6:
        return np.nan
    return float((1.0 - mase_model / mase_naive) * 100.0)

def evaluate_predictions(y_true, y_pred, y_train_history=None, y_prev=None, seasonal_m=48):
    """
    Compute comprehensive suite of forecast evaluation metrics on valid (observed) rows.
    """
    if isinstance(y_true, pd.Series) and isinstance(y_pred, pd.Series):
        df_eval = pd.DataFrame({"true": y_true, "pred": y_pred})
        if y_prev is not None and isinstance(y_prev, pd.Series):
            df_eval["prev"] = y_prev
        df_eval = df_eval.dropna(subset=["true", "pred"])
        if len(df_eval) == 0:
            return {
                "MAE": np.nan, "RMSE": np.nan, "MAPE": np.nan, "sMAPE": np.nan,
                "MASE": np.nan, "R2": np.nan, "Bias": np.nan, "Directional_Accuracy": np.nan,
                "n_obs": 0
            }
        yt = df_eval["true"].values
        yp = df_eval["pred"].values
        ypr = df_eval["prev"].values if "prev" in df_eval.columns else (np.array(y_prev) if y_prev is not None else None)
    else:
        mask = pd.notna(y_true) & pd.notna(y_pred)
        if mask.sum() == 0:
            return {
                "MAE": np.nan, "RMSE": np.nan, "MAPE": np.nan, "sMAPE": np.nan,
                "MASE": np.nan, "R2": np.nan, "Bias": np.nan, "Directional_Accuracy": np.nan,
                "n_obs": 0
            }
        yt = np.array(y_true)[mask]
        yp = np.array(y_pred)[mask]
        ypr = np.array(y_prev)[mask] if y_prev is not None else None
    
    mae = mean_absolute_error(yt, yp)
    rmse = np.sqrt(mean_squared_error(yt, yp))
    mape = compute_mape(yt, yp)
    smape = compute_smape(yt, yp)
    r2 = r2_score(yt, yp) if len(yt) > 1 else np.nan
    bias = np.mean(yp - yt)
    
    if y_train_history is not None:
        mase = compute_mase(yt, yp, y_train_history, seasonal_m=seasonal_m)
    else:
        mase = np.nan
        
    if ypr is not None:
        da = compute_directional_accuracy(yt, yp, ypr)
    else:
        da = np.nan
        
    return {
        "MAE": round(float(mae), 2),
        "RMSE": round(float(rmse), 2),
        "MAPE": round(float(mape), 2),
        "sMAPE": round(float(smape), 2),
        "MASE": round(float(mase), 4) if pd.notna(mase) else np.nan,
        "R2": round(float(r2), 4) if pd.notna(r2) else np.nan,
        "Bias": round(float(bias), 2),
        "Directional_Accuracy": round(float(da), 2) if pd.notna(da) else np.nan,
        "n_obs": int(len(yt))
    }

def block_bootstrap_mase(y_true, y_pred, y_naive_pred=None, y_winner_pred=None, y_train_history=None, week_indices=None, block_length=4, n_boot=1000, seed=42):
    """
    Moving block bootstrap (block length B weeks) computing 95% CIs for:
      1) Model MASE
      2) Difference to naive (Delta_MASE_naive = MASE_model - MASE_naive)
      3) Difference to winner (Delta_MASE_winner = MASE_model - MASE_winner)
    When week_indices is provided, resampling is performed at the WEEK BLOCK level,
    preserving cross-vegetable contemporaneous correlation.
    """
    rng = np.random.default_rng(seed)
    mask = pd.notna(y_true) & pd.notna(y_pred)
    if y_naive_pred is not None:
        mask = mask & pd.notna(y_naive_pred)
    if y_winner_pred is not None:
        mask = mask & pd.notna(y_winner_pred)
        
    yt = np.array(y_true)[mask]
    yp = np.array(y_pred)[mask]
    yp_naive = np.array(y_naive_pred)[mask] if y_naive_pred is not None else None
    yp_win = np.array(y_winner_pred)[mask] if y_winner_pred is not None else None
    
    n = len(yt)
    if n < 10:
        return {"mase_ci_low": np.nan, "mase_ci_high": np.nan, "diff_naive_ci_low": np.nan, "diff_naive_ci_high": np.nan}
        
    train_clean = pd.Series(y_train_history).dropna().values if y_train_history is not None else np.array([])
    if len(train_clean) > 48:
        scale = max(1e-4, np.mean(np.abs(train_clean[48:] - train_clean[:-48])))
    elif len(train_clean) > 1:
        scale = max(1e-4, np.mean(np.abs(train_clean[1:] - train_clean[:-1])))
    else:
        scale = 1.0

    boot_mases = []
    boot_diff_naives = []
    boot_diff_wins = []

    if week_indices is not None:
        # Week-block bootstrap preserving cross-vegetable correlation
        weeks_arr = np.array(week_indices)[mask]
        unique_weeks = np.sort(np.unique(weeks_arr))
        n_weeks = len(unique_weeks)
        n_week_blocks = int(np.ceil(n_weeks / block_length))
        max_start = max(1, n_weeks - block_length + 1)
        
        # Precompute indices for each week for fast gathering
        week_to_idx = {w: np.where(weeks_arr == w)[0] for w in unique_weeks}

        for _ in range(n_boot):
            starts = rng.integers(0, max_start, size=n_week_blocks)
            sampled_weeks = np.concatenate([unique_weeks[s:s + block_length] for s in starts])[:n_weeks]
            b_indices = np.concatenate([week_to_idx[w] for w in sampled_weeks])
            
            b_yt = yt[b_indices]
            b_yp = yp[b_indices]
            b_mase = np.mean(np.abs(b_yt - b_yp)) / scale
            boot_mases.append(b_mase)
            
            if yp_naive is not None:
                b_yp_naive = yp_naive[b_indices]
                b_mase_naive = np.mean(np.abs(b_yt - b_yp_naive)) / scale
                boot_diff_naives.append(b_mase - b_mase_naive)
                
            if yp_win is not None:
                b_yp_win = yp_win[b_indices]
                b_mase_win = np.mean(np.abs(b_yt - b_yp_win)) / scale
                boot_diff_wins.append(b_mase - b_mase_win)
    else:
        # Row-level moving block indices
        n_blocks = int(np.ceil(n / block_length))
        max_start = max(1, n - block_length + 1)
        
        for _ in range(n_boot):
            starts = rng.integers(0, max_start, size=n_blocks)
            indices = np.concatenate([np.arange(s, s + block_length) for s in starts])[:n]
            
            b_yt = yt[indices]
            b_yp = yp[indices]
            b_mase = np.mean(np.abs(b_yt - b_yp)) / scale
            boot_mases.append(b_mase)
            
            if yp_naive is not None:
                b_yp_naive = yp_naive[indices]
                b_mase_naive = np.mean(np.abs(b_yt - b_yp_naive)) / scale
                boot_diff_naives.append(b_mase - b_mase_naive)
                
            if yp_win is not None:
                b_yp_win = yp_win[indices]
                b_mase_win = np.mean(np.abs(b_yt - b_yp_win)) / scale
                boot_diff_wins.append(b_mase - b_mase_win)
            
    res = {
        "mase_ci_low": round(float(np.quantile(boot_mases, 0.025)), 4),
        "mase_ci_high": round(float(np.quantile(boot_mases, 0.975)), 4),
    }
    if boot_diff_naives:
        res["diff_naive_ci_low"] = round(float(np.quantile(boot_diff_naives, 0.025)), 4)
        res["diff_naive_ci_high"] = round(float(np.quantile(boot_diff_naives, 0.975)), 4)
    if boot_diff_wins:
        res["diff_winner_ci_low"] = round(float(np.quantile(boot_diff_wins, 0.025)), 4)
        res["diff_winner_ci_high"] = round(float(np.quantile(boot_diff_wins, 0.975)), 4)
        
    return res

def diebold_mariano_test(y_true, y_pred1, y_pred2, h=1, week_indices=None, loss="absolute"):
    """
    Diebold-Mariano test of equal predictive accuracy for two forecasts at horizon h.
    Loss: 'absolute' or 'squared'.
    When week_indices is provided, losses are aggregated by week, preserving time series structure.
    Returns (DM_statistic, p_value).
    """
    mask = pd.notna(y_true) & pd.notna(y_pred1) & pd.notna(y_pred2)
    yt = np.array(y_true)[mask]
    yp1 = np.array(y_pred1)[mask]
    yp2 = np.array(y_pred2)[mask]
    
    if len(yt) < 10:
        return np.nan, np.nan
        
    if week_indices is not None:
        weeks = np.array(week_indices)[mask]
        df_loss = pd.DataFrame({"week": weeks, "yt": yt, "yp1": yp1, "yp2": yp2})
        if loss == "absolute":
            df_loss["d"] = np.abs(df_loss["yt"] - df_loss["yp1"]) - np.abs(df_loss["yt"] - df_loss["yp2"])
        else:
            df_loss["d"] = (df_loss["yt"] - df_loss["yp1"])**2 - (df_loss["yt"] - df_loss["yp2"])**2
        d_series = df_loss.groupby("week")["d"].mean().sort_index().values
        d = d_series
    else:
        if loss == "absolute":
            d = np.abs(yt - yp1) - np.abs(yt - yp2)
        else:
            d = (yt - yp1)**2 - (yt - yp2)**2
        
    d_mean = np.mean(d)
    n = len(d)
    
    gamma_0 = np.var(d, ddof=0)
    gamma_sum = 0.0
    for k in range(1, h):
        if k < n:
            gamma_k = np.cov(d[k:], d[:-k])[0, 1]
            gamma_sum += 2 * (1 - k / h) * gamma_k
            
    v_d = (gamma_0 + gamma_sum) / n
    if v_d <= 1e-8:
        return 0.0, 1.0
        
    dm_stat = d_mean / np.sqrt(v_d)
    p_val = 2.0 * (1.0 - stats.norm.cdf(np.abs(dm_stat)))
    return round(float(dm_stat), 4), round(float(p_val), 4)

def holm_bonferroni_correction(p_values):
    """
    Holm-Bonferroni step-down correction for multiple testing.
    Returns array of adjusted p-values in original order.
    """
    p_vals = np.array(p_values)
    m = len(p_vals)
    if m == 0:
        return np.array([])
        
    order = np.argsort(p_vals)
    sorted_p = p_vals[order]
    
    adj_p = np.zeros(m)
    current_max = 0.0
    for i, p in enumerate(sorted_p):
        step_val = (m - i) * p
        current_max = max(current_max, step_val)
        adj_p[i] = min(1.0, current_max)
        
    # Revert back to original index order
    revert = np.argsort(order)
    return np.round(adj_p[revert], 4)

def compute_friedman_nemenyi(perf_matrix):
    """
    Friedman non-parametric test + Nemenyi critical difference calculation.
    perf_matrix: DataFrame with vegetables as rows, models as columns (lower is better, e.g. MASE).
    Returns (friedman_stat, friedman_p, average_ranks, critical_difference).
    """
    ranks = perf_matrix.rank(axis=1, ascending=True)
    avg_ranks = ranks.mean(axis=0)
    
    n_datasets, k_models = perf_matrix.shape
    if n_datasets < 2 or k_models < 2:
        return np.nan, np.nan, avg_ranks, np.nan
        
    stat, p_val = stats.friedmanchisquare(*[ranks.iloc[:, j] for j in range(k_models)])
    
    # Nemenyi critical difference at alpha = 0.05
    # q_alpha approximation for alpha=0.05
    # For k between 5 and 30, studentized range stat / sqrt(2) approx:
    q_alpha = 1.960 + 0.3 * np.log(k_models)
    cd = q_alpha * np.sqrt((k_models * (k_models + 1)) / (6.0 * n_datasets))
    
    return round(float(stat), 4), round(float(p_val), 6), avg_ranks.round(2), round(float(cd), 2)

def compute_model_confidence_set(loss_matrix, alpha=0.05, n_boot=500, seed=42):
    """
    Model Confidence Set (MCS) procedure (Hansen et al. 2011).
    Iteratively eliminates the worst model until the hypothesis of equal predictive ability (EPA) holds.
    loss_matrix: DataFrame of absolute errors (rows: observations, cols: models).
    Returns list of model names included in the (1 - alpha) MCS.
    """
    models = list(loss_matrix.columns)
    rng = np.random.default_rng(seed)
    
    while len(models) > 1:
        sub_losses = loss_matrix[models].values
        n, m = sub_losses.shape
        mean_losses = sub_losses.mean(axis=0)
        
        # Loss differential against grand mean
        grand_mean = mean_losses.mean()
        d_j = mean_losses - grand_mean
        
        # Variance of d_j via bootstrap
        boot_d = []
        for _ in range(n_boot):
            idx = rng.integers(0, n, size=n)
            b_means = sub_losses[idx].mean(axis=0)
            boot_d.append(b_means - b_means.mean())
        var_d = np.var(boot_d, axis=0, ddof=1)
        var_d = np.clip(var_d, a_min=1e-8, a_max=None)
        
        t_stats = d_j / np.sqrt(var_d)
        t_max = np.max(t_stats)
        
        # P-value of t_max under null of EPA
        boot_t_max = [np.max((b - d_j) / np.sqrt(var_d)) for b in boot_d]
        p_val = np.mean(np.array(boot_t_max) >= t_max)
        
        if p_val > alpha:
            break # Null of EPA cannot be rejected
            
        # Eliminate model with largest loss
        worst_idx = np.argmax(mean_losses)
        models.pop(worst_idx)
        
    return models
