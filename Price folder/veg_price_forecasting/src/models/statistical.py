import logging
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet

from ..utils import get_logger

logger = get_logger("src.models.statistical")

# Silence noisy third-party loggers
logging.getLogger("cmdstanpy").setLevel(logging.ERROR)
logging.getLogger("prophet").setLevel(logging.ERROR)

class HoltWintersRollingForecaster:
    """
    Holt-Winters Exponential Smoothing on log-prices with rolling state updates.
    State recursion:
      level[t] = alpha * (z[t] - season[t-m]) + (1 - alpha) * (level[t-1] + phi * trend[t-1])
      trend[t] = beta * (level[t] - level[t-1]) + (1 - beta) * phi * trend[t-1]
      season[t] = gamma * (z[t] - level[t]) + (1 - gamma) * season[t-m]
    Forecast:
      z_hat[t+h|t] = level[t] + sum(phi^j * trend[t]) + season[t+h-m]
      y_hat[t+h|t] = exp(z_hat[t+h|t])
    """
    def __init__(self, seasonal_periods=48, damped=True):
        self.name = "holt_winters_ets"
        self.seasonal_periods = seasonal_periods
        self.damped = damped
        self.alpha = 0.4
        self.beta = 0.05
        self.gamma = 0.1
        self.phi = 0.95 if damped else 1.0
        
    def fit_parameters(self, train_series):
        """Fit smoothing parameters on train log prices by minimizing 1-step SSE."""
        s = pd.Series(train_series).ffill().bfill().clip(lower=1.0)
        z = np.log(s.values)
        m = self.seasonal_periods
        n = len(z)
        if n < 10:
            return self
            
        def sse_loss(params):
            a, b = params
            level = z[0]
            trend = 0.0
            err = 0.0
            for t in range(1, n):
                fc = level + trend
                err += (z[t] - fc) ** 2
                new_level = a * z[t] + (1.0 - a) * (level + trend)
                trend = b * (new_level - level) + (1.0 - b) * trend
                level = new_level
            return err
            
        try:
            res = minimize(sse_loss, [0.6, 0.02], bounds=[(0.15, 0.95), (0.00, 0.15)], method="L-BFGS-B")
            self.alpha, self.beta = res.x
        except Exception as e:
            logger.debug(f"Holt-Winters parameter optimization fallback: {e}")
            self.alpha, self.beta = 0.6, 0.02
        return self
        
    def rolling_forecast(self, full_series, target_indices, horizon=1):
        """
        Produce rolling-origin h-step ahead forecasts for each origin in target_indices.
        At each origin t, information set includes only index <= t.
        """
        s = pd.Series(full_series).ffill().bfill().clip(lower=1.0)
        z = np.log(s.values)
        m = self.seasonal_periods
        n = len(z)
        
        # Initialize filter state
        level = np.mean(z[:min(m, n)])
        trend = (z[min(m, n-1)] - z[0]) / max(1, min(m, n-1))
        season = list(z[:min(m, n)] - level)
        if len(season) < m:
            season = [0.0] * (m - len(season)) + season
            
        a, b, g, phi = self.alpha, self.beta, self.gamma, self.phi
        
        # Step through up to each target index
        forecasts = {}
        target_set = set(target_indices)
        
        for t in range(n):
            z_t = z[t]
            s_prev = season[len(season) - m]
            new_level = a * (z_t - s_prev) + (1.0 - a) * (level + phi * trend)
            new_trend = b * (new_level - level) + (1.0 - b) * phi * trend
            new_season = g * (z_t - new_level) + (1.0 - g) * s_prev
            level, trend = new_level, new_trend
            season.append(new_season)
            
            if t in target_set:
                # Forecast h steps ahead from origin t
                # Trend damping sum: phi + phi^2 + ... + phi^h
                phi_sum = phi * (1.0 - phi**horizon) / (1.0 - phi) if abs(phi - 1.0) > 1e-4 else float(horizon)
                s_future = season[len(season) - m + ((horizon - 1) % m)]
                z_hat = level + phi_sum * trend + s_future
                forecasts[t] = max(0.0, float(np.exp(z_hat)))
                
        return forecasts

class AutoARIMARollingForecaster:
    """
    ARIMA forecaster on log prices with rolling Kalman filter state updates.
    Fits order (p, 1, q) on train, then updates sequentially via model.apply().
    """
    def __init__(self, d=1):
        self.name = "auto_arima"
        self.d = d
        self.best_order = (1, 1, 1)
        self.fitted_res = None
        
    def fit_parameters(self, train_series):
        s = pd.Series(train_series).ffill().bfill().clip(lower=1.0)
        z = np.log(s.values)
        candidates = [(1, self.d, 0), (0, self.d, 1), (1, self.d, 1), (2, self.d, 1)]
        best_aic = float("inf")
        best_res = None
        best_ord = (1, self.d, 1)
        
        for order in candidates:
            try:
                mod = ARIMA(z, order=order)
                res = mod.fit()
                if res.aic < best_aic:
                    best_aic = res.aic
                    best_res = res
                    best_ord = order
            except Exception:
                continue
                
        self.fitted_res = best_res
        self.best_order = best_ord
        return self
        
    def rolling_forecast(self, full_series, target_indices, horizon=1):
        s = pd.Series(full_series).ffill().bfill().clip(lower=1.0)
        z = np.log(s.values)
        forecasts = {}
        
        if self.fitted_res is None:
            self.fit_parameters(z[:target_indices[0]])
            
        for t in target_indices:
            hist_z = z[:t+1]
            try:
                res_t = self.fitted_res.apply(hist_z)
                fc_log = res_t.forecast(steps=horizon)[-1]
                forecasts[t] = max(0.0, float(np.exp(fc_log)))
            except Exception:
                # Fallback to naive persistence on log scale
                forecasts[t] = max(0.0, float(s.iloc[t]))
                
        return forecasts

class SARIMAXRollingForecaster:
    """
    SARIMAX forecaster on log prices with category seasonal persistence.
    """
    def __init__(self, order=(1, 1, 1)):
        self.name = "sarimax"
        self.order = order
        self.fitted_res = None
        
    def fit_parameters(self, train_series):
        s = pd.Series(train_series).ffill().bfill().clip(lower=1.0)
        z = np.log(s.values)
        try:
            mod = ARIMA(z, order=self.order)
            self.fitted_res = mod.fit()
        except Exception:
            self.fitted_res = None
        return self
        
    def rolling_forecast(self, full_series, target_indices, horizon=1):
        s = pd.Series(full_series).ffill().bfill().clip(lower=1.0)
        z = np.log(s.values)
        forecasts = {}
        
        if self.fitted_res is None:
            self.fit_parameters(z[:target_indices[0]])
            
        for t in target_indices:
            hist_z = z[:t+1]
            try:
                if self.fitted_res is not None:
                    res_t = self.fitted_res.apply(hist_z)
                    fc_log = res_t.forecast(steps=horizon)[-1]
                    forecasts[t] = max(0.0, float(np.exp(fc_log)))
                else:
                    forecasts[t] = max(0.0, float(s.iloc[t]))
            except Exception:
                forecasts[t] = max(0.0, float(s.iloc[t]))
                
        return forecasts

class ProphetRollingForecaster:
    """
    Prophet forecaster on log prices with autoregressive residual state updates.
    """
    def __init__(self):
        self.name = "prophet"
        self.model = None
        
    def fit(self, df_train):
        """df_train must have columns 'ds' and 'y' (where y is log-price)."""
        m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
        m.fit(df_train)
        self.model = m
        return self
        
    def rolling_forecast(self, df_all, target_indices, horizon=1):
        """df_all must have 'ds' (datetime) and 'price_lkr'."""
        df_p = df_all.copy()
        df_p["y_log"] = np.log(df_p["price_lkr"].ffill().bfill().clip(lower=1.0))
        
        # Fit Prophet on history up to first target index
        first_t = target_indices[0]
        tr_df = df_p.iloc[:first_t][["ds", "y_log"]].rename(columns={"y_log": "y"})
        self.fit(tr_df)
        
        # Predict full timeline
        fc = self.model.predict(df_p[["ds"]])
        pred_base = fc["yhat"].values
        actual_z = df_p["y_log"].values
        
        forecasts = {}
        for t in target_indices:
            target_step = t + horizon
            base_target = pred_base[target_step] if target_step < len(pred_base) else pred_base[-1]
            # Residual at origin t
            res_t = actual_z[t] - pred_base[t]
            # AR(1) decay of residual offset
            rho = 0.88 ** horizon
            fc_log = base_target + res_t * rho
            forecasts[t] = max(0.0, float(np.exp(fc_log)))
            
        return forecasts
