"""
features.py - Leak-free preprocessing and feature engineering for IT4010 COC.
"""

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import KFold


class CropLagImputer(BaseEstimator, TransformerMixin):
    """
    Imputes missing values in Prev_Season_Total_Cost_Incl_Imputed:
    - Computes crop-level median on training fold.
    - Fallback to global median on training fold.
    - Creates binary indicator column PrevSeason_Was_Missing.
    """
    def __init__(self, lag_col='Prev_Season_Total_Cost_Incl_Imputed', crop_col='Crop'):
        self.lag_col = lag_col
        self.crop_col = crop_col
        self.global_median_ = 0.0
        self.crop_medians_ = {}

    def fit(self, X, y=None):
        X_df = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        if self.lag_col in X_df.columns:
            valid_vals = X_df[self.lag_col].dropna()
            self.global_median_ = float(valid_vals.median()) if len(valid_vals) > 0 else 0.0
            if self.crop_col in X_df.columns:
                self.crop_medians_ = X_df.groupby(self.crop_col)[self.lag_col].median().to_dict()
        return self

    def transform(self, X):
        X_df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        if self.lag_col in X_df.columns:
            missing_flag = X_df[self.lag_col].isna().astype(float)
            crop_series = X_df[self.crop_col].map(self.crop_medians_).fillna(self.global_median_)
            X_df[self.lag_col] = X_df[self.lag_col].fillna(crop_series).fillna(self.global_median_)
            X_df['PrevSeason_Was_Missing'] = missing_flag
        return X_df


def build_leak_free_preprocessor(random_state=42):
    """
    Builds the verified leak-free Pipeline:
    1. CropLagImputer on Prev_Season_Total_Cost_Incl_Imputed.
    2. ColumnTransformer:
       - TargetEncoder for Crop and District (5-fold internal CV, fit only on train fold).
       - OneHotEncoder for Season and Irrigation_Type.
       - StandardScaler for Year_Start, USD_LKR_Rate.
       - StandardScaler for Prev_Season_Total_Cost_Incl_Imputed, PrevSeason_Was_Missing.
    """
    cv_kf = KFold(n_splits=5, shuffle=True, random_state=random_state)

    te = TargetEncoder(target_type='continuous', cv=cv_kf, smooth='auto')
    ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)

    ct = ColumnTransformer(
        transformers=[
            ('target_enc', te, ['Crop', 'District']),
            ('ohe', ohe, ['Season', 'Irrigation_Type']),
            ('time_scaler', StandardScaler(), ['Year_Start', 'USD_LKR_Rate']),
            ('lag_scaler', StandardScaler(), ['Prev_Season_Total_Cost_Incl_Imputed', 'PrevSeason_Was_Missing'])
        ],
        remainder='drop'
    )

    pipe = Pipeline([
        ('lag_imputer', CropLagImputer()),
        ('col_transformer', ct)
    ])
    return pipe


def get_feature_names(fitted_pipeline, sample_X):
    """Extracts output feature names from the fitted preprocessor pipeline."""
    ct = fitted_pipeline.named_steps['col_transformer']
    names = []
    for name, trans, cols in ct.transformers_:
        if name == 'remainder':
            continue
        if hasattr(trans, 'get_feature_names_out'):
            try:
                fn = list(trans.get_feature_names_out(cols))
                names.extend(fn)
                continue
            except Exception:
                pass
        names.extend(cols)
    return names
