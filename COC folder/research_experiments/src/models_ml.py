"""
models_ml.py - Classical and ensemble shallow machine learning models for IT4010 COC.
Supports Ridge, Lasso, ElasticNet, KNN, SVR, DT, RF, ExtraTrees, GB, HistGB, XGBoost, LightGBM, CatBoost, and Stacking.
"""

from typing import Dict, Any
from sklearn.linear_model import Ridge, Lasso, ElasticNet
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import (
    RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor,
    HistGradientBoostingRegressor, StackingRegressor, VotingRegressor
)
from sklearn.compose import TransformedTargetRegressor
from sklearn.pipeline import Pipeline
import xgboost as xgb
import lightgbm as lgb
import catboost as cb
import numpy as np

from features import build_leak_free_preprocessor


def get_base_regressor(model_name: str, random_state: int = 42):
    """Instantiates base regressor by identifier."""
    name = model_name.lower()

    if name == "ridge":
        return Ridge(alpha=1.0)
    elif name == "lasso":
        return Lasso(alpha=0.001, random_state=random_state)
    elif name == "elasticnet":
        return ElasticNet(alpha=0.01, l1_ratio=0.5, random_state=random_state)
    elif name == "knn":
        return KNeighborsRegressor(n_neighbors=5, weights="distance")
    elif name == "svr":
        return SVR(C=10.0, epsilon=0.05, kernel="rbf")
    elif name == "decisiontree":
        return DecisionTreeRegressor(max_depth=6, min_samples_split=5, random_state=random_state)
    elif name == "randomforest":
        return RandomForestRegressor(n_estimators=100, max_depth=8, random_state=random_state, n_jobs=-1)
    elif name == "extratrees":
        return ExtraTreesRegressor(n_estimators=100, max_depth=8, random_state=random_state, n_jobs=-1)
    elif name == "gradientboosting":
        return GradientBoostingRegressor(n_estimators=100, learning_rate=0.05, max_depth=3, subsample=0.8, random_state=random_state)
    elif name == "gradientboosting_tuned":
        return GradientBoostingRegressor(n_estimators=150, learning_rate=0.05, max_depth=4, subsample=0.8, random_state=random_state)
    elif name == "histgradientboosting":
        return HistGradientBoostingRegressor(max_iter=100, learning_rate=0.05, max_depth=4, random_state=random_state)
    elif name == "xgboost":
        return xgb.XGBRegressor(n_estimators=150, learning_rate=0.05, max_depth=4, subsample=0.8, random_state=random_state, n_jobs=-1)
    elif name == "lightgbm":
        return lgb.LGBMRegressor(n_estimators=150, learning_rate=0.05, max_depth=4, num_leaves=15, subsample=0.8, random_state=random_state, verbose=-1, n_jobs=-1)
    elif name == "catboost":
        return cb.CatBoostRegressor(iterations=200, learning_rate=0.05, depth=4, random_seed=random_state, verbose=0)
    else:
        raise ValueError(f"Unknown model name: {model_name}")


def build_pipeline_model(model_name: str, random_state: int = 42) -> TransformedTargetRegressor:
    """Builds full end-to-end TransformedTargetRegressor pipeline (preprocessor + model)."""
    base = get_base_regressor(model_name, random_state=random_state)
    prep = build_leak_free_preprocessor(random_state=random_state)
    pipe = Pipeline([
        ("prep", prep),
        ("regressor", base)
    ])
    return TransformedTargetRegressor(regressor=pipe, func=np.log1p, inverse_func=np.expm1)


def build_stacking_ensemble(top_model_names=None, random_state: int = 42) -> TransformedTargetRegressor:
    """Builds a Stacking Regressor combining top tree-based algorithms."""
    if top_model_names is None:
        top_model_names = ["gradientboosting", "randomforest", "catboost"]

    estimators = [(name, get_base_regressor(name, random_state=random_state)) for name in top_model_names]
    stacking = StackingRegressor(
        estimators=estimators,
        final_estimator=Ridge(alpha=1.0),
        cv=5
    )
    prep = build_leak_free_preprocessor(random_state=random_state)
    pipe = Pipeline([
        ("prep", prep),
        ("regressor", stacking)
    ])
    return TransformedTargetRegressor(regressor=pipe, func=np.log1p, inverse_func=np.expm1)
