import logging
import numpy as np
import pandas as pd
import lightgbm as lgb

from .utils import get_logger

logger = get_logger("src.intervals")

class ScaleAwareConformalPredictor:
    """
    Scale-aware conformal prediction using relative log-price residuals:
      s_i = |log(y_i) - log(y_hat_i)|
    Interval bounds for predicted price y_hat:
      [y_hat * exp(-q), y_hat * exp(+q)]
    Guarantees non-negative bounds and constant percentage width across price scales.
    Calibrated strictly on a dedicated calibration fold that is NOT the evaluation fold.
    """
    def __init__(self, alpha_levels=(0.20, 0.05)):
        self.alpha_levels = alpha_levels
        self.log_quantiles = {}
        
    def calibrate(self, y_cal, y_cal_pred):
        """Compute relative log-ratio non-conformity scores on dedicated calibration fold."""
        y_c = np.array(y_cal)
        y_cp = np.array(y_cal_pred)
        mask = pd.notna(y_c) & pd.notna(y_cp) & (y_c > 0) & (y_cp > 0)
        
        if mask.sum() == 0:
            logger.warning("Empty calibration set for conformal calibration.")
            return
            
        # Non-conformity score: absolute log error
        s_scores = np.abs(np.log(y_c[mask]) - np.log(y_cp[mask]))
        n = len(s_scores)
        
        for alpha in self.alpha_levels:
            # Finite-sample conformal quantile: ceil((n + 1) * (1 - alpha)) / n
            level = min(1.0, np.ceil((n + 1) * (1.0 - alpha)) / n)
            q = np.quantile(s_scores, q=min(0.999, level))
            self.log_quantiles[alpha] = float(q)
            
    def predict_intervals(self, y_pred):
        """Generate scale-aware lower and upper bounds as a percentage of predicted price."""
        yp = np.array(y_pred)
        results = {}
        for alpha, q in self.log_quantiles.items():
            conf_pct = int(round((1.0 - alpha) * 100))
            lower = np.maximum(0.0, yp * np.exp(-q))
            upper = yp * np.exp(+q)
            results[f"lower_{conf_pct}"] = lower
            results[f"upper_{conf_pct}"] = upper
            results[f"width_pct_{conf_pct}"] = float((np.exp(q) - np.exp(-q)) * 100.0)
        return results

class ConformalizedQuantileRegression:
    """
    Conformalized Quantile Regression (CQR) using LightGBM pinball loss.
    Calibrates on dedicated calibration fold to provide distribution-free marginal coverage.
    """
    def __init__(self, alpha=0.20, n_estimators=150, random_state=42):
        self.alpha = alpha
        self.q_low = alpha / 2.0
        self.q_high = 1.0 - alpha / 2.0
        self.model_low = lgb.LGBMRegressor(objective="quantile", alpha=self.q_low, n_estimators=n_estimators, random_state=random_state, verbose=-1, n_jobs=-1)
        self.model_high = lgb.LGBMRegressor(objective="quantile", alpha=self.q_high, n_estimators=n_estimators, random_state=random_state, verbose=-1, n_jobs=-1)
        self.correction_q = 0.0
        
    def fit(self, X_train, y_train):
        mask = pd.notna(y_train)
        self.model_low.fit(X_train[mask], y_train[mask])
        self.model_high.fit(X_train[mask], y_train[mask])
        return self
        
    def calibrate(self, X_cal, y_cal):
        mask = pd.notna(y_cal)
        yc = np.array(y_cal)[mask]
        q_l = self.model_low.predict(X_cal[mask])
        q_h = self.model_high.predict(X_cal[mask])
        
        # CQR non-conformity score: E_i = max(q_low - y, y - q_high)
        e_scores = np.maximum(q_l - yc, yc - q_h)
        n = len(e_scores)
        level = min(1.0, np.ceil((n + 1) * (1.0 - self.alpha)) / n)
        self.correction_q = float(np.quantile(e_scores, q=min(0.999, level)))
        return self
        
    def predict_intervals(self, X_eval):
        q_l = self.model_low.predict(X_eval)
        q_h = self.model_high.predict(X_eval)
        lower = np.maximum(0.0, q_l - self.correction_q)
        upper = q_h + self.correction_q
        return lower, upper

def evaluate_interval_quality(y_true, lower, upper, y_pred=None, metadata_df=None):
    """
    Calculate empirical coverage %, mean width (Rs), and mean width (% of price).
    Optionally computes breakdowns by vegetable and by category.
    """
    mask = np.array(pd.notna(y_true) & pd.notna(lower) & pd.notna(upper))
    if mask.sum() == 0:
        return {"coverage_pct": np.nan, "mean_width_lkr": np.nan, "mean_width_pct": np.nan}
        
    yt = np.array(y_true)[mask]
    lb = np.array(lower)[mask]
    ub = np.array(upper)[mask]
    
    covered = (yt >= lb) & (yt <= ub)
    coverage = np.mean(covered) * 100.0
    width_lkr = np.mean(ub - lb)
    
    # Scale-aware width as percentage of true price (or predicted price)
    denom = np.array(y_pred)[mask] if y_pred is not None else yt
    denom = np.clip(denom, a_min=1.0, a_max=None)
    width_pct = np.mean((ub - lb) / denom) * 100.0
    
    res = {
        "coverage_pct": round(float(coverage), 2),
        "mean_width_lkr": round(float(width_lkr), 2),
        "mean_width_pct": round(float(width_pct), 2),
        "n_eval": int(len(yt))
    }
    
    if metadata_df is not None and len(metadata_df) == len(mask):
        sub_meta = metadata_df.reset_index(drop=True).iloc[mask]
        yt_arr = np.array(y_true)[mask]
        lb_arr = np.array(lower)[mask]
        ub_arr = np.array(upper)[mask]
        by_cat = {}
        for cat in sub_meta["category"].unique():
            c_idx = (sub_meta["category"] == cat).values
            if c_idx.sum() > 0:
                cov_c = np.mean((yt_arr[c_idx] >= lb_arr[c_idx]) & (yt_arr[c_idx] <= ub_arr[c_idx])) * 100.0
                w_pct_c = np.mean((ub_arr[c_idx] - lb_arr[c_idx]) / np.clip(yt_arr[c_idx], 1.0, None)) * 100.0
                by_cat[cat] = {"coverage_pct": round(float(cov_c), 2), "width_pct": round(float(w_pct_c), 2)}
        res["by_category"] = by_cat
        
    return res
