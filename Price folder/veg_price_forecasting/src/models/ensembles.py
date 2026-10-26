import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge

from ..utils import get_logger

logger = get_logger("src.models.ensembles")

class SimpleAverageEnsemble:
    """Combines top-k model forecasts via unweighted arithmetic mean."""
    def __init__(self, model_names):
        self.name = "simple_average_ensemble"
        self.model_names = model_names
        
    def predict(self, pred_dict):
        """pred_dict: {model_name: array_of_predictions}"""
        selected = [pred_dict[m] for m in self.model_names if m in pred_dict]
        if not selected:
            raise ValueError(f"None of {self.model_names} found in prediction dictionary.")
        stacked = np.column_stack(selected)
        return np.nan_to_num(np.nanmean(stacked, axis=1), nan=0.0)

class StackingMetaLearner:
    """Stacking meta-learner using constrained Ridge regression on validation forecasts."""
    def __init__(self, model_names, alpha=1.0):
        self.name = "stacking_meta_learner"
        self.model_names = model_names
        self.meta_reg = Ridge(alpha=alpha, positive=True, fit_intercept=False)
        
    def fit(self, val_preds_dict, y_val):
        """Fit meta-learner on validation predictions only."""
        X_meta = np.column_stack([val_preds_dict[m] for m in self.model_names])
        X_meta = np.nan_to_num(X_meta, nan=0.0, posinf=1e6, neginf=0.0)
        mask = pd.notna(y_val)
        self.meta_reg.fit(X_meta[mask], np.array(y_val)[mask])
        return self
        
    def predict(self, pred_dict):
        X_meta = np.column_stack([pred_dict[m] for m in self.model_names])
        X_meta = np.nan_to_num(X_meta, nan=0.0, posinf=1e6, neginf=0.0)
        return np.clip(self.meta_reg.predict(X_meta), a_min=0.0, a_max=None)

class BestPerCategoryEnsemble:
    """Selects the best performing model per vegetable category on validation data."""
    def __init__(self):
        self.name = "best_per_category"
        self.best_models_by_category = {}
        
    def fit(self, val_preds_dict, y_val, categories_series):
        """Find best model (lowest MASE/MAE) for each category on validation."""
        cats_arr = np.array(categories_series)
        unique_cats = np.unique(cats_arr)
        y_val_arr = np.array(y_val)
        for cat in unique_cats:
            cat_mask = (cats_arr == cat) & pd.notna(y_val_arr)
            best_cat_mae = float("inf")
            best_cat_m = list(val_preds_dict.keys())[0]
            for m_name, preds in val_preds_dict.items():
                p_cat = np.array(preds)[cat_mask]
                y_cat = y_val_arr[cat_mask]
                if len(y_cat) > 0:
                    mae = np.mean(np.abs(y_cat - p_cat))
                    if mae < best_cat_mae:
                        best_cat_mae = mae
                        best_cat_m = m_name
            self.best_models_by_category[cat] = best_cat_m
        return self
        
    def predict(self, pred_dict, categories_series):
        cats_arr = np.array(categories_series)
        res = np.zeros(len(cats_arr))
        for cat, m_name in self.best_models_by_category.items():
            cat_mask = (cats_arr == cat)
            res[cat_mask] = np.array(pred_dict[m_name])[cat_mask]
        return np.nan_to_num(res, nan=0.0)

