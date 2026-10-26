import logging
import numpy as np
import pandas as pd

from .utils import load_config, get_logger

logger = get_logger("src.features")

def apply_causal_imputation(series, max_ffill=2):
    """
    Impute missing inputs causally: forward-fill only up to max_ffill consecutive steps.
    Never interpolate backward or forward using future values.
    Returns (imputed_series, missing_indicator).
    """
    missing_indicator = series.isna().astype(float)
    # Forward-fill limited to max_ffill steps
    imputed = series.ffill(limit=max_ffill)
    return imputed, missing_indicator

def build_vegetable_features(df_long, cfg=None, include_cross_veg=True):
    """
    Generate comprehensive, leakage-free causal features across all 32 vegetables.
    Returns feature matrix X, targets y for all horizons, and metadata dataframe.
    """
    if cfg is None:
        cfg = load_config()
        
    feat_cfg = cfg["features"]
    max_ffill = feat_cfg.get("causal_imputation_max_ffill", 2)
    lags = feat_cfg.get("lags", [1, 2, 3, 4, 8, 12, 26, 48])
    rolling_windows = feat_cfg.get("rolling_windows", [4, 8, 12, 26])
    horizons = cfg["task"].get("horizons", [1, 4, 8, 12])
    
    # Sort strictly by vegetable and time
    df_sorted = df_long.sort_values(["product_name", "week_index"]).copy()
    
    # Compute cross-vegetable statistics first (at each week) to allow lag-1 features
    # Market-wide median and category-level means
    market_stats = df_sorted.groupby("week_index")["price_lkr"].agg(
        market_median_price="median",
        market_mean_price="mean"
    ).reset_index()
    
    category_stats = df_sorted.groupby(["category", "week_index"])["price_lkr"].agg(
        category_mean_price="mean"
    ).reset_index()
    
    # Shift cross-veg features by 1 week so they represent strictly prior information
    market_stats["market_median_lag1"] = market_stats["market_median_price"].shift(1)
    market_stats["market_pct_change_lag1"] = market_stats["market_median_price"].pct_change(1)
    market_stats = market_stats.drop(columns=["market_median_price", "market_mean_price"])
    
    category_stats["category_mean_lag1"] = category_stats.groupby("category")["category_mean_price"].shift(1)
    category_stats = category_stats.drop(columns=["category_mean_price"])
    
    # Merge lagged cross-veg features
    df_sorted = df_sorted.merge(market_stats, on="week_index", how="left")
    df_sorted = df_sorted.merge(category_stats, on=["category", "week_index"], how="left")
    
    feature_rows = []
    
    for veg, group in df_sorted.groupby("product_name"):
        grp = group.sort_values("week_index").copy()
        
        # Raw prices
        raw_price = grp["price_lkr"].copy()
        imputed_price, missing_ind = apply_causal_imputation(raw_price, max_ffill=max_ffill)
        
        # Log prices (with small epsilon for numeric stability)
        log_price = np.log(imputed_price.clip(lower=1.0))
        
        feat_df = pd.DataFrame(index=grp.index)
        feat_df["week_index"] = grp["week_index"]
        feat_df["year"] = grp["year"]
        feat_df["month"] = grp["month"]
        feat_df["week_of_month"] = grp["week_of_month"]
        feat_df["approx_date"] = grp["approx_date"]
        feat_df["product_name"] = grp["product_name"]
        feat_df["category"] = grp["category"]
        feat_df["unit"] = grp["unit"]
        feat_df["price_lkr"] = grp["price_lkr"]
        feat_df["is_backfilled"] = grp["is_backfilled"].astype(float)
        feat_df["is_stale_run"] = grp["is_stale_run"].astype(float)
        feat_df["missing_indicator"] = missing_ind
        
        # Target variables: original observed price at horizon h (un-imputed!)
        for h in horizons:
            feat_df[f"target_h{h}"] = raw_price.shift(-h)
            feat_df[f"target_log_h{h}"] = np.log(raw_price.shift(-h).clip(lower=1.0))
            
        # Cyclical calendar features
        month_rad = 2 * np.pi * (grp["month"] - 1) / 12.0
        feat_df["sin_month"] = np.sin(month_rad)
        feat_df["cos_month"] = np.cos(month_rad)
        
        # Week of month (1..4)
        wom_rad = 2 * np.pi * (grp["week_of_month"] - 1) / 4.0
        feat_df["sin_wom"] = np.sin(wom_rad)
        feat_df["cos_wom"] = np.cos(wom_rad)
        
        # Reporting week of year (1..48)
        rep_woy = ((grp["month"] - 1) * 4 + grp["week_of_month"]).clip(1, 48)
        woy_rad = 2 * np.pi * (rep_woy - 1) / 48.0
        feat_df["sin_woy"] = np.sin(woy_rad)
        feat_df["cos_woy"] = np.cos(woy_rad)
        
        # Lags of imputed price and log_price
        for lag in lags:
            feat_df[f"lag_{lag}"] = imputed_price.shift(lag)
            feat_df[f"log_lag_{lag}"] = log_price.shift(lag)
            
        # Rolling statistics over causal lookback windows
        for w in rolling_windows:
            rolled = imputed_price.shift(1).rolling(window=w, min_periods=max(2, w//2))
            feat_df[f"roll_mean_{w}"] = rolled.mean()
            feat_df[f"roll_std_{w}"] = rolled.std().fillna(0)
            feat_df[f"roll_min_{w}"] = rolled.min()
            feat_df[f"roll_max_{w}"] = rolled.max()
            feat_df[f"roll_skew_{w}"] = (rolled.max() - rolled.min()) / (rolled.mean().clip(lower=1.0))
            
        # Momentum & percentage changes
        feat_df["pct_change_1w"] = imputed_price.pct_change(1).shift(1)
        feat_df["pct_change_4w"] = imputed_price.pct_change(4).shift(1)
        feat_df["pct_change_12w"] = imputed_price.pct_change(12).shift(1)
        
        # Relative to rolling annual average (48 weeks)
        roll_48 = imputed_price.shift(1).rolling(window=48, min_periods=12).mean()
        feat_df["ratio_to_annual_mean"] = imputed_price.shift(1) / roll_48.clip(lower=1.0)
        
        # Same week last year ratio (seasonal comparison)
        lag_48 = imputed_price.shift(48)
        feat_df["seasonal_yoy_ratio"] = imputed_price.shift(1) / lag_48.clip(lower=1.0)
        
        # Cross-vegetable features
        if include_cross_veg:
            feat_df["market_median_lag1"] = grp["market_median_lag1"]
            feat_df["market_pct_change_lag1"] = grp["market_pct_change_lag1"]
            feat_df["category_mean_lag1"] = grp["category_mean_lag1"]
            feat_df["ratio_to_category_mean"] = imputed_price.shift(1) / grp["category_mean_lag1"].clip(lower=1.0)
            
        feature_rows.append(feat_df)
        
    df_features = pd.concat(feature_rows, axis=0).sort_values(["product_name", "week_index"]).reset_index(drop=True)
    
    logger.info(f"Engineered {len(df_features.columns)} total columns across {len(df_features)} observations (cross_veg={include_cross_veg}).")
    return df_features
