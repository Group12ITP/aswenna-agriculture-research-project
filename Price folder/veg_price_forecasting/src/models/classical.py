import logging
import numpy as np
import pandas as pd
from sklearn.linear_model import Ridge, Lasso, ElasticNet, LinearRegression
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor
from sklearn.svm import SVR
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
import lightgbm as lgb
import xgboost as xgb
from catboost import CatBoostRegressor

from ..utils import get_logger

logger = get_logger("src.models.classical")

def get_classical_model(model_name, params=None, random_state=42):
    """Factory creating sklearn-compatible regression pipelines."""
    params = params or {}
    
    if model_name == "linear_regression":
        return Pipeline([("scaler", StandardScaler()), ("reg", LinearRegression())])
        
    elif model_name == "ridge":
        alpha = params.get("alpha", 1.0)
        return Pipeline([("scaler", StandardScaler()), ("reg", Ridge(alpha=alpha, random_state=random_state))])
        
    elif model_name == "lasso":
        alpha = params.get("alpha", 0.1)
        return Pipeline([("scaler", StandardScaler()), ("reg", Lasso(alpha=alpha, random_state=random_state, max_iter=2000))])
        
    elif model_name == "elastic_net":
        alpha = params.get("alpha", 0.1)
        l1_ratio = params.get("l1_ratio", 0.5)
        return Pipeline([("scaler", StandardScaler()), ("reg", ElasticNet(alpha=alpha, l1_ratio=l1_ratio, random_state=random_state, max_iter=2000))])
        
    elif model_name == "random_forest":
        n_estimators = params.get("n_estimators", 150)
        max_depth = params.get("max_depth", 12)
        min_samples_leaf = params.get("min_samples_leaf", 3)
        return RandomForestRegressor(
            n_estimators=n_estimators, max_depth=max_depth,
            min_samples_leaf=min_samples_leaf, random_state=random_state, n_jobs=-1
        )
        
    elif model_name == "extra_trees":
        n_estimators = params.get("n_estimators", 150)
        max_depth = params.get("max_depth", 12)
        min_samples_leaf = params.get("min_samples_leaf", 3)
        return ExtraTreesRegressor(
            n_estimators=n_estimators, max_depth=max_depth,
            min_samples_leaf=min_samples_leaf, random_state=random_state, n_jobs=-1
        )
        
    elif model_name == "gradient_boosting":
        n_estimators = params.get("n_estimators", 150)
        learning_rate = params.get("learning_rate", 0.05)
        max_depth = params.get("max_depth", 5)
        return GradientBoostingRegressor(
            n_estimators=n_estimators, learning_rate=learning_rate,
            max_depth=max_depth, random_state=random_state
        )
        
    elif model_name == "lightgbm":
        n_estimators = params.get("n_estimators", 200)
        learning_rate = params.get("learning_rate", 0.04)
        num_leaves = params.get("num_leaves", 31)
        subsample = params.get("subsample", 0.8)
        colsample_bytree = params.get("colsample_bytree", 0.8)
        return lgb.LGBMRegressor(
            n_estimators=n_estimators, learning_rate=learning_rate,
            num_leaves=num_leaves, subsample=subsample,
            colsample_bytree=colsample_bytree, random_state=random_state,
            verbose=-1, n_jobs=-1
        )
        
    elif model_name == "xgboost":
        n_estimators = params.get("n_estimators", 200)
        learning_rate = params.get("learning_rate", 0.04)
        max_depth = params.get("max_depth", 5)
        subsample = params.get("subsample", 0.8)
        colsample_bytree = params.get("colsample_bytree", 0.8)
        return xgb.XGBRegressor(
            n_estimators=n_estimators, learning_rate=learning_rate,
            max_depth=max_depth, subsample=subsample,
            colsample_bytree=colsample_bytree, random_state=random_state,
            n_jobs=-1
        )
        
    elif model_name == "catboost":
        iterations = params.get("iterations", params.get("n_estimators", 100))
        learning_rate = params.get("learning_rate", 0.04)
        depth = params.get("depth", params.get("max_depth", 5))
        return CatBoostRegressor(
            iterations=iterations, learning_rate=learning_rate,
            depth=depth, random_seed=random_state, verbose=False, thread_count=-1
        )
        
    elif model_name == "svr":
        C = params.get("C", 10.0)
        epsilon = params.get("epsilon", 0.1)
        return Pipeline([("scaler", StandardScaler()), ("reg", SVR(C=C, epsilon=epsilon))])
        
    else:
        raise ValueError(f"Unknown classical model name: {model_name}")

class QuantileLightGBM:
    """LightGBM quantile regressor for 80% and 95% intervals."""
    def __init__(self, quantiles=(0.025, 0.10, 0.50, 0.90, 0.975), params=None, random_state=42):
        self.quantiles = quantiles
        self.params = params or {}
        self.random_state = random_state
        self.models = {}
        
    def fit(self, X, y):
        for q in self.quantiles:
            reg = lgb.LGBMRegressor(
                objective="quantile",
                alpha=q,
                n_estimators=self.params.get("n_estimators", 150),
                learning_rate=self.params.get("learning_rate", 0.05),
                num_leaves=self.params.get("num_leaves", 31),
                random_state=self.random_state,
                verbose=-1,
                n_jobs=-1
            )
            reg.fit(X, y)
            self.models[q] = reg
        return self
        
    def predict(self, X):
        preds = {q: self.models[q].predict(X) for q in self.quantiles}
        return {
            "expected": preds.get(0.50),
            "lower_80": np.clip(preds.get(0.10), a_min=0.0, a_max=None),
            "upper_80": preds.get(0.90),
            "lower_95": np.clip(preds.get(0.025), a_min=0.0, a_max=None),
            "upper_95": preds.get(0.975),
        }
