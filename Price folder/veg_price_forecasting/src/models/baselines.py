import numpy as np
import pandas as pd

class NaiveForecaster:
    """Predicts the most recently observed value for all horizons."""
    def __init__(self):
        self.name = "naive"
        
    def fit(self, y_train):
        self.last_value = pd.Series(y_train).dropna().iloc[-1] if len(pd.Series(y_train).dropna()) > 0 else 0.0
        return self
        
    def predict(self, horizon=1, y_history=None):
        if y_history is not None and len(pd.Series(y_history).dropna()) > 0:
            return float(pd.Series(y_history).dropna().iloc[-1])
        return float(self.last_value)

class SeasonalNaiveForecaster:
    """Predicts value from the same reporting week in the previous year (season_m=48)."""
    def __init__(self, season_m=48):
        self.name = f"seasonal_naive_{season_m}"
        self.season_m = season_m
        
    def fit(self, y_train):
        self.history = pd.Series(y_train).ffill().bfill().values
        return self
        
    def predict(self, horizon=1, y_history=None):
        hist = pd.Series(y_history).ffill().bfill().values if y_history is not None else self.history
        if len(hist) >= self.season_m:
            idx = len(hist) - self.season_m + (horizon - 1) % self.season_m
            idx = min(idx, len(hist) - 1)
            return float(hist[idx])
        elif len(hist) > 0:
            return float(hist[-1])
        return 0.0

class MovingAverageForecaster:
    """Predicts mean of the last k weeks."""
    def __init__(self, window=4):
        self.name = f"moving_average_{window}"
        self.window = window
        
    def fit(self, y_train):
        self.last_k = pd.Series(y_train).dropna().iloc[-self.window:].mean() if len(pd.Series(y_train).dropna()) > 0 else 0.0
        return self
        
    def predict(self, horizon=1, y_history=None):
        if y_history is not None and len(pd.Series(y_history).dropna()) > 0:
            return float(pd.Series(y_history).dropna().iloc[-self.window:].mean())
        return float(self.last_k)

class DriftForecaster:
    """Predicts linear drift extrapolated from start to end of available history."""
    def __init__(self):
        self.name = "drift"
        
    def fit(self, y_train):
        s = pd.Series(y_train).dropna()
        if len(s) > 1:
            self.first_val = float(s.iloc[0])
            self.last_val = float(s.iloc[-1])
            self.t_span = len(s)
            self.slope = (self.last_val - self.first_val) / max(1, self.t_span - 1)
        else:
            self.last_val = float(s.iloc[0]) if len(s) > 0 else 0.0
            self.slope = 0.0
        return self
        
    def predict(self, horizon=1, y_history=None):
        if y_history is not None:
            s = pd.Series(y_history).dropna()
            if len(s) > 1:
                slope = (float(s.iloc[-1]) - float(s.iloc[0])) / max(1, len(s) - 1)
                return max(0.0, float(s.iloc[-1]) + horizon * slope)
            elif len(s) > 0:
                return float(s.iloc[-1])
        return max(0.0, self.last_val + horizon * self.slope)

class RollingMeanForecaster:
    """Predicts mean of the last 52 weeks (rolling 52-week mean)."""
    def __init__(self, window=52):
        self.name = f"rolling_{window}wk_mean"
        self.window = window
        
    def fit(self, y_train):
        s = pd.Series(y_train).dropna()
        self.mean_val = float(s.iloc[-self.window:].mean()) if len(s) > 0 else 0.0
        return self
        
    def predict(self, horizon=1, y_history=None):
        if y_history is not None:
            s = pd.Series(y_history).dropna()
            if len(s) > 0:
                return float(s.iloc[-self.window:].mean())
        return float(self.mean_val)

class SeasonalMean4YrForecaster:
    """Predicts seasonal mean of the same week of year across the prior 4 years."""
    def __init__(self, season_m=48, n_years=4):
        self.name = "seasonal_mean_4yr"
        self.season_m = season_m
        self.n_years = n_years
        
    def fit(self, y_train):
        self.history = pd.Series(y_train).ffill().bfill().values
        return self
        
    def predict(self, horizon=1, y_history=None):
        hist = pd.Series(y_history).ffill().bfill().values if y_history is not None else self.history
        n = len(hist)
        if n == 0:
            return 0.0
        vals = []
        for k in range(1, self.n_years + 1):
            idx = n - k * self.season_m + (horizon - 1) % self.season_m
            if 0 <= idx < n:
                vals.append(float(hist[idx]))
        if len(vals) > 0:
            return float(np.mean(vals))
        return float(hist[-1])

class AR1CategoryMeanForecaster:
    """Predicts AR(1) reversion toward category mean: y_hat = phi^h * y_t + (1 - phi^h) * cat_mean."""
    def __init__(self, phi=0.92):
        self.name = "ar1_category_mean"
        self.phi = phi
        
    def fit(self, y_train, cat_mean=None):
        s = pd.Series(y_train).dropna()
        self.last_val = float(s.iloc[-1]) if len(s) > 0 else 0.0
        self.cat_mean = float(cat_mean) if cat_mean is not None else self.last_val
        return self
        
    def predict(self, horizon=1, y_history=None, cat_mean=None):
        s = pd.Series(y_history).dropna() if y_history is not None else []
        y_t = float(s.iloc[-1]) if len(s) > 0 else self.last_val
        mu = float(cat_mean) if cat_mean is not None else (self.cat_mean if hasattr(self, 'cat_mean') else y_t)
        decay = self.phi ** horizon
        return float(decay * y_t + (1.0 - decay) * mu)

