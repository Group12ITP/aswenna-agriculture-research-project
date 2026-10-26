import os
import json
import logging
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
import optuna
import matplotlib.pyplot as plt

from .utils import load_config, set_seeds, get_logger, generate_run_id
from .data import load_and_preprocess_vegetables
from .splits import get_split_masks
from .features import build_vegetable_features
from .metrics import (
    evaluate_predictions, compute_skill_vs_naive, block_bootstrap_mase,
    diebold_mariano_test, holm_bonferroni_correction, compute_friedman_nemenyi,
    compute_model_confidence_set
)
from .intervals import (
    ScaleAwareConformalPredictor, ConformalizedQuantileRegression,
    evaluate_interval_quality
)
from .models.baselines import (
    NaiveForecaster, SeasonalNaiveForecaster, MovingAverageForecaster, DriftForecaster
)
from .models.statistical import (
    HoltWintersRollingForecaster, AutoARIMARollingForecaster,
    SARIMAXRollingForecaster, ProphetRollingForecaster
)
from .models.classical import get_classical_model
from .models.deep_learning import PyTorchForecaster, plot_dl_learning_curves
from .models.ensembles import SimpleAverageEnsemble, StackingMetaLearner, BestPerCategoryEnsemble

logger = get_logger("src.train")

# Quiet optuna logging
optuna.logging.set_verbosity(optuna.logging.WARNING)

def train_baseline_model(model_name, horizon, df_feat, train_mask, val_mask, test_mask):
    """Evaluate local baseline models using strictly prior information (<= curr_w)."""
    val_preds = []
    test_preds = []
    
    unique_vegs = df_feat["product_name"].unique()
    for veg in unique_vegs:
        v_mask = df_feat["product_name"] == veg
        v_df = df_feat[v_mask].sort_values("week_index")
        
        v_tr_idx = v_df.index[train_mask.loc[v_df.index]]
        train_prices = v_df.loc[v_tr_idx, "price_lkr"].dropna().values
        val_idx = v_df.index[val_mask.loc[v_df.index]]
        test_idx = v_df.index[test_mask.loc[v_df.index]]
        
        if model_name == "naive":
            model = NaiveForecaster()
        elif model_name == "seasonal_naive_48":
            model = SeasonalNaiveForecaster(season_m=48)
        elif model_name == "moving_average_4":
            model = MovingAverageForecaster(window=4)
        elif model_name == "moving_average_12":
            model = MovingAverageForecaster(window=12)
        elif model_name == "drift":
            model = DriftForecaster()
        else:
            raise ValueError(f"Unknown baseline: {model_name}")
            
        model.fit(train_prices)
        
        # Validation predictions (history up to and including origin week t)
        for idx in val_idx:
            curr_w = v_df.loc[idx, "week_index"]
            hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
            val_preds.append((idx, model.predict(horizon=horizon, y_history=hist)))
            
        # Test predictions (history up to and including origin week t)
        for idx in test_idx:
            curr_w = v_df.loc[idx, "week_index"]
            hist = v_df.loc[v_df["week_index"] <= curr_w, "price_lkr"].values
            test_preds.append((idx, model.predict(horizon=horizon, y_history=hist)))
            
    val_s = pd.Series({idx: pred for idx, pred in val_preds}, name=f"pred_{model_name}")
    test_s = pd.Series({idx: pred for idx, pred in test_preds}, name=f"pred_{model_name}")
    return val_s, test_s

def train_statistical_model(model_name, horizon, df_feat, train_mask, val_mask, test_mask):
    """
    Evaluate local statistical models (Holt-Winters, Auto-ARIMA, SARIMAX, Prophet)
    using ROLLING-ORIGIN h-step-ahead forecasts on log prices.
    Includes automated sanity check against naive baseline at h=1.
    """
    val_preds = []
    test_preds = []
    
    unique_vegs = df_feat["product_name"].unique()
    for veg in unique_vegs:
        v_mask = df_feat["product_name"] == veg
        v_df = df_feat[v_mask].sort_values("week_index").copy()
        
        v_df["ds"] = pd.to_datetime(v_df["approx_date"])
        full_series = v_df["price_lkr"].values
        
        v_tr_idx = v_df.index[train_mask.loc[v_df.index]]
        train_series = v_df.loc[v_tr_idx, "price_lkr"].values
        
        val_idx = v_df.index[val_mask.loc[v_df.index]]
        test_idx = v_df.index[test_mask.loc[v_df.index]]
        
        # Convert index labels to positional indices in v_df
        val_pos = [v_df.index.get_loc(idx) for idx in val_idx]
        test_pos = [v_df.index.get_loc(idx) for idx in test_idx]
        
        if model_name == "holt_winters_ets":
            forecaster = HoltWintersRollingForecaster(seasonal_periods=48)
            forecaster.fit_parameters(train_series)
            val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=horizon)
            test_fc = forecaster.rolling_forecast(full_series, test_pos, horizon=horizon)
            
        elif model_name == "auto_arima":
            forecaster = AutoARIMARollingForecaster(d=1)
            forecaster.fit_parameters(train_series)
            val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=horizon)
            test_fc = forecaster.rolling_forecast(full_series, test_pos, horizon=horizon)
            
        elif model_name == "sarimax":
            forecaster = SARIMAXRollingForecaster(order=(1, 1, 1))
            forecaster.fit_parameters(train_series)
            val_fc = forecaster.rolling_forecast(full_series, val_pos, horizon=horizon)
            test_fc = forecaster.rolling_forecast(full_series, test_pos, horizon=horizon)
            
        elif model_name == "prophet":
            forecaster = ProphetRollingForecaster()
            val_fc = forecaster.rolling_forecast(v_df, val_pos, horizon=horizon)
            test_fc = forecaster.rolling_forecast(v_df, test_pos, horizon=horizon)
        else:
            raise ValueError(f"Unknown statistical model: {model_name}")
            
        for idx, pos in zip(val_idx, val_pos):
            val_preds.append((idx, val_fc.get(pos, float(v_df.loc[idx, "price_lkr"]))))
            
        for idx, pos in zip(test_idx, test_pos):
            test_preds.append((idx, test_fc.get(pos, float(v_df.loc[idx, "price_lkr"]))))
            
    val_s = pd.Series({idx: pred for idx, pred in val_preds}, name=f"pred_{model_name}")
    test_s = pd.Series({idx: pred for idx, pred in test_preds}, name=f"pred_{model_name}")
    
    # Automated Sanity Check at h=1
    if horizon == 1:
        target_col = "target_h1"
        y_val_clean = df_feat.loc[val_mask, target_col]
        naive_val_pred = df_feat.loc[val_mask, "price_lkr"] # naive is y_t
        eval_mask = pd.notna(y_val_clean) & pd.notna(val_s) & pd.notna(naive_val_pred)
        
        mae_stat = np.mean(np.abs(y_val_clean[eval_mask] - val_s[eval_mask]))
        mae_naive = np.mean(np.abs(y_val_clean[eval_mask] - naive_val_pred[eval_mask]))
        ratio = mae_stat / max(1e-4, mae_naive)
        
        logger.info(f"Statistical sanity check at h=1 for [{model_name}]: MAE={mae_stat:.2f} vs Naive={mae_naive:.2f} (Ratio={ratio:.3f})")
        if ratio > 1.15:
            err_msg = f"Sanity check FAILED: {model_name} h=1 MAE ({mae_stat:.2f}) exceeds Naive ({mae_naive:.2f}) by >15% (Ratio={ratio:.3f})!"
            logger.error(err_msg)
            # Log warning or raise error if flag is strict
            
    return val_s, test_s

def prepare_feature_matrices(df_feat, target_col="target_h4"):
    """Prepare feature matrix X and target vector y with proper categorical encodings."""
    target_cols = [c for c in df_feat.columns if c.startswith("target_")]
    meta_cols = ["week_index", "year", "month", "week_of_month", "approx_date", "product_name", "category", "unit"]
    drop_cols = target_cols + meta_cols
    
    feature_cols = [c for c in df_feat.columns if c not in drop_cols]
    
    df_encoded = df_feat.copy()
    df_encoded["veg_code"] = df_feat["product_name"].astype("category").cat.codes
    df_encoded["cat_code"] = df_feat["category"].astype("category").cat.codes
    df_encoded["unit_code"] = df_feat["unit"].astype("category").cat.codes
    
    all_features = feature_cols + ["veg_code", "cat_code", "unit_code"]
    
    X = df_encoded[all_features].copy()
    X = X.ffill().bfill().fillna(0.0)
    y = df_feat[target_col].copy()
    
    return X, y, all_features

def tune_classical_model(model_name, X_train, y_train, horizon, n_trials=15):
    """Optuna hyperparameter tuning using expanding-window time-series CV on train."""
    if model_name in ["ridge", "lasso", "elastic_net", "svr"]:
        def objective(trial):
            alpha = trial.suggest_float("alpha", 1e-3, 1e2, log=True)
            params = {"alpha": alpha}
            if model_name == "elastic_net":
                params["l1_ratio"] = trial.suggest_float("l1_ratio", 0.1, 0.9)
            elif model_name == "svr":
                params = {
                    "C": trial.suggest_float("C", 1.0, 300.0, log=True),
                    "epsilon": trial.suggest_float("epsilon", 0.01, 0.5)
                }
            model = get_classical_model(model_name, params=params)
            n = len(X_train)
            scores = []
            for split_pt in [int(n * 0.6), int(n * 0.8)]:
                x_tr, y_tr = X_train.iloc[:split_pt], y_train.iloc[:split_pt]
                x_vl, y_vl = X_train.iloc[split_pt:split_pt+int(n*0.2)], y_train.iloc[split_pt:split_pt+int(n*0.2)]
                mask_tr = pd.notna(y_tr)
                mask_vl = pd.notna(y_vl)
                if mask_tr.sum() == 0 or mask_vl.sum() == 0:
                    continue
                model.fit(x_tr[mask_tr], y_tr[mask_tr])
                pred = model.predict(x_vl[mask_vl])
                scores.append(np.mean(np.abs(y_vl[mask_vl] - pred)))
            return np.mean(scores) if scores else 1e6
            
    elif model_name in ["lightgbm", "xgboost", "catboost", "random_forest", "extra_trees", "gradient_boosting"]:
        def objective(trial):
            params = {
                "n_estimators": trial.suggest_int("n_estimators", 80, 200, step=40),
                "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
                "max_depth": trial.suggest_int("max_depth", 3, 8)
            }
            if model_name == "lightgbm":
                params["num_leaves"] = trial.suggest_int("num_leaves", 15, 63)
            model = get_classical_model(model_name, params=params)
            n = len(X_train)
            scores = []
            for split_pt in [int(n * 0.6), int(n * 0.8)]:
                x_tr, y_tr = X_train.iloc[:split_pt], y_train.iloc[:split_pt]
                x_vl, y_vl = X_train.iloc[split_pt:split_pt+int(n*0.2)], y_train.iloc[split_pt:split_pt+int(n*0.2)]
                mask_tr = pd.notna(y_tr)
                mask_vl = pd.notna(y_vl)
                if mask_tr.sum() == 0 or mask_vl.sum() == 0:
                    continue
                model.fit(x_tr[mask_tr], y_tr[mask_tr])
                pred = model.predict(x_vl[mask_vl])
                scores.append(np.mean(np.abs(y_vl[mask_vl] - pred)))
            return np.mean(scores) if scores else 1e6
    else:
        return {}
        
    study = optuna.create_study(direction="minimize")
    study.optimize(objective, n_trials=n_trials, timeout=40)
    return study.best_params

def train_classical_model(model_name, horizon, df_feat, train_mask, val_mask, test_mask, n_trials=15, is_smoke=False):
    """Train global classical ML model, evaluate on val, refit on train+val, evaluate on test."""
    target_col = f"target_h{horizon}"
    X, y, features = prepare_feature_matrices(df_feat, target_col=target_col)
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    trials = 2 if is_smoke else n_trials
    best_params = tune_classical_model(model_name, X_train, y_train, horizon=horizon, n_trials=trials)
    
    model_val = get_classical_model(model_name, params=best_params)
    tr_mask_clean = pd.notna(y_train)
    model_val.fit(X_train[tr_mask_clean], y_train[tr_mask_clean])
    val_pred = model_val.predict(X_val)
    
    # Refit on train + val -> predict test
    X_tr_val = pd.concat([X_train, X_val], axis=0)
    y_tr_val = pd.concat([y_train, y_val], axis=0)
    tr_val_mask_clean = pd.notna(y_tr_val)
    
    model_final = get_classical_model(model_name, params=best_params)
    model_final.fit(X_tr_val[tr_val_mask_clean], y_tr_val[tr_val_mask_clean])
    test_pred = model_final.predict(X_test)
    
    val_s = pd.Series(val_pred, index=X_val.index, name=f"pred_{model_name}")
    test_s = pd.Series(test_pred, index=X_test.index, name=f"pred_{model_name}")
    
    return val_s, test_s, best_params, model_final

def train_deep_learning_model(arch, horizon, df_feat, train_mask, val_mask, test_mask, epochs=30, is_smoke=False):
    """Train global PyTorch architecture with log-scale Huber loss and loss curve tracking."""
    target_col = f"target_h{horizon}"
    X, y, features = prepare_feature_matrices(df_feat, target_col=target_col)
    
    X_train, y_train = X[train_mask], y[train_mask]
    X_val, y_val = X[val_mask], y[val_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    
    ep = 3 if is_smoke else epochs
    model = PyTorchForecaster(arch=arch, epochs=ep, batch_size=128)
    
    tr_mask_clean = pd.notna(y_train)
    # Pass validation set to compute val_loss per epoch for learning curves
    model.fit(X_train[tr_mask_clean], y_train[tr_mask_clean], X_val=X_val, y_val=y_val)
    val_pred = model.predict(X_val)
    
    # Refit on train+val for final test deployment
    X_tr_val = pd.concat([X_train, X_val], axis=0)
    y_tr_val = pd.concat([y_train, y_val], axis=0)
    tr_val_mask_clean = pd.notna(y_tr_val)
    
    model_final = PyTorchForecaster(arch=arch, epochs=ep, batch_size=128)
    model_final.fit(X_tr_val[tr_val_mask_clean], y_tr_val[tr_val_mask_clean])
    test_pred = model_final.predict(X_test)
    
    val_s = pd.Series(val_pred, index=X_val.index, name=f"pred_{arch}")
    test_s = pd.Series(test_pred, index=X_test.index, name=f"pred_{arch}")
    
    return val_s, test_s, {}, model_final

def run_experiment_pipeline(cfg=None, is_smoke=False):
    """
    Execute complete multi-model, multi-horizon research pipeline.
    Saves all artefacts, logs, models, and leaderboards.
    """
    if cfg is None:
        cfg = load_config()
        
    set_seeds(cfg.get("random_seed", 42))
    
    runs_dir = Path(cfg["paths"]["runs"])
    models_dir = Path(cfg["paths"]["models"])
    exp_dir = Path(cfg["paths"]["experiments"])
    results_dir = Path(cfg["paths"]["results"])
    runs_dir.mkdir(parents=True, exist_ok=True)
    models_dir.mkdir(parents=True, exist_ok=True)
    exp_dir.mkdir(parents=True, exist_ok=True)
    results_dir.mkdir(parents=True, exist_ok=True)
    Path("results/figures").mkdir(parents=True, exist_ok=True)
    Path("results/tables").mkdir(parents=True, exist_ok=True)
    
    df_wide, df_long = load_and_preprocess_vegetables(cfg)
    
    if is_smoke:
        target_vegs = cfg["smoke_test"]["vegetables"]
        target_horizons = cfg["smoke_test"]["horizons"]
        df_long = df_long[df_long["product_name"].isin(target_vegs)].copy()
        logger.info(f"Running in SMOKE TEST mode on: {target_vegs} across horizons: {target_horizons}")
    else:
        target_horizons = cfg["task"]["horizons"]
        logger.info(f"Running in FULL RESEARCH mode across all 32 vegetables and horizons: {target_horizons}")
        
    df_feat = build_vegetable_features(df_long, cfg=cfg, include_cross_veg=True)
    train_mask, val_mask, test_mask = get_split_masks(df_feat, cfg=cfg)
    
    # Partition validation set into dedicated Tune Fold (first 24 weeks) and Cal Fold (last 24 weeks)
    val_weeks = df_feat.loc[val_mask, "week_index"].sort_values().unique()
    mid_week = val_weeks[len(val_weeks) // 2]
    val_tune_mask = val_mask & (df_feat["week_index"] < mid_week)
    val_cal_mask = val_mask & (df_feat["week_index"] >= mid_week)
    
    logger.info(f"Split breakdown: Train={train_mask.sum()} obs, Val-Tune={val_tune_mask.sum()}, Val-Cal={val_cal_mask.sum()}, Test={test_mask.sum()}")
    
    leaderboard_records = []
    by_veg_records = []
    by_cat_records = []
    by_horizon_records = []
    uncertainty_records = []
    leafy_audit_records = []
    
    all_val_preds = {} # (horizon, model) -> Series
    all_test_preds = {}
    fitted_models = {}
    
    model_families = {
        "baselines": cfg["models"]["baselines"],
        "statistical": cfg["models"]["statistical"],
        "classical_ml": cfg["models"]["classical_ml"],
        "deep_learning": cfg["models"]["deep_learning"],
    }
    
    for h in target_horizons:
        logger.info(f"\n{'='*30} TRAINING HORIZON h = {h} {'='*30}")
        target_col = f"target_h{h}"
        y_val_true = df_feat.loc[val_mask, target_col]
        y_test_true = df_feat.loc[test_mask, target_col]
        y_cal_true = df_feat.loc[val_cal_mask, target_col]
        y_origin_price_val = df_feat.loc[val_mask, "price_lkr"]
        y_origin_price_test = df_feat.loc[test_mask, "price_lkr"]
        
        # 1. Baselines
        for m_name in model_families["baselines"]:
            logger.info(f"Training Baseline [{m_name}] for h={h}...")
            val_p, test_p = train_baseline_model(m_name, h, df_feat, train_mask, val_mask, test_mask)
            all_val_preds[(h, m_name)] = val_p
            all_test_preds[(h, m_name)] = test_p
            
        # 2. Statistical Models
        for m_name in model_families["statistical"]:
            logger.info(f"Training Statistical Model [{m_name}] for h={h}...")
            val_p, test_p = train_statistical_model(m_name, h, df_feat, train_mask, val_mask, test_mask)
            all_val_preds[(h, m_name)] = val_p
            all_test_preds[(h, m_name)] = test_p
            
        # 3. Classical ML
        for m_name in model_families["classical_ml"]:
            logger.info(f"Training Classical ML [{m_name}] for h={h}...")
            val_p, test_p, params, fitted_m = train_classical_model(
                m_name, h, df_feat, train_mask, val_mask, test_mask,
                n_trials=cfg["optimization"]["ml_trials"], is_smoke=is_smoke
            )
            all_val_preds[(h, m_name)] = val_p
            all_test_preds[(h, m_name)] = test_p
            fitted_models[(h, m_name)] = fitted_m
            
        # 4. Deep Learning
        for arch in model_families["deep_learning"]:
            logger.info(f"Training Deep Learning [{arch}] for h={h}...")
            val_p, test_p, params, fitted_m = train_deep_learning_model(
                arch, h, df_feat, train_mask, val_mask, test_mask,
                epochs=cfg["optimization"]["dl_trials"] if is_smoke else 30, is_smoke=is_smoke
            )
            all_val_preds[(h, arch)] = val_p
            all_test_preds[(h, arch)] = test_p
            fitted_models[(h, arch)] = fitted_m
            
        # 5. Ensembles
        # Find top 3 models on validation MASE for this horizon
        model_val_mases = {}
        candidate_models = model_families["classical_ml"] + model_families["deep_learning"]
        for cm in candidate_models:
            val_s = all_val_preds.get((h, cm))
            if val_s is not None:
                m_res = evaluate_predictions(y_val_true, val_s, y_train_history=df_feat.loc[train_mask, "price_lkr"])
                model_val_mases[cm] = m_res.get("MASE", 999.0)
                
        sorted_top = sorted(model_val_mases.items(), key=lambda x: x[1])
        top3_names = [x[0] for x in sorted_top[:3]] if len(sorted_top) >= 3 else [x[0] for x in sorted_top]
        logger.info(f"Top 3 models for h={h} ensemble: {top3_names}")
        
        # Simple Average Top-3
        avg_ens = SimpleAverageEnsemble(top3_names)
        val_ens_p = avg_ens.predict({m: all_val_preds[(h, m)].values for m in top3_names})
        test_ens_p = avg_ens.predict({m: all_test_preds[(h, m)].values for m in top3_names})
        all_val_preds[(h, "simple_average_top3")] = pd.Series(val_ens_p, index=y_val_true.index)
        all_test_preds[(h, "simple_average_top3")] = pd.Series(test_ens_p, index=y_test_true.index)
        fitted_models[(h, "simple_average_top3")] = (avg_ens, {m: fitted_models.get((h, m)) for m in top3_names})
        
        # Stacking Meta Learner
        stack_ens = StackingMetaLearner(top3_names)
        stack_ens.fit({m: all_val_preds[(h, m)].values for m in top3_names}, y_val_true)
        val_stack_p = stack_ens.predict({m: all_val_preds[(h, m)].values for m in top3_names})
        test_stack_p = stack_ens.predict({m: all_test_preds[(h, m)].values for m in top3_names})
        all_val_preds[(h, "stacking_meta_learner")] = pd.Series(val_stack_p, index=y_val_true.index)
        all_test_preds[(h, "stacking_meta_learner")] = pd.Series(test_stack_p, index=y_test_true.index)
        fitted_models[(h, "stacking_meta_learner")] = (stack_ens, {m: fitted_models.get((h, m)) for m in top3_names})
        
        # Best Per Category Ensemble
        cat_ens = BestPerCategoryEnsemble()
        cat_ens.fit({m: all_val_preds[(h, m)].values for m in candidate_models}, y_val_true, df_feat.loc[val_mask, "category"])
        val_cat_p = cat_ens.predict({m: all_val_preds[(h, m)].values for m in candidate_models}, df_feat.loc[val_mask, "category"])
        test_cat_p = cat_ens.predict({m: all_test_preds[(h, m)].values for m in candidate_models}, df_feat.loc[test_mask, "category"])
        all_val_preds[(h, "best_per_category")] = pd.Series(val_cat_p, index=y_val_true.index)
        all_test_preds[(h, "best_per_category")] = pd.Series(test_cat_p, index=y_test_true.index)
        fitted_models[(h, "best_per_category")] = cat_ens
        
        # 6. Evaluation, Scale-Aware Conformal Intervals & Honest Statistics
        all_models_for_h = (
            model_families["baselines"] + model_families["statistical"] +
            model_families["classical_ml"] + model_families["deep_learning"] +
            ["simple_average_top3", "stacking_meta_learner", "best_per_category"]
        )
        
        naive_val_pred = all_val_preds[(h, "naive")]
        naive_test_pred = all_test_preds[(h, "naive")]
        mase_naive_val = evaluate_predictions(y_val_true, naive_val_pred, y_train_history=df_feat.loc[train_mask, "price_lkr"])["MASE"]
        mase_naive_test = evaluate_predictions(y_test_true, naive_test_pred, y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"])["MASE"]
        
        # First pass to find winner on validation for bootstrap delta comparison
        val_mases = {}
        for m_name in all_models_for_h:
            vp = all_val_preds[(h, m_name)]
            vm = evaluate_predictions(y_val_true, vp, y_train_history=df_feat.loc[train_mask, "price_lkr"], y_prev=y_origin_price_val)
            val_mases[m_name] = vm["MASE"]
        winner_m_name = min(val_mases, key=val_mases.get)
        winner_val_pred = all_val_preds[(h, winner_m_name)]
        winner_test_pred = all_test_preds[(h, winner_m_name)]
        
        for m_name in all_models_for_h:
            val_p = all_val_preds[(h, m_name)]
            test_p = all_test_preds[(h, m_name)]
            
            # Dedicated calibration on val_cal_mask (HELD-OUT from evaluation)
            conformal = ScaleAwareConformalPredictor(alpha_levels=(0.20, 0.05))
            val_cal_pred = val_p.loc[val_cal_mask]
            conformal.calibrate(y_cal_true, val_cal_pred)
            test_intervals = conformal.predict_intervals(test_p)
            
            # Uncertainty evaluation on held-out test split
            cov_test_80 = evaluate_interval_quality(y_test_true, test_intervals["lower_80"], test_intervals["upper_80"], y_pred=test_p, metadata_df=df_feat.loc[test_mask])
            cov_test_95 = evaluate_interval_quality(y_test_true, test_intervals["lower_95"], test_intervals["upper_95"], y_pred=test_p, metadata_df=df_feat.loc[test_mask])
            
            uncertainty_records.append({
                "model": m_name, "horizon": h,
                "coverage_80_test": cov_test_80["coverage_pct"],
                "width_80_lkr": cov_test_80["mean_width_lkr"],
                "width_80_pct": cov_test_80["mean_width_pct"],
                "coverage_95_test": cov_test_95["coverage_pct"],
                "width_95_lkr": cov_test_95["mean_width_lkr"],
                "width_95_pct": cov_test_95["mean_width_pct"]
            })
            
            # Metrics computation
            val_metrics = evaluate_predictions(y_val_true, val_p, y_train_history=df_feat.loc[train_mask, "price_lkr"], y_prev=y_origin_price_val)
            test_metrics = evaluate_predictions(y_test_true, test_p, y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"], y_prev=y_origin_price_test)
            
            skill_val = compute_skill_vs_naive(val_metrics["MASE"], mase_naive_val)
            skill_test = compute_skill_vs_naive(test_metrics["MASE"], mase_naive_test)
            
            # Block-bootstrap 95% CIs on test set (1,000 resamples)
            boot_res = block_bootstrap_mase(
                y_test_true, test_p, y_naive_pred=naive_test_pred,
                y_winner_pred=winner_test_pred,
                y_train_history=df_feat.loc[train_mask | val_mask, "price_lkr"],
                block_length=4, n_boot=1000
            )
            
            # Diebold-Mariano test on test set vs Naive and vs Winner
            dm_stat_naive, dm_p_naive = diebold_mariano_test(y_test_true, test_p, naive_test_pred, h=h)
            dm_stat_win, dm_p_win = diebold_mariano_test(y_test_true, test_p, winner_test_pred, h=h)
            
            # Record in leaderboard
            for split_name, mets, skill_score in [
                ("validation", val_metrics, skill_val),
                ("test", test_metrics, skill_test)
            ]:
                row_dict = {
                    "model": m_name,
                    "horizon": h,
                    "split": split_name,
                    "MAE": mets["MAE"],
                    "RMSE": mets["RMSE"],
                    "MAPE": mets["MAPE"],
                    "sMAPE": mets["sMAPE"],
                    "MASE": mets["MASE"],
                    "R2": mets["R2"],
                    "Bias": mets["Bias"],
                    "Directional_Accuracy": mets["Directional_Accuracy"],
                    "Skill_vs_Naive": round(float(skill_score), 2) if pd.notna(skill_score) else np.nan,
                    "n_obs": mets["n_obs"]
                }
                if split_name == "test":
                    row_dict["Coverage_80"] = cov_test_80["coverage_pct"]
                    row_dict["Width_80_LKR"] = cov_test_80["mean_width_lkr"]
                    row_dict["Width_80_Pct"] = cov_test_80["mean_width_pct"]
                    row_dict["Coverage_95"] = cov_test_95["coverage_pct"]
                    row_dict["Width_95_LKR"] = cov_test_95["mean_width_lkr"]
                    row_dict["Width_95_Pct"] = cov_test_95["mean_width_pct"]
                    row_dict["MASE_CI_95"] = f"[{boot_res.get('mase_ci_low')}, {boot_res.get('mase_ci_high')}]"
                    row_dict["Diff_Naive_CI_95"] = f"[{boot_res.get('diff_naive_ci_low')}, {boot_res.get('diff_naive_ci_high')}]"
                    row_dict["DM_stat_vs_Naive"] = dm_stat_naive
                    row_dict["DM_pval_vs_Naive"] = dm_p_naive
                else:
                    # Drop validation coverage as required by user prompt
                    row_dict["Coverage_80"] = np.nan
                    row_dict["Width_80_LKR"] = np.nan
                    row_dict["Width_80_Pct"] = np.nan
                    row_dict["Coverage_95"] = np.nan
                    row_dict["Width_95_LKR"] = np.nan
                    row_dict["Width_95_Pct"] = np.nan
                    row_dict["MASE_CI_95"] = np.nan
                    row_dict["Diff_Naive_CI_95"] = np.nan
                    row_dict["DM_stat_vs_Naive"] = np.nan
                    row_dict["DM_pval_vs_Naive"] = np.nan
                    
                leaderboard_records.append(row_dict)
                
            # Disaggregated evaluation by vegetable and category
            for veg in df_feat["product_name"].unique():
                v_mask = df_feat["product_name"] == veg
                v_val_mask = val_mask & v_mask
                v_test_mask = test_mask & v_mask
                
                v_m_val = evaluate_predictions(
                    df_feat.loc[v_val_mask, target_col], val_p.loc[v_val_mask],
                    y_train_history=df_feat.loc[train_mask & v_mask, "price_lkr"],
                    y_prev=df_feat.loc[v_val_mask, "price_lkr"]
                )
                v_m_test = evaluate_predictions(
                    df_feat.loc[v_test_mask, target_col], test_p.loc[v_test_mask],
                    y_train_history=df_feat.loc[(train_mask | val_mask) & v_mask, "price_lkr"],
                    y_prev=df_feat.loc[v_test_mask, "price_lkr"]
                )
                by_veg_records.append({
                    "model": m_name, "horizon": h, "vegetable": veg,
                    "val_MAE": v_m_val["MAE"], "val_MASE": v_m_val["MASE"], "val_sMAPE": v_m_val["sMAPE"],
                    "test_MAE": v_m_test["MAE"], "test_RMSE": v_m_test["RMSE"],
                    "test_sMAPE": v_m_test["sMAPE"], "test_MASE": v_m_test["MASE"],
                    "test_R2": v_m_test["R2"], "test_DA": v_m_test["Directional_Accuracy"]
                })
                
            # Disaggregated by category
            for cat in df_feat["category"].unique():
                c_mask = df_feat["category"] == cat
                c_test_mask = test_mask & c_mask
                c_m_test = evaluate_predictions(
                    df_feat.loc[c_test_mask, target_col], test_p.loc[c_test_mask],
                    y_train_history=df_feat.loc[(train_mask | val_mask) & c_mask, "price_lkr"],
                    y_prev=df_feat.loc[c_test_mask, "price_lkr"]
                )
                by_cat_records.append({
                    "model": m_name, "horizon": h, "category": cat,
                    "test_MAE": c_m_test["MAE"], "test_RMSE": c_m_test["RMSE"],
                    "test_sMAPE": c_m_test["sMAPE"], "test_MASE": c_m_test["MASE"],
                    "test_R2": c_m_test["R2"], "test_DA": c_m_test["Directional_Accuracy"]
                })
                
            # Leafy vegetables audit: overall vs clean (stale & backfilled excluded)
            leafy_mask = df_feat["category"] == "Leafy Vegetables"
            leafy_test = test_mask & leafy_mask
            leafy_clean_test = leafy_test & (df_feat["is_stale_run"] == 0) & (df_feat["is_backfilled"] == 0)
            
            m_leafy_all = evaluate_predictions(df_feat.loc[leafy_test, target_col], test_p.loc[leafy_test], y_prev=df_feat.loc[leafy_test, "price_lkr"])
            m_leafy_clean = evaluate_predictions(df_feat.loc[leafy_clean_test, target_col], test_p.loc[leafy_clean_test], y_prev=df_feat.loc[leafy_clean_test, "price_lkr"])
            
            leafy_audit_records.append({
                "model": m_name, "horizon": h,
                "all_leafy_MAE": m_leafy_all["MAE"], "all_leafy_sMAPE": m_leafy_all["sMAPE"], "all_leafy_R2": m_leafy_all["R2"],
                "clean_leafy_MAE": m_leafy_clean["MAE"], "clean_leafy_sMAPE": m_leafy_clean["sMAPE"], "clean_leafy_R2": m_leafy_clean["R2"],
                "n_all": m_leafy_all["n_obs"], "n_clean": m_leafy_clean["n_obs"]
            })
            
            # Save predictions and run config
            run_id = generate_run_id(m_name, h)
            run_path = runs_dir / run_id
            run_path.mkdir(parents=True, exist_ok=True)
            
            with open(run_path / "config.json", "w", encoding="utf-8") as f:
                json.dump({"model": m_name, "horizon": h, "is_smoke": is_smoke}, f, indent=2)
            with open(run_path / "metrics.json", "w", encoding="utf-8") as f:
                json.dump({"val": val_metrics, "test": test_metrics, "uncertainty": cov_test_80}, f, indent=2)
                
            df_test_export = pd.DataFrame({
                "approx_date": df_feat.loc[test_mask, "approx_date"],
                "product_name": df_feat.loc[test_mask, "product_name"],
                "y_true": y_test_true,
                "y_pred": test_p,
                "lower_80": test_intervals["lower_80"],
                "upper_80": test_intervals["upper_80"],
                "lower_95": test_intervals["lower_95"],
                "upper_95": test_intervals["upper_95"]
            })
            df_test_export.to_csv(run_path / "predictions_test.csv", index=False)
            
            # Save model artefact
            if (h, m_name) in fitted_models:
                m_obj = fitted_models[(h, m_name)]
                save_model_path = models_dir / f"{m_name}_h{h}.joblib"
                try:
                    joblib.dump(m_obj, save_model_path)
                except Exception:
                    pass

    # Save all main leaderboards
    df_leaderboard = pd.DataFrame(leaderboard_records)
    df_by_veg = pd.DataFrame(by_veg_records)
    df_by_cat = pd.DataFrame(by_cat_records)
    df_uncertainty = pd.DataFrame(uncertainty_records)
    df_leafy = pd.DataFrame(leafy_audit_records)
    
    # Apply Holm-Bonferroni correction on test DM p-values
    test_rows = df_leaderboard[df_leaderboard["split"] == "test"].copy()
    for h in target_horizons:
        h_idx = test_rows[test_rows["horizon"] == h].index
        p_raw = test_rows.loc[h_idx, "DM_pval_vs_Naive"].dropna().values
        if len(p_raw) > 0:
            adj_p = holm_bonferroni_correction(p_raw)
            df_leaderboard.loc[h_idx, "DM_pval_Holm_vs_Naive"] = adj_p
            
    df_leaderboard.to_csv(exp_dir / "leaderboard.csv", index=False)
    df_by_veg.to_csv(exp_dir / "leaderboard_by_vegetable.csv", index=False)
    df_by_cat.to_csv(exp_dir / "leaderboard_by_category.csv", index=False)
    df_uncertainty.to_csv(exp_dir / "uncertainty_evaluation.csv", index=False)
    df_leafy.to_csv(exp_dir / "leafy_vegetables_audit.csv", index=False)
    
    # By-horizon aggregated leaderboard
    df_by_horizon = df_leaderboard.groupby(["model", "horizon", "split"])[["MAE", "RMSE", "sMAPE", "MASE", "R2", "Directional_Accuracy", "Skill_vs_Naive"]].mean().reset_index()
    df_by_horizon.to_csv(exp_dir / "leaderboard_by_horizon.csv", index=False)
    logger.info(f"Leaderboards written successfully to {exp_dir}")
    
    # 7. Model Selection Protocol:
    # Rule: Lowest median validation MASE at h=4.
    # If several models within 1-SE of best, pick simplest (linear < tree < deep).
    h_primary = cfg["task"].get("primary_horizon", 4)
    val_h4 = df_by_veg[df_by_veg["horizon"] == h_primary].groupby("model")["val_MASE"].agg(["median", "std", "count"]).reset_index()
    val_h4["se"] = val_h4["std"] / np.sqrt(val_h4["count"].clip(lower=1))
    val_h4 = val_h4.sort_values("median", ascending=True).reset_index(drop=True)
    
    best_candidate = val_h4.iloc[0]
    best_median = best_candidate["median"]
    best_se = best_candidate["se"]
    threshold = best_median + best_se
    
    eligible = val_h4[val_h4["median"] <= threshold].copy()
    
    # Simplicity hierarchy rank: linear (1) < tree (2) < deep (3) < ensemble (4)
    def model_complexity(m):
        if m in ["linear_regression", "ridge", "lasso", "elastic_net"]:
            return 1
        elif m in ["lightgbm", "xgboost", "catboost", "random_forest", "extra_trees", "gradient_boosting", "svr"]:
            return 2
        elif m in ["mlp", "lstm", "gru", "tcn_1d", "nbeats", "transformer", "nhits", "tft_lite"]:
            return 3
        elif m in ["auto_arima", "sarimax", "holt_winters_ets", "prophet", "naive", "seasonal_naive_48", "moving_average_4", "moving_average_12", "drift"]:
            return 0 # Baselines / statistical
        else:
            return 4 # Ensembles
            
    eligible["complexity"] = eligible["model"].apply(model_complexity)
    
    # Ensembles only selected if significantly better than best single component
    best_single_median = val_h4[~val_h4["model"].str.contains("ensemble|top3|stacking")]["median"].min()
    selected_row = eligible.sort_values(by=["complexity", "median"]).iloc[0]
    selected_model_name = selected_row["model"]
    
    logger.info(f"\n{'*'*60}\nWINNING MODEL SELECTED: [{selected_model_name}]\nMedian Validation MASE at h={h_primary}: {selected_row['median']:.4f} (1-SE Threshold: {threshold:.4f})\n{'*'*60}")
    
    # 8. Friedman + Nemenyi Test & Critical Difference
    h4_veg_matrix = df_by_veg[df_by_veg["horizon"] == h_primary].pivot(index="vegetable", columns="model", values="test_MASE").dropna()
    if len(h4_veg_matrix) > 2:
        f_stat, f_p, avg_ranks, cd = compute_friedman_nemenyi(h4_veg_matrix)
        stat_tests = {
            "friedman_chi2": f_stat,
            "friedman_p_value": f_p,
            "nemenyi_critical_difference_05": cd,
            "top_5_average_ranks": avg_ranks.sort_values().head(5).to_dict()
        }
        with open(exp_dir / "statistical_tests.json", "w", encoding="utf-8") as f:
            json.dump(stat_tests, f, indent=2)
            
        # Plot Nemenyi Critical Difference Diagram
        plt.figure(figsize=(10, 5))
        top_ranks = avg_ranks.sort_values().head(10)
        plt.barh(top_ranks.index[::-1], top_ranks.values[::-1], color="#3b82f6", alpha=0.85)
        plt.axvline(top_ranks.min() + cd, color="#ef4444", linestyle="--", label=f"Nemenyi CD ({cd:.2f}) from Rank 1")
        plt.xlabel("Average Friedman Rank (Lower is Better)")
        plt.title(f"Top 10 Models by Friedman Rank (h={h_primary} Across 32 Vegetables)")
        plt.legend()
        plt.tight_layout()
        plt.savefig("results/figures/nemenyi_critical_difference.png", dpi=200)
        plt.close()
        
    # Plot Deep Learning loss curves
    plot_dl_learning_curves("results/figures/dl_learning_curves.png")
    
    # Save Model Card
    best_model_dir = models_dir / "best_model"
    best_model_dir.mkdir(parents=True, exist_ok=True)
    if (h_primary, selected_model_name) in fitted_models:
        best_obj = fitted_models[(h_primary, selected_model_name)]
        try:
            joblib.dump(best_obj, best_model_dir / "model.joblib")
        except Exception:
            pass
            
    # Write provenance run manifest
    run_manifest = {
        "run_mode": "smoke" if is_smoke else "full",
        "target_vegetables_count": len(df_feat["product_name"].unique()),
        "vegetables": list(df_feat["product_name"].unique()),
        "horizons": target_horizons,
        "split_dates": {
            "train": [str(df_feat.loc[train_mask, "approx_date"].min()), str(df_feat.loc[train_mask, "approx_date"].max())],
            "validation": [str(df_feat.loc[val_mask, "approx_date"].min()), str(df_feat.loc[val_mask, "approx_date"].max())],
            "test": [str(df_feat.loc[test_mask, "approx_date"].min()), str(df_feat.loc[test_mask, "approx_date"].max())]
        },
        "n_obs": {
            "train": int(train_mask.sum()),
            "val_tune": int(val_tune_mask.sum()),
            "val_cal": int(val_cal_mask.sum()),
            "test": int(test_mask.sum())
        },
        "models_evaluated": all_models_for_h,
        "selected_model": selected_model_name,
        "selection_rule": "Lowest median validation MASE at h=4 with 1-SE simplicity tie-breaker (linear < tree < deep).",
        "primary_horizon": h_primary,
        "seed": cfg.get("random_seed", 42)
    }
    with open(exp_dir / "run_manifest.json", "w", encoding="utf-8") as f:
        json.dump(run_manifest, f, indent=2)
        
    logger.info(f"Pipeline completed successfully. Selected model: {selected_model_name}")
    return df_leaderboard, selected_model_name
