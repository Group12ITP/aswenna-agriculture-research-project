import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
import pandas as pd
import joblib

# Ensure root veg_price_forecasting directory is in sys.path
PROJECT_DIR = Path(__file__).resolve().parent.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

from src.utils import load_config
from src.data import load_and_preprocess_vegetables
from src.features import build_vegetable_features
from src.train import prepare_feature_matrices
from src.models.statistical import AutoARIMARollingForecaster
from src.models.baselines import NaiveForecaster, SeasonalMean4YrForecaster

logger = logging.getLogger("backend.inference")
logging.basicConfig(level=logging.INFO)

# Category-specific scale-aware conformal multipliers calibrated on weeks 393-416 (frozen artifact manifest)
CONFORMAL_CALIBRATION_80 = {
    "leafy vegetables": {"q_80": 0.0814, "mult_lower": 0.922, "mult_upper": 1.085, "width_pct": 16.3},
    "lowland vegetables": {"q_80": 0.2696, "mult_lower": 0.764, "mult_upper": 1.309, "width_pct": 54.6},
    "upcountry vegetables": {"q_80": 0.3769, "mult_lower": 0.686, "mult_upper": 1.458, "width_pct": 77.2}
}

class ForecasterService:
    def __init__(self):
        self.initialized = False
        self.cfg = None
        self.df_long = None
        self.df_feat = None
        self.origin_week = None
        self.origin_date = None
        self.vegetables_catalog = []
        self.veg_names = []
        self.models = {}
        self.feature_matrices = {}
        self.precomputed_forecasts = {}

    def initialize(self):
        if self.initialized:
            return
        
        logger.info("Initializing ForecasterService...")
        self.cfg = load_config(PROJECT_DIR / "config.yaml")
        _, self.df_long = load_and_preprocess_vegetables(self.cfg)
        self.df_feat = build_vegetable_features(self.df_long, cfg=self.cfg, include_cross_veg=True)
        
        self.origin_week = int(self.df_feat["week_index"].max())
        origin_row = self.df_feat[self.df_feat["week_index"] == self.origin_week].iloc[0]
        self.origin_date = str(origin_row["approx_date"])
        logger.info(f"Origin Week: {self.origin_week} ({self.origin_date})")

        # Build vegetable catalog
        veg_df = self.df_feat[self.df_feat["week_index"] == self.origin_week][
            ["product_name", "category", "unit", "price_lkr"]
        ].sort_values(["category", "product_name"])
        
        self.vegetables_catalog = [
            {
                "name": row["product_name"],
                "category": row["category"],
                "unit": row["unit"],
                "latest_price": round(float(row["price_lkr"]), 2),
                "origin_date": self.origin_date,
                "origin_week": self.origin_week
            }
            for _, row in veg_df.iterrows()
        ]
        self.veg_names = [v["name"] for v in self.vegetables_catalog]

        # Load frozen models
        frozen_dir = PROJECT_DIR / "models" / "frozen"
        logger.info(f"Loading frozen models from {frozen_dir}...")
        
        # h=1 Lasso
        lasso_path = frozen_dir / "selected_h1_lasso.joblib"
        if lasso_path.exists():
            self.models["lasso_h1"] = joblib.load(lasso_path)
            X1, _, _ = prepare_feature_matrices(self.df_feat, target_col="target_h1")
            self.feature_matrices[1] = X1
            logger.info("Loaded selected h=1 Lasso model.")

        # h=4 AutoARIMA
        arima_path = frozen_dir / "selected_h4_auto_arima.joblib"
        if arima_path.exists():
            self.models["auto_arima_h4"] = joblib.load(arima_path)
            logger.info("Loaded selected h=4 AutoARIMA suite.")

        # h=8 CatBoost
        cb_path = frozen_dir / "selected_h8_catboost.joblib"
        if cb_path.exists():
            self.models["catboost_h8"] = joblib.load(cb_path)
            X8, _, _ = prepare_feature_matrices(self.df_feat, target_col="target_h8")
            self.feature_matrices[8] = X8
            logger.info("Loaded selected h=8 CatBoost model.")

        # h=12 Transformer
        tf_path = frozen_dir / "selected_h12_transformer.joblib"
        if tf_path.exists():
            self.models["transformer_h12"] = joblib.load(tf_path)
            X12, _, _ = prepare_feature_matrices(self.df_feat, target_col="target_h12")
            self.feature_matrices[12] = X12
            logger.info("Loaded selected h=12 Transformer model.")

        # Precompute all (vegetable, horizon, model) combinations for instant responses
        self._precompute_all()
        self.initialized = True
        logger.info("ForecasterService initialization completed successfully.")

    def _precompute_all(self):
        """Precomputes point forecasts and comparison baselines for all 32 vegetables and 4 horizons."""
        cache_dir = PROJECT_DIR / "backend" / "cache"
        cache_dir.mkdir(parents=True, exist_ok=True)
        cache_file = cache_dir / "precomputed_forecasts.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    raw_cache = json.load(f)
                # Reconstruct tuple keys
                self.precomputed_forecasts = {
                    (item["vegetable"], int(item["horizon"])): item["data"]
                    for item in raw_cache
                }
                logger.info(f"Loaded {len(self.precomputed_forecasts)} precomputed forecasts from {cache_file}.")
                return
            except Exception as e:
                logger.warning(f"Could not load cache: {e}. Recomputing...")

        logger.info("Precomputing forward predictions for all 32 vegetables at origin week %d...", self.origin_week)
        horizons = [1, 4, 8, 12]
        origin_mask = self.df_feat["week_index"] == self.origin_week
        cache_records = []
        
        for h in horizons:
            # 1. Rule-selected model
            if h == 1:
                model_name = "Lasso (Selected)"
                X1 = self.feature_matrices[1]
                x_sub = X1.loc[origin_mask]
                preds = self.models["lasso_h1"].predict(x_sub)
                pred_dict = dict(zip(self.df_feat.loc[origin_mask, "product_name"], preds))
            elif h == 4:
                model_name = "AutoARIMA (Selected)"
                pred_dict = {}
                for veg in self.veg_names:
                    v_df = self.df_feat[self.df_feat["product_name"] == veg].sort_values("week_index")
                    hist = v_df["price_lkr"].values
                    forecaster = AutoARIMARollingForecaster(d=1)
                    forecaster.fit_parameters(hist)
                    fc_map = forecaster.rolling_forecast(hist, [len(hist)-1], horizon=4)
                    pred_dict[veg] = fc_map.get(len(hist)-1, float(hist[-1]))
            elif h == 8:
                model_name = "CatBoost (Selected)"
                cb = self.models["catboost_h8"]
                X8 = self.feature_matrices[8]
                x_sub = X8.loc[origin_mask, cb.feature_names_]
                preds = cb.predict(x_sub)
                pred_dict = dict(zip(self.df_feat.loc[origin_mask, "product_name"], preds))
            elif h == 12:
                model_name = "Transformer (Selected)"
                tf = self.models["transformer_h12"]
                X12 = self.feature_matrices[12]
                x_sub = X12.loc[origin_mask]
                preds = tf.predict(x_sub)
                pred_dict = dict(zip(self.df_feat.loc[origin_mask, "product_name"], preds))

            # Store baseline predictions
            naive_model = NaiveForecaster()
            s_mean_model = SeasonalMean4YrForecaster(season_m=48, n_years=4)
            
            for veg in self.veg_names:
                v_df = self.df_feat[self.df_feat["product_name"] == veg].sort_values("week_index")
                hist = v_df["price_lkr"].values
                cat = v_df["category"].iloc[0]
                unit = v_df["unit"].iloc[0]
                last_price = float(hist[-1])
                
                naive_val = round(max(0.0, float(naive_model.predict(horizon=h, y_history=hist))), 2)
                s_mean_val = round(max(0.0, float(s_mean_model.predict(horizon=h, y_history=hist))), 2)
                selected_val = round(max(0.0, float(pred_dict[veg])), 2)

                record = {
                    "selected": selected_val,
                    "selected_model_name": model_name,
                    "naive": naive_val,
                    "seasonal_mean_4yr": s_mean_val,
                    "last_observed_price": round(last_price, 2),
                    "category": cat,
                    "unit": unit
                }
                self.precomputed_forecasts[(veg, h)] = record
                cache_records.append({
                    "vegetable": veg,
                    "horizon": h,
                    "data": record
                })

        # Save to disk cache
        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_records, f, indent=2)
            logger.info(f"Saved {len(cache_records)} precomputed forecasts to disk cache at {cache_file}.")
        except Exception as e:
            logger.warning(f"Failed to write cache to {cache_file}: {e}")

    def get_vegetables(self) -> List[Dict[str, Any]]:
        return self.vegetables_catalog

    def get_history(self, vegetable: str, weeks: int = 104) -> Dict[str, Any]:
        # Case-insensitive match
        match = next((v for v in self.vegetables_catalog if v["name"].lower() == vegetable.lower()), None)
        if not match:
            available = ", ".join(self.veg_names[:10]) + "..."
            raise ValueError(f"Vegetable '{vegetable}' not found. Available vegetables include: {available}")
        
        veg_clean = match["name"]
        v_df = self.df_long[self.df_long["product_name"] == veg_clean].sort_values("week_index")
        if weeks > 0:
            v_df = v_df.tail(weeks)
            
        history_list = [
            {
                "week": int(row["week_index"]),
                "date": str(row["approx_date"]),
                "price": round(float(row["price_lkr"]), 2)
            }
            for _, row in v_df.iterrows()
        ]
        
        return {
            "vegetable": veg_clean,
            "category": match["category"],
            "unit": match["unit"],
            "total_weeks": len(history_list),
            "history": history_list
        }

    def get_forecast(self, vegetable: str, horizon: int = 4, model: str = "selected") -> Dict[str, Any]:
        if horizon not in [1, 4, 8, 12]:
            raise ValueError(f"Invalid horizon: {horizon}. Must be one of [1, 4, 8, 12].")
            
        valid_models = ["selected", "naive", "seasonal_mean_4yr"]
        if model not in valid_models:
            raise ValueError(f"Invalid model: '{model}'. Must be one of {valid_models}.")

        match = next((v for v in self.vegetables_catalog if v["name"].lower() == vegetable.lower()), None)
        if not match:
            available = ", ".join(self.veg_names[:10]) + "..."
            raise ValueError(f"Vegetable '{vegetable}' not found. Available vegetables include: {available}")

        veg_clean = match["name"]
        cached = self.precomputed_forecasts.get((veg_clean, horizon))
        if not cached:
            raise RuntimeError(f"Forecast not found for {veg_clean} at h={horizon}.")

        # Target date calculation (7 days per week)
        origin_dt = pd.to_datetime(self.origin_date)
        target_dt = origin_dt + pd.Timedelta(weeks=horizon)
        target_date_str = target_dt.strftime("%Y-%m-%d")
        target_week = self.origin_week + horizon

        # Determine point forecast and model used
        if model == "selected":
            point_fc = cached["selected"]
            model_used = cached["selected_model_name"]
        elif model == "naive":
            point_fc = cached["naive"]
            model_used = "Naive Persistence (y_t)"
        elif model == "seasonal_mean_4yr":
            point_fc = cached["seasonal_mean_4yr"]
            model_used = "Seasonal Mean (4-Year Historical Average)"

        # Conformal intervals
        cat = cached["category"]
        cal_80 = CONFORMAL_CALIBRATION_80.get(cat)
        if cal_80:
            lo_80 = round(max(0.0, point_fc * cal_80["mult_lower"]), 2)
            hi_80 = round(point_fc * cal_80["mult_upper"], 2)
            interval_80 = {"lo": lo_80, "hi": hi_80}
        else:
            interval_80 = None

        # 95% interval:
        # Prompt requirement: "If the existing code can't produce them at inference, say so and return null instead of inventing them."
        interval_95 = None

        return {
            "vegetable": veg_clean,
            "category": cat,
            "unit": cached["unit"],
            "origin_week": self.origin_week,
            "origin_date": self.origin_date,
            "target_week": target_week,
            "target_date": target_date_str,
            "model_used": model_used,
            "point_forecast": point_fc,
            "interval_80": interval_80,
            "interval_95": interval_95,
            "interval_95_note": "95% conformal multipliers were not calibrated in the frozen category manifest (only 80% was calibrated on weeks 393-416).",
            "last_observed_price": cached["last_observed_price"],
            "naive_forecast": cached["naive"],
            "seasonal_mean_4yr_forecast": cached["seasonal_mean_4yr"]
        }

# Global singleton
service = ForecasterService()

def get_service() -> ForecasterService:
    if not service.initialized:
        service.initialize()
    return service
