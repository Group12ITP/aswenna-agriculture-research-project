"""
models_stat.py - Statistical, econometric, and time-series models for IT4010 COC.
Supports Naive, Seasonal Naive, Historical Mean, ETS, ARIMA, SARIMA, SARIMAX, Prophet, and Prophet Regularized.
"""

from typing import Dict, Any, Optional, Tuple
from pathlib import Path
import warnings
import json
import numpy as np
import pandas as pd

from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from prophet import Prophet


class TimeSeriesSeriesWrapper:
    """
    Manages per-series time-series forecasting across 95 Crop x District x Irrigation series.
    Provides automated AIC order search, fallback handling, and test-set prediction.
    """
    def __init__(self, model_type: str = "arima", min_obs: int = 8, fallback: str = "seasonal_naive"):
        self.model_type = model_type.lower()
        self.min_obs = min_obs
        self.fallback = fallback.lower()
        self.fitted_models_ = {}
        self.series_orders_ = {}
        self.series_history_ = {}
        self.crop_medians_ = {}
        self.global_median_ = 100000.0

    def fit(self, df_train: pd.DataFrame, exog_col: Optional[str] = "USD_LKR_Rate"):
        """Fits time-series models per series on the training fold."""
        self.fitted_models_ = {}
        self.series_orders_ = {}
        self.series_history_ = {}

        # Calculate crop-level medians for graceful fallback
        self.crop_medians_ = df_train.groupby("Crop")["Total_Cost_Incl_Imputed"].median().to_dict()
        self.global_median_ = float(df_train["Total_Cost_Incl_Imputed"].median())

        # Group training data by series
        for series_key, grp in df_train.groupby("series_key"):
            s_sorted = grp.sort_values(by="season_order_key").copy()
            y_hist = np.log1p(s_sorted["Total_Cost_Incl_Imputed"].values)
            dates = s_sorted["calendar_date"].values
            exog_hist = s_sorted[exog_col].values if (exog_col and exog_col in s_sorted.columns) else None

            self.series_history_[series_key] = {
                "y": y_hist,
                "dates": dates,
                "exog": exog_hist,
                "seasons": s_sorted["Season"].values,
                "years": s_sorted["Year_Start"].values,
                "raw_costs": s_sorted["Total_Cost_Incl_Imputed"].values,
                "crop": s_sorted["Crop"].iloc[0]
            }

            # Check eligibility for parametric time-series models
            if len(y_hist) < self.min_obs or self.model_type in ["naive", "seasonal_naive", "historical_mean"]:
                continue

            try:
                if self.model_type == "ets":
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        ets = ExponentialSmoothing(y_hist, trend="add", seasonal=None, initialization_method="estimated")
                        fit_res = ets.fit()
                        self.fitted_models_[series_key] = fit_res

                elif self.model_type in ["arima", "sarima", "sarimax"]:
                    best_aic = float("inf")
                    best_model = None
                    best_order = (1, 1, 0)

                    # Concise, robust candidate orders
                    if self.model_type == "arima":
                        candidate_orders = [(1, 1, 0), (0, 1, 1), (1, 1, 1), (0, 1, 0), (1, 0, 0)]
                        seasonal_order = (0, 0, 0, 0)
                    elif self.model_type in ["sarima", "sarimax"]:
                        candidate_orders = [(1, 1, 0), (0, 1, 1), (1, 0, 0)]
                        seasonal_order = (0, 1, 0, 2) if len(y_hist) >= 10 else (0, 0, 0, 0)

                    for order in candidate_orders:
                        try:
                            with warnings.catch_warnings():
                                warnings.simplefilter("ignore")
                                if self.model_type == "sarimax" and exog_hist is not None:
                                    model = ARIMA(
                                        y_hist,
                                        exog=exog_hist,
                                        order=order,
                                        seasonal_order=seasonal_order
                                    )
                                elif self.model_type == "sarima":
                                    model = ARIMA(
                                        y_hist,
                                        order=order,
                                        seasonal_order=seasonal_order
                                    )
                                else:
                                    model = ARIMA(y_hist, order=order)
                                res = model.fit()
                                if res.aic < best_aic:
                                    best_aic = res.aic
                                    best_model = res
                                    best_order = order
                        except Exception:
                            continue

                    if best_model is not None:
                        self.fitted_models_[series_key] = best_model
                        self.series_orders_[series_key] = best_order

                elif self.model_type in ["prophet", "prophet_regularized"]:
                    df_p = pd.DataFrame({
                        "ds": pd.to_datetime(dates),
                        "y": y_hist
                    })
                    if exog_col and exog_hist is not None:
                        df_p["usd_rate"] = exog_hist

                    cp_scale = 0.001 if self.model_type == "prophet_regularized" else 0.01
                    n_cp = 2 if self.model_type == "prophet_regularized" else 3

                    m = Prophet(
                        growth="linear",
                        yearly_seasonality=False,
                        weekly_seasonality=False,
                        daily_seasonality=False,
                        changepoint_prior_scale=cp_scale,
                        n_changepoints=n_cp
                    )
                    m.add_seasonality(name="maha_yala", period=365.25, fourier_order=2)
                    if exog_col and exog_hist is not None:
                        m.add_regressor("usd_rate")

                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        m.fit(df_p)
                        self.fitted_models_[series_key] = m

            except Exception:
                pass

        return self

    def predict(self, df_test: pd.DataFrame, exog_col: Optional[str] = "USD_LKR_Rate") -> Tuple[np.ndarray, float]:
        """
        Generates predictions for all rows in df_test.
        Returns predicted values (original LKR scale) and model coverage share.
        """
        preds = []
        covered_count = 0

        for _, row in df_test.iterrows():
            s_key = row["series_key"]
            test_season = row["Season"]
            test_year = row["Year_Start"]
            test_crop = row["Crop"]
            test_exog = row.get(exog_col, 250.0) if exog_col else 250.0

            history = self.series_history_.get(s_key, None)
            crop_median = self.crop_medians_.get(test_crop, self.global_median_)

            # --- BASELINE FAMILIES ---
            if self.model_type == "naive":
                if history is not None and len(history["raw_costs"]) > 0:
                    preds.append(float(history["raw_costs"][-1]))
                    covered_count += 1
                else:
                    preds.append(float(crop_median))
                continue

            elif self.model_type == "seasonal_naive":
                if history is not None and len(history["raw_costs"]) > 0:
                    same_season = history["raw_costs"][history["seasons"] == test_season]
                    if len(same_season) > 0:
                        preds.append(float(same_season[-1]))
                        covered_count += 1
                    else:
                        preds.append(float(history["raw_costs"][-1]))
                        covered_count += 1
                else:
                    preds.append(float(crop_median))
                continue

            elif self.model_type == "historical_mean":
                if history is not None and len(history["raw_costs"]) > 0:
                    preds.append(float(np.mean(history["raw_costs"])))
                    covered_count += 1
                else:
                    preds.append(float(crop_median))
                continue

            # --- PARAMETRIC TIME-SERIES (ETS, ARIMA, SARIMA, SARIMAX, PROPHET) ---
            def get_fallback():
                if history is not None and len(history["raw_costs"]) > 0:
                    same_season = history["raw_costs"][history["seasons"] == test_season]
                    if len(same_season) > 0:
                        return float(same_season[-1])
                    return float(history["raw_costs"][-1])
                return float(crop_median)

            pred_val = None
            if s_key in self.fitted_models_:
                fitted = self.fitted_models_[s_key]
                try:
                    if self.model_type == "ets":
                        log_p = fitted.forecast(1)[0]
                        pred_val = float(np.expm1(log_p))
                    elif self.model_type in ["arima", "sarima"]:
                        log_p = fitted.forecast(steps=1)[0]
                        pred_val = float(np.expm1(log_p))
                    elif self.model_type == "sarimax":
                        log_p = fitted.forecast(steps=1, exog=[test_exog])[0]
                        pred_val = float(np.expm1(log_p))
                    elif self.model_type in ["prophet", "prophet_regularized"]:
                        fut = pd.DataFrame({
                            "ds": [pd.to_datetime(f"{test_year}-05-01" if test_season == "Yala" else f"{test_year}-10-01")]
                        })
                        if exog_col:
                            fut["usd_rate"] = [test_exog]
                        log_p = fitted.predict(fut)["yhat"].values[0]
                        if self.model_type == "prophet_regularized":
                            log_p = np.clip(log_p, 9.0, 15.5)
                        pred_val = float(np.expm1(log_p))
                except Exception:
                    pred_val = None

            if pred_val is not None and not np.isnan(pred_val) and pred_val > 0:
                preds.append(pred_val)
                covered_count += 1
            else:
                preds.append(get_fallback())

        coverage = covered_count / max(1, len(df_test))
        return np.array(preds), coverage

    def save_fold_models(self, save_dir: Path, fold_name: str):
        """Saves fitted models and orders to disk for reproducibility."""
        save_dir.mkdir(parents=True, exist_ok=True)
        orders_file = save_dir / "series_orders.json"
        with open(orders_file, "w") as f:
            json.dump({k: list(v) for k, v in self.series_orders_.items()}, f, indent=2)
