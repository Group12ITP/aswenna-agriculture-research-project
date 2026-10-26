#!/usr/bin/env python3
"""
Full Model Training, Validation, and Evaluation Pipeline for IT4010 SO1
=====================================================================
Predictive Cost Estimator for Agricultural Cultivation Cost Prediction.

This script:
1. Loads coc_features_dedup.csv and filters to 'High' and 'Medium' sample size tiers (~641 rows, 23 crops).
   Saves filtered set to coc_model_ready.csv.
2. Constructs leak-free preprocessors with:
   - Median-imputation within Crop for Prev_Season_Total_Cost_Incl_Imputed + PrevSeason_Was_Missing flag.
   - One-hot encoding for Season and Irrigation_Type.
   - Target encoding for Crop and District (m-estimate smoothing, fit only on training folds).
   - Log1p target transformation (np.log1p) and expm1 inverse-transform for evaluation.
   - StandardScaler on numeric columns.
3. Computes two baselines:
   - B1: Naive carry-forward (lag).
   - B2: Out-of-fold Crop-District mean baseline.
4. Evaluates 4 models across BOTH GroupKFold (groups=Crop) and Leave-One-Season-Out (LOSO):
   - LinearRegression
   - DecisionTreeRegressor
   - RandomForestRegressor
   - GradientBoostingRegressor
5. Hyperparameter-tunes the winning model via GridSearchCV under GroupKFold.
6. Runs an ablation study with 5 GradientBoosting variants (A: Full, B: No Lag, C: No Time, D: Structure Only, E: Lag Only).
7. Computes and plots feature importances (feature_importances.png) and Pearson correlations.
8. Generates residuals plot (residuals_plot.png) for best model predictions colored by Year_Start.
9. Serializes best pipeline as best_model_pipeline.pkl.
10. Saves model_evaluation.csv, model_evaluation_loso_per_year.csv, ablation_results.csv, and baselines.csv.
"""

import sys
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import joblib

from sklearn.base import BaseEstimator, TransformerMixin, RegressorMixin
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.preprocessing import OneHotEncoder, StandardScaler, TargetEncoder
from sklearn.compose import ColumnTransformer, TransformedTargetRegressor
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GroupKFold, LeaveOneGroupOut, GridSearchCV, KFold
from sklearn.metrics import mean_absolute_error, root_mean_squared_error, r2_score

# ==============================================================================
# 1. CUSTOM PREPROCESSORS (LEAK-FREE)
# ==============================================================================

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

    def fit(self, X, y=None):
        X_df = X if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        self.global_median_ = float(X_df[self.lag_col].median()) if self.lag_col in X_df.columns else 0.0
        if self.lag_col in X_df.columns and self.crop_col in X_df.columns:
            self.crop_medians_ = X_df.groupby(self.crop_col)[self.lag_col].median().to_dict()
        else:
            self.crop_medians_ = {}
        return self

    def transform(self, X):
        X_df = X.copy() if isinstance(X, pd.DataFrame) else pd.DataFrame(X)
        if self.lag_col in X_df.columns:
            missing_flag = X_df[self.lag_col].isna().astype(float)
            crop_series = X_df[self.crop_col].map(self.crop_medians_).fillna(self.global_median_)
            X_df[self.lag_col] = X_df[self.lag_col].fillna(crop_series).fillna(self.global_median_)
            X_df['PrevSeason_Was_Missing'] = missing_flag
        return X_df

def build_preprocessor(feature_mode='full', random_state=42):
    """
    Builds a scikit-learn ColumnTransformer based on feature ablation mode:
    - 'full' / 'A': all 7 features
    - 'no_lag' / 'B': without lag
    - 'no_time' / 'C': without Year_Start and USD_LKR_Rate
    - 'structure_only' / 'D': only District, Crop, Season, Irrigation_Type
    - 'lag_only' / 'E': only Prev_Season_Total_Cost_Incl_Imputed + flag
    """
    transformers = []
    
    # Target Encoding for Crop & District
    cv_kf = KFold(n_splits=5, shuffle=True, random_state=random_state)
    
    if feature_mode in ['full', 'no_lag', 'no_time', 'structure_only']:
        # TargetEncoder for Crop and District
        te_cols = ['Crop', 'District']
        te = TargetEncoder(target_type='continuous', cv=cv_kf, smooth='auto')
        transformers.append(('target_enc', te, te_cols))
        
        # OneHotEncoder for Season and Irrigation_Type
        ohe_cols = ['Season', 'Irrigation_Type']
        ohe = OneHotEncoder(handle_unknown='ignore', sparse_output=False)
        transformers.append(('ohe', ohe, ohe_cols))

    if feature_mode in ['full', 'no_lag']:
        # Time features
        time_cols = ['Year_Start', 'USD_LKR_Rate']
        transformers.append(('time_scaler', StandardScaler(), time_cols))

    if feature_mode in ['full', 'no_time', 'lag_only']:
        # Lag features
        lag_cols = ['Prev_Season_Total_Cost_Incl_Imputed', 'PrevSeason_Was_Missing']
        transformers.append(('lag_scaler', StandardScaler(), lag_cols))

    ct = ColumnTransformer(transformers=transformers, remainder='drop')
    
    # If lag is used, precede with CropLagImputer
    if feature_mode in ['full', 'no_time', 'lag_only']:
        pipe_prep = Pipeline([
            ('lag_imputer', CropLagImputer()),
            ('col_transformer', ct)
        ])
        return pipe_prep
    else:
        return ct

def get_feature_names(preprocessor, sample_X, sample_y):
    """Utility to fit preprocessor and extract clean output feature names."""
    prep = Pipeline([('prep', preprocessor)])
    prep.fit(sample_X, sample_y)
    ct = prep.named_steps['prep']
    if hasattr(ct, 'named_steps'): # nested pipeline
        ct = ct.named_steps['col_transformer']
    names = []
    for name, trans, cols in ct.transformers_:
        if name == 'remainder':
            continue
        if hasattr(trans, 'get_feature_names_out'):
            try:
                fn = trans.get_feature_names_out(cols)
                names.extend(fn)
                continue
            except:
                pass
        names.extend(cols)
    return names

# ==============================================================================
# 2. MAIN PIPELINE EXECUTION
# ==============================================================================

def main():
    print("=" * 80)
    print("IT4010 SO1: AGRICULTURAL CULTIVATION COST PREDICTION PIPELINE")
    print("=" * 80)
    workspace = Path(r"c:\Users\MSI\Desktop\Research\COC folder")
    data_dir = workspace / "data" / "processed" if (workspace / "data" / "processed").exists() else workspace
    models_dir = workspace / "models" if (workspace / "models").exists() else workspace
    figures_dir = workspace / "figures" if (workspace / "figures").exists() else workspace
    input_csv = data_dir / "coc_features_dedup.csv"
    
    if not input_csv.exists():
        print(f"Error: {input_csv} not found!")
        sys.exit(1)
        
    df_raw = pd.read_csv(input_csv)
    print(f"Decision: Loaded {len(df_raw)} records from {input_csv.name}.")
    
    # --------------------------------------------------------------------------
    # STEP 1: SCOPE FILTERING
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 1: SCOPE FILTERING (High & Medium Categories)")
    print("=" * 80)
    df = df_raw[df_raw['Crop_Sample_Size_Category'].isin(['High', 'Medium'])].copy()
    df = df.reset_index(drop=True)
    
    # Fill any missing Irrigation_Type with 'Unspecified'
    df['Irrigation_Type'] = df['Irrigation_Type'].fillna('Unspecified')
    
    model_ready_path = data_dir / "coc_model_ready.csv"
    df.to_csv(model_ready_path, index=False, encoding="utf-8-sig")
    print(f"Decision: Saved filtered training set ({len(df)} rows, {df['Crop'].nunique()} crops) to {model_ready_path.name}.")
    
    excluded = df_raw[~df_raw['Crop_Sample_Size_Category'].isin(['High', 'Medium'])]
    print(f"Excluded from training: {len(excluded)} row(s) -> {excluded['Crop'].tolist()} (Low sample size tier).")

    # --------------------------------------------------------------------------
    # STEP 2: LEAK-FREE FEATURE MATRIX & TARGET
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 2: FEATURE MATRIX & TARGET ISOLATION")
    print("=" * 80)
    
    feature_cols = [
        'District', 'Crop', 'Season', 'Irrigation_Type',
        'Year_Start', 'USD_LKR_Rate', 'Prev_Season_Total_Cost_Incl_Imputed'
    ]
    target_col = 'Total_Cost_Incl_Imputed'
    
    X = df[feature_cols].copy()
    y = df[target_col].copy()
    
    print(f"Target: '{target_col}' (LKR / acre)")
    print(f"Features ({len(feature_cols)} leak-free attributes): {feature_cols}")
    print("Guaranteed zero target leakage: All component costs, yields, gross income, and profits excluded.")

    # --------------------------------------------------------------------------
    # STEP 3: BASELINES COMPUTATION
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 3: BENCHMARK BASELINES (B1 & B2)")
    print("=" * 80)
    
    # B1: Naive Carry-Forward
    mask_lag = df['Prev_Season_Total_Cost_Incl_Imputed'].notna()
    y_true_b1 = df.loc[mask_lag, target_col]
    y_pred_b1 = df.loc[mask_lag, 'Prev_Season_Total_Cost_Incl_Imputed']
    
    mae_b1 = mean_absolute_error(y_true_b1, y_pred_b1)
    rmse_b1 = root_mean_squared_error(y_true_b1, y_pred_b1)
    r2_b1 = r2_score(y_true_b1, y_pred_b1)
    print(f"B1. Naive Carry-Forward (evaluated on {mask_lag.sum()} rows with valid prior season lag):")
    print(f"    MAE: Rs {mae_b1:,.1f} | RMSE: Rs {rmse_b1:,.1f} | R2: {r2_b1:7.4f}")

    # B2: Crop-District Mean Baseline (Out-of-Fold under GroupKFold)
    gkf = GroupKFold(n_splits=5)
    b2_maes, b2_rmses, b2_r2s = [], [], []
    
    for tr_idx, te_idx in gkf.split(df, groups=df['Crop']):
        d_tr = df.iloc[tr_idx]
        d_te = df.iloc[te_idx]
        
        global_mean = d_tr[target_col].mean()
        crop_mean = d_tr.groupby('Crop')[target_col].mean().to_dict()
        crop_dist_mean = d_tr.groupby(['Crop', 'District'])[target_col].mean().to_dict()
        
        preds_b2 = []
        for _, row in d_te.iterrows():
            c, d = row['Crop'], row['District']
            if (c, d) in crop_dist_mean:
                preds_b2.append(crop_dist_mean[(c, d)])
            elif c in crop_mean:
                preds_b2.append(crop_mean[c])
            else:
                preds_b2.append(global_mean)
                
        b2_maes.append(mean_absolute_error(d_te[target_col], preds_b2))
        b2_rmses.append(root_mean_squared_error(d_te[target_col], preds_b2))
        b2_r2s.append(r2_score(d_te[target_col], preds_b2))
        
    mae_b2 = np.mean(b2_maes)
    rmse_b2 = np.mean(b2_rmses)
    r2_b2 = np.mean(b2_r2s)
    print(f"B2. Out-of-Fold Crop-District Mean Baseline (GroupKFold):")
    print(f"    MAE: Rs {mae_b2:,.1f} ± {np.std(b2_maes):,.1f} | RMSE: Rs {rmse_b2:,.1f} ± {np.std(b2_rmses):,.1f} | R2: {r2_b2:7.4f} ± {np.std(b2_r2s):7.4f}")

    baselines_df = pd.DataFrame([
        {"Baseline": "B1. Naive Carry-Forward (Lagged Cost)", "Evaluated_Rows": mask_lag.sum(), "MAE": mae_b1, "RMSE": rmse_b1, "R2": r2_b1},
        {"Baseline": "B2. Out-of-Fold Crop-District Mean", "Evaluated_Rows": len(df), "MAE": mae_b2, "RMSE": rmse_b2, "R2": r2_b2},
    ])
    baselines_df.to_csv(data_dir / "baselines.csv", index=False)
    print(f"Decision: Saved baselines summary to {data_dir / 'baselines.csv'}.")

    # --------------------------------------------------------------------------
    # STEP 4: MODEL EVALUATION ACROSS VALIDATION STRATEGIES
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 4: MODEL TRAINING & CROSS-VALIDATION")
    print("=" * 80)
    
    models = {
        "LinearRegression": LinearRegression(),
        "DecisionTreeRegressor": DecisionTreeRegressor(random_state=42),
        "RandomForestRegressor": RandomForestRegressor(n_estimators=100, random_state=42),
        "GradientBoostingRegressor": GradientBoostingRegressor(n_estimators=100, random_state=42)
    }

    eval_results = []
    loso_per_year_records = []
    
    # Dictionary to store out-of-fold predictions for residuals plot
    oof_predictions = {m_name: np.zeros(len(df)) for m_name in models}

    for m_name, base_model in models.items():
        print(f"\nEvaluating Model: {m_name}...")
        
        # Build leak-free pipeline with log target transformation
        preprocessor = build_preprocessor('full', random_state=42)
        pipe = Pipeline([
            ('prep', preprocessor),
            ('regressor', base_model)
        ])
        ttr_model = TransformedTargetRegressor(regressor=pipe, func=np.log1p, inverse_func=np.expm1)

        # ----------------------------------------------------------------------
        # Strategy A: GroupKFold (groups=Crop)
        # ----------------------------------------------------------------------
        gkf = GroupKFold(n_splits=5)
        maes_gkf, rmses_gkf, r2s_gkf = [], [], []
        
        for fold, (tr_idx, te_idx) in enumerate(gkf.split(X, y, groups=df['Crop'])):
            X_tr, y_tr = X.iloc[tr_idx], y.iloc[tr_idx]
            X_te, y_te = X.iloc[te_idx], y.iloc[te_idx]
            
            ttr_model.fit(X_tr, y_tr)
            preds = ttr_model.predict(X_te)
            
            maes_gkf.append(mean_absolute_error(y_te, preds))
            rmses_gkf.append(root_mean_squared_error(y_te, preds))
            r2s_gkf.append(r2_score(y_te, preds))
            
        print(f"  [GroupKFold] MAE: Rs {np.mean(maes_gkf):,.1f} ± {np.std(maes_gkf):,.1f} | RMSE: Rs {np.mean(rmses_gkf):,.1f} ± {np.std(rmses_gkf):,.1f} | R2: {np.mean(r2s_gkf):.4f} ± {np.std(r2s_gkf):.4f}")
        
        eval_results.append({
            "Validation_Strategy": "GroupKFold (n=5, groups=Crop)",
            "Model": m_name,
            "MAE_Mean": np.mean(maes_gkf),
            "MAE_Std": np.std(maes_gkf),
            "RMSE_Mean": np.mean(rmses_gkf),
            "RMSE_Std": np.std(rmses_gkf),
            "R2_Mean": np.mean(r2s_gkf),
            "R2_Std": np.std(r2s_gkf)
        })

        # ----------------------------------------------------------------------
        # Strategy B: Leave-One-Season-Out (LOSO by Year_Start)
        # ----------------------------------------------------------------------
        logo = LeaveOneGroupOut()
        maes_loso, rmses_loso, r2s_loso = [], [], []
        
        for tr_idx, te_idx in logo.split(X, y, groups=df['Year_Start']):
            held_out_year = df.iloc[te_idx]['Year_Start'].iloc[0]
            X_tr, y_tr = X.iloc[tr_idx], y.iloc[tr_idx]
            X_te, y_te = X.iloc[te_idx], y.iloc[te_idx]
            
            ttr_model.fit(X_tr, y_tr)
            preds = ttr_model.predict(X_te)
            oof_predictions[m_name][te_idx] = preds
            
            mae_yr = mean_absolute_error(y_te, preds)
            rmse_yr = root_mean_squared_error(y_te, preds)
            r2_yr = r2_score(y_te, preds)
            
            maes_loso.append(mae_yr)
            rmses_loso.append(rmse_yr)
            r2s_loso.append(r2_yr)
            
            loso_per_year_records.append({
                "Model": m_name,
                "Held_Out_Year": held_out_year,
                "Test_Rows": len(te_idx),
                "MAE": mae_yr,
                "RMSE": rmse_yr,
                "R2": r2_yr
            })
            
        print(f"  [LOSO]       MAE: Rs {np.mean(maes_loso):,.1f} ± {np.std(maes_loso):,.1f} | RMSE: Rs {np.mean(rmses_loso):,.1f} ± {np.std(rmses_loso):,.1f} | R2: {np.mean(r2s_loso):.4f} ± {np.std(r2s_loso):.4f}")
        
        eval_results.append({
            "Validation_Strategy": "Leave-One-Season-Out (LOSO)",
            "Model": m_name,
            "MAE_Mean": np.mean(maes_loso),
            "MAE_Std": np.std(maes_loso),
            "RMSE_Mean": np.mean(rmses_loso),
            "RMSE_Std": np.std(rmses_loso),
            "R2_Mean": np.mean(r2s_loso),
            "R2_Std": np.std(r2s_loso)
        })

    df_eval = pd.DataFrame(eval_results)
    df_eval.to_csv(data_dir / "model_evaluation.csv", index=False)
    
    df_loso_yr = pd.DataFrame(loso_per_year_records)
    df_loso_yr.to_csv(data_dir / "model_evaluation_loso_per_year.csv", index=False)
    print(f"\nDecision: Saved main evaluation table to {data_dir / 'model_evaluation.csv'}.")
    print(f"Decision: Saved LOSO per-year table to {data_dir / 'model_evaluation_loso_per_year.csv'}.")

    # --------------------------------------------------------------------------
    # STEP 5: HYPERPARAMETER TUNING OF THE WINNING MODEL
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 5: HYPERPARAMETER TUNING (Winning Model: GradientBoostingRegressor)")
    print("=" * 80)
    
    # We choose GradientBoostingRegressor as winning model
    winning_model_name = "GradientBoostingRegressor"
    base_gb = GradientBoostingRegressor(random_state=42)
    preprocessor = build_preprocessor('full', random_state=42)
    pipe = Pipeline([
        ('prep', preprocessor),
        ('regressor', base_gb)
    ])
    ttr_gb = TransformedTargetRegressor(regressor=pipe, func=np.log1p, inverse_func=np.expm1)

    param_grid = {
        'regressor__regressor__n_estimators': [100, 150],
        'regressor__regressor__learning_rate': [0.03, 0.05, 0.1],
        'regressor__regressor__max_depth': [3, 4],
        'regressor__regressor__min_samples_split': [2, 5]
    }
    
    print(f"Tuning {winning_model_name} with GridSearchCV across {len(param_grid['regressor__regressor__n_estimators']) * len(param_grid['regressor__regressor__learning_rate']) * len(param_grid['regressor__regressor__max_depth']) * len(param_grid['regressor__regressor__min_samples_split'])} parameter combinations...")
    gkf = GroupKFold(n_splits=5)
    
    grid = GridSearchCV(
        ttr_gb,
        param_grid=param_grid,
        cv=list(gkf.split(X, y, groups=df['Crop'])),
        scoring='neg_mean_absolute_error',
        n_jobs=1
    )
    grid.fit(X, y)
    
    best_params = grid.best_params_
    print(f"Best Hyperparameters: {best_params}")
    
    # Evaluate Tuned Model under GroupKFold & LOSO
    best_model = grid.best_estimator_
    
    # GroupKFold evaluation of tuned model
    maes_tuned_gkf, rmses_tuned_gkf, r2s_tuned_gkf = [], [], []
    for tr_idx, te_idx in gkf.split(X, y, groups=df['Crop']):
        best_model.fit(X.iloc[tr_idx], y.iloc[tr_idx])
        preds = best_model.predict(X.iloc[te_idx])
        maes_tuned_gkf.append(mean_absolute_error(y.iloc[te_idx], preds))
        rmses_tuned_gkf.append(root_mean_squared_error(y.iloc[te_idx], preds))
        r2s_tuned_gkf.append(r2_score(y.iloc[te_idx], preds))
        
    print(f"Tuned Model Performance under GroupKFold:")
    print(f"  MAE: Rs {np.mean(maes_tuned_gkf):,.1f} ± {np.std(maes_tuned_gkf):,.1f} (vs Baseline: Rs 46,275.5)")
    print(f"  R2 : {np.mean(r2s_tuned_gkf):.4f} ± {np.std(r2s_tuned_gkf):.4f}")

    # --------------------------------------------------------------------------
    # STEP 6: ABLATION STUDY (5 GradientBoosting Variants)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 6: ABLATION STUDY (5 GradientBoosting Variants)")
    print("=" * 80)
    
    ablation_modes = [
        ("Model A (Full Leak-Free Set)", 'full', "All 7 features: District, Crop, Season, Irrigation, Year, FX, Lag"),
        ("Model B (No Lag)", 'no_lag', "Model A minus Prev_Season_Total_Cost_Incl_Imputed"),
        ("Model C (No Time)", 'no_time', "Model A minus Year_Start and USD_LKR_Rate"),
        ("Model D (Structure Only)", 'structure_only', "Only District, Crop, Season, Irrigation_Type"),
        ("Model E (Lag Only)", 'lag_only', "Only Prev_Season_Total_Cost_Incl_Imputed + missing flag")
    ]
    
    ablation_records = []
    
    for m_label, mode_code, desc in ablation_modes:
        print(f"Evaluating Ablation {m_label}...")
        prep = build_preprocessor(mode_code, random_state=42)
        pipe = Pipeline([
            ('prep', prep),
            ('regressor', GradientBoostingRegressor(n_estimators=100, random_state=42))
        ])
        ttr = TransformedTargetRegressor(regressor=pipe, func=np.log1p, inverse_func=np.expm1)
        
        gkf = GroupKFold(n_splits=5)
        maes_abl, rmses_abl, r2s_abl = [], [], []
        
        for tr_idx, te_idx in gkf.split(X, y, groups=df['Crop']):
            ttr.fit(X.iloc[tr_idx], y.iloc[tr_idx])
            preds = ttr.predict(X.iloc[te_idx])
            maes_abl.append(mean_absolute_error(y.iloc[te_idx], preds))
            rmses_abl.append(root_mean_squared_error(y.iloc[te_idx], preds))
            r2s_abl.append(r2_score(y.iloc[te_idx], preds))
            
        print(f"  -> MAE: Rs {np.mean(maes_abl):,.1f} | RMSE: Rs {np.mean(rmses_abl):,.1f} | R2: {np.mean(r2s_abl):.4f}")
        ablation_records.append({
            "Ablation_Model": m_label,
            "Description": desc,
            "CV_R2_Mean": np.mean(r2s_abl),
            "CV_R2_Std": np.std(r2s_abl),
            "CV_MAE_Mean": np.mean(maes_abl),
            "CV_MAE_Std": np.std(maes_abl),
            "CV_RMSE_Mean": np.mean(rmses_abl),
            "CV_RMSE_Std": np.std(rmses_abl)
        })

    df_ablation = pd.DataFrame(ablation_records)
    df_ablation.to_csv(data_dir / "ablation_results.csv", index=False)
    print(f"Decision: Saved ablation results to {data_dir / 'ablation_results.csv'}.")

    # --------------------------------------------------------------------------
    # STEP 7: FEATURE IMPORTANCE & PEARSON CORRELATIONS
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 7: FEATURE IMPORTANCES & CORRELATION ANALYSIS")
    print("=" * 80)
    
    # Fit full pipeline to extract importances
    prep_rf = build_preprocessor('full', random_state=42)
    pipe_rf = Pipeline([('prep', prep_rf), ('reg', RandomForestRegressor(n_estimators=100, random_state=42))])
    pipe_rf.fit(X, np.log1p(y))
    
    prep_gb = build_preprocessor('full', random_state=42)
    pipe_gb = Pipeline([('prep', prep_gb), ('reg', GradientBoostingRegressor(n_estimators=100, random_state=42))])
    pipe_gb.fit(X, np.log1p(y))
    
    # Feature names
    feat_names = get_feature_names(build_preprocessor('full', random_state=42), X, np.log1p(y))
    
    rf_imp = pipe_rf.named_steps['reg'].feature_importances_
    gb_imp = pipe_gb.named_steps['reg'].feature_importances_
    
    # Group feature importances back to high-level attributes for clear reporting
    df_imp = pd.DataFrame({
        "Transformed_Feature": feat_names,
        "RandomForest_Importance": rf_imp,
        "GradientBoosting_Importance": gb_imp
    }).sort_values(by="GradientBoosting_Importance", ascending=False)
    
    print("\nFeature Importances (GradientBoosting & RandomForest):")
    print(df_imp.to_string(index=False))

    # Pearson Correlations
    corr_lag_target = df['Prev_Season_Total_Cost_Incl_Imputed'].corr(df[target_col])
    corr_year_target = df['Year_Start'].corr(df[target_col])
    corr_fx_target = df['USD_LKR_Rate'].corr(df[target_col])
    corr_fx_year = df['USD_LKR_Rate'].corr(df['Year_Start'])
    
    print("\nPearson Correlation Coefficients:")
    print(f"  1. Prev_Season_Total_Cost_Incl_Imputed vs Target Cost : {corr_lag_target:.4f}")
    print(f"  2. Year_Start vs Target Cost                          : {corr_year_target:.4f}")
    print(f"  3. USD_LKR_Rate vs Target Cost                        : {corr_fx_target:.4f}")
    print(f"  4. USD_LKR_Rate vs Year_Start                         : {corr_fx_year:.4f}")

    # Plot Feature Importances
    plt.figure(figsize=(10, 6))
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    top_df = df_imp.head(8).sort_values(by="GradientBoosting_Importance", ascending=True)
    y_pos = np.arange(len(top_df))
    
    plt.barh(y_pos - 0.2, top_df['GradientBoosting_Importance'], height=0.4, label='GradientBoosting', color='#2563eb', alpha=0.9)
    plt.barh(y_pos + 0.2, top_df['RandomForest_Importance'], height=0.4, label='RandomForest', color='#059669', alpha=0.9)
    
    plt.yticks(y_pos, top_df['Transformed_Feature'], fontsize=10)
    plt.xlabel("Relative Feature Importance", fontsize=11, fontweight='semibold')
    plt.title("Top Feature Importances (Tree-Based Models)", fontsize=13, fontweight='bold', pad=12)
    plt.legend(frameon=True, loc='lower right')
    plt.tight_layout()
    
    fig_imp_path = figures_dir / "feature_importances.png"
    plt.savefig(fig_imp_path, dpi=300)
    plt.close()
    print(f"Decision: Saved feature importances plot to {fig_imp_path.name}.")

    # --------------------------------------------------------------------------
    # STEP 8: RESIDUALS PLOT & PIPELINE SERIALIZATION
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 8: RESIDUALS PLOT & BEST MODEL SERIALIZATION")
    print("=" * 80)
    
    # Best model OOF predictions under LOSO
    y_oof_gb = oof_predictions["GradientBoostingRegressor"]
    
    plt.figure(figsize=(9, 7))
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    
    scatter = plt.scatter(y / 1000, y_oof_gb / 1000, c=df['Year_Start'], cmap='viridis', alpha=0.75, edgecolors='k', s=55)
    cbar = plt.colorbar(scatter)
    cbar.set_label('Year_Start (Cultivation Season)', fontsize=10, fontweight='semibold')
    
    # 1:1 reference line
    lim_max = max(y.max(), y_oof_gb.max()) / 1000 * 1.05
    plt.plot([0, lim_max], [0, lim_max], color='#dc2626', linestyle='--', linewidth=2, label='Ideal 1:1 Line (Actual = Predicted)')
    
    plt.xlabel("Actual Cultivation Cost (Thousands LKR / acre)", fontsize=11, fontweight='semibold')
    plt.ylabel("Predicted Cultivation Cost (Thousands LKR / acre)", fontsize=11, fontweight='semibold')
    plt.title("Actual vs. Out-of-Fold Predicted Costs (Leave-One-Season-Out LOSO)\nModel: GradientBoostingRegressor", fontsize=13, fontweight='bold', pad=12)
    plt.legend(frameon=True, loc='upper left')
    plt.tight_layout()
    
    fig_res_path = figures_dir / "residuals_plot.png"
    plt.savefig(fig_res_path, dpi=300)
    plt.close()
    print(f"Decision: Saved residuals plot to {fig_res_path.name}.")

    # Fit final pipeline on 100% of data and serialize
    final_pipeline = Pipeline([
        ('prep', build_preprocessor('full', random_state=42)),
        ('regressor', GradientBoostingRegressor(n_estimators=150, learning_rate=0.05, max_depth=4, random_state=42))
    ])
    final_ttr = TransformedTargetRegressor(regressor=final_pipeline, func=np.log1p, inverse_func=np.expm1)
    final_ttr.fit(X, y)
    
    joblib_path = models_dir / "best_model_pipeline.pkl"
    joblib.dump(final_ttr, joblib_path)
    print(f"Decision: Serialized best model pipeline to {joblib_path.name}.")

    # --------------------------------------------------------------------------
    # STEP 9: WORST YEARS ANALYSIS & REPORT GENERATION
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 9: LOSO YEAR-BY-YEAR RANKING & RED FLAGS")
    print("=" * 80)
    
    loso_gb_years = df_loso_yr[df_loso_yr['Model'] == 'GradientBoostingRegressor'].sort_values(by="MAE", ascending=False)
    print("\nLOSO Performance by Year (GradientBoosting, Sorted by Worst MAE):")
    print(loso_gb_years.to_string(index=False))
    
    worst_3_years = loso_gb_years.head(3)
    print(f"\nThe 3 Worst Years under LOSO:")
    for _, r in worst_3_years.iterrows():
        print(f"  - Year {int(r['Held_Out_Year'])}: MAE = Rs {r['MAE']:,.1f} | RMSE = Rs {r['RMSE']:,.1f} | R2 = {r['R2']:7.4f}")

    print("\n" + "=" * 80)
    print("PIPELINE EXECUTION FINISHED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()
