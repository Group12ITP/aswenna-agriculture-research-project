#!/usr/bin/env python3
"""
Prediction Intervals & Feature Attribution Module for IT4010 SO1
================================================================
Constructs calibrated multiplicative prediction intervals in log-space:
    log_pred = np.log1p(predicted_cost)
    log_low  = log_pred - z * sigma_log
    log_high = log_pred + z * sigma_log
    low      = np.expm1(log_low)
    high     = np.expm1(log_high)

And computes local SHAP feature attributions for individual predictions,
ranking top cost drivers with their relative percentage contributions
and directional impact (+ / -).
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt
import joblib

# Global File Paths
WORKSPACE = Path(__file__).resolve().parent
SCRIPTS_DIR = WORKSPACE / "scripts"
if str(WORKSPACE) not in sys.path:
    sys.path.insert(0, str(WORKSPACE))
if SCRIPTS_DIR.exists() and str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

# Ensure custom transformer CropLagImputer is available for unpickling
from train_evaluate_pipeline import CropLagImputer, build_preprocessor, get_feature_names

# Optional SHAP integration with graceful fallback
try:
    import shap
    HAS_SHAP = True
except ImportError:
    HAS_SHAP = False

MODEL_PATH = WORKSPACE / "models" / "best_model_pipeline.pkl"
if not MODEL_PATH.exists():
    MODEL_PATH = WORKSPACE / "best_model_pipeline.pkl"

DATA_PATH = WORKSPACE / "data" / "processed" / "coc_model_ready.csv"
if not DATA_PATH.exists():
    DATA_PATH = WORKSPACE / "coc_model_ready.csv"

MODEL_VERSION = "extratrees_champion_v2"

# Pre-computed LOSO Out-of-Fold Log-Residual Standard Deviations (ddof=1)
# Calibrated on empirical winning ExtraTreesRegressor (LOSO MAE = Rs 22,822.02, R2 = 0.9329)
SIGMA_LOG_ALL = 0.17074       # Overall LOSO log-residual std across all 12 years (641 rows)
SIGMA_LOG_STABLE = 0.14495    # Stable era: 2014-2020 (362 rows) -> ~14.5% relative std
SIGMA_LOG_CRISIS = 0.22446    # Volatile crisis era: 2021-2023 (162 rows) -> ~22.4% relative std
SIGMA_LOG_POST = 0.14724      # Post-crisis recovery: 2024-2025 (117 rows) -> ~14.7% relative std

USD_LKR_RATE_TRAIN_MEAN = 217.0255 # Historical training mean exchange rate

# Compute training USD/LKR range at startup
if DATA_PATH.exists():
    _df_usd = pd.read_csv(DATA_PATH)
    USD_MIN_TRAINING = round(float(_df_usd['USD_LKR_Rate'].min()), 2)  # 130.54
    USD_MAX_TRAINING = round(float(_df_usd['USD_LKR_Rate'].max()), 2)  # 326.63
else:
    USD_MIN_TRAINING = 130.54
    USD_MAX_TRAINING = 326.63

FEATURES = [
    'District', 'Crop', 'Season', 'Irrigation_Type', 
    'Year_Start', 'USD_LKR_Rate', 'Prev_Season_Total_Cost_Incl_Imputed'
]

# Mapping of transformed feature columns back to original 7 user-facing attributes
FEATURE_COLUMN_MAPPING = {
    'Crop': 'Crop',
    'District': 'District',
    'Season_Maha': 'Season',
    'Season_Yala': 'Season',
    'Irrigation_Type_Irrigated': 'Irrigation_Type',
    'Irrigation_Type_Rainfed': 'Irrigation_Type',
    'Irrigation_Type_Unspecified': 'Irrigation_Type',
    'Year_Start': 'Year_Start',
    'USD_LKR_Rate': 'USD_LKR_Rate',
    'Prev_Season_Total_Cost_Incl_Imputed': 'Prev_Season_Total_Cost_Incl_Imputed',
    'PrevSeason_Was_Missing': 'Prev_Season_Total_Cost_Incl_Imputed'
}

# Cached singletons
_CACHED_MODEL = None
_CACHED_EXPLAINER = None
_CACHED_FEAT_NAMES = None


def get_model():
    """Load or return the cached best model pipeline."""
    global _CACHED_MODEL
    if _CACHED_MODEL is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Trained model pipeline not found at {MODEL_PATH}")
        _CACHED_MODEL = joblib.load(MODEL_PATH)
    return _CACHED_MODEL


def get_explainer():
    """Load or return the cached SHAP TreeExplainer and transformed feature names."""
    global _CACHED_EXPLAINER, _CACHED_FEAT_NAMES
    if _CACHED_EXPLAINER is None:
        model = get_model()
        pipeline = model.regressor_
        reg = pipeline.named_steps['regressor']
        
        if HAS_SHAP:
            _CACHED_EXPLAINER = shap.TreeExplainer(reg)
        else:
            _CACHED_EXPLAINER = "FALLBACK"
            
        # Extract feature names
        sample_df = pd.read_csv(DATA_PATH, nrows=50)
        _CACHED_FEAT_NAMES = get_feature_names(
            build_preprocessor('full', random_state=42), 
            sample_df[FEATURES], 
            np.log1p(sample_df['Total_Cost_Incl_Imputed'])
        )
    return _CACHED_EXPLAINER, _CACHED_FEAT_NAMES


class PredictionInterval:
    """
    Structured result object for prediction intervals with feature attributions.
    Unpacks cleanly as (interval_low, predicted_cost, interval_high).
    """
    def __init__(self, low: float, prediction: float, high: float, low_confidence: bool, 
                 top_drivers: list, eff_sigma: float, z_score: float, 
                 low_confidence_reason: str = None,
                 model_version: str = MODEL_VERSION):
        self.predicted_cost = float(prediction)
        self.interval_low = float(low)
        self.interval_high = float(high)
        self.low_confidence = bool(low_confidence)
        self.low_confidence_reason = low_confidence_reason
        self.top_drivers = top_drivers
        self.model_version = model_version
        
        # Convenience aliases
        self.prediction = self.predicted_cost
        self.low = self.interval_low
        self.high = self.interval_high
        self.interval_width = float(high - low)
        self.eff_sigma = float(eff_sigma)
        self.z_score = float(z_score)

    def __iter__(self):
        """Allows unpacking: low, pred, high = predict_with_interval(x)"""
        return iter([self.interval_low, self.predicted_cost, self.interval_high])

    def __getitem__(self, item):
        if isinstance(item, int):
            return [self.interval_low, self.predicted_cost, self.interval_high][item]
        elif isinstance(item, str):
            if hasattr(self, item):
                return getattr(self, item)
        raise KeyError(item)

    def __len__(self):
        return 3

    def to_dict(self):
        """Return the clean JSON/dict representation requested."""
        return {
            "predicted_cost": round(self.predicted_cost, 1),
            "interval_low": round(self.interval_low, 1),
            "interval_high": round(self.interval_high, 1),
            "low_confidence": self.low_confidence,
            "low_confidence_reason": self.low_confidence_reason,
            "top_drivers": self.top_drivers,
            "model_version": self.model_version,
            # Aliases for DataFrame/analysis convenience
            "prediction": round(self.predicted_cost, 1),
            "low": round(self.interval_low, 1),
            "high": round(self.interval_high, 1),
            "interval_width": round(self.interval_width, 1)
        }

    def __repr__(self):
        return (f"PredictionInterval(predicted_cost=Rs {self.predicted_cost:,.1f}, "
                f"interval=[Rs {self.interval_low:,.1f}, Rs {self.interval_high:,.1f}], "
                f"low_confidence={self.low_confidence}, "
                f"top_driver='{self.top_drivers[0]['feature']}' ({self.top_drivers[0]['contribution_pct']}%, {self.top_drivers[0]['direction']}))")


def compute_feature_drivers(X_trans_row, feat_names, regressor, top_n: int = 3):
    """
    Computes local feature contribution percentages and directions.
    Uses SHAP TreeExplainer if available, otherwise falls back to
    feature importances weighted by normalized input deviation.
    """
    explainer, _ = get_explainer()
    grouped_contributions = {}

    if HAS_SHAP and explainer != "FALLBACK":
        # SHAP TreeExplainer
        shap_vals = explainer.shap_values(X_trans_row)[0]
        for name, val in zip(feat_names, shap_vals):
            orig_feat = FEATURE_COLUMN_MAPPING.get(name, name)
            grouped_contributions[orig_feat] = grouped_contributions.get(orig_feat, 0.0) + float(val)
    else:
        # Fallback proxy: tree feature importances * transformed deviation
        importances = regressor.feature_importances_
        row_vals = np.asarray(X_trans_row).flatten()
        proxy_contributions = importances * row_vals
        for name, val in zip(feat_names, proxy_contributions):
            orig_feat = FEATURE_COLUMN_MAPPING.get(name, name)
            grouped_contributions[orig_feat] = grouped_contributions.get(orig_feat, 0.0) + float(val)

    # Compute relative percentages
    total_abs = sum(abs(v) for v in grouped_contributions.values())
    drivers = []
    for f, v in grouped_contributions.items():
        pct = (abs(v) / total_abs * 100.0) if total_abs > 0 else 0.0
        direction = "+" if v >= 0 else "-"
        drivers.append({
            "feature": f,
            "contribution_pct": round(pct, 1),
            "direction": direction
        })

    # Sort descending by contribution percentage
    drivers_sorted = sorted(drivers, key=lambda x: x["contribution_pct"], reverse=True)
    return drivers_sorted[:top_n]


def predict_with_interval(X_raw, confidence: float = 0.80, top_n_drivers: int = 3):
    """
    Predict agricultural cultivation cost with calibrated multiplicative prediction intervals
    and local SHAP feature attributions.

    Parameters
    ----------
    X_raw : pd.DataFrame, pd.Series, or dict
        Input feature record(s) containing:
        ['District', 'Crop', 'Season', 'Irrigation_Type', 'Year_Start', 
         'USD_LKR_Rate', 'Prev_Season_Total_Cost_Incl_Imputed']
    confidence : float, default=0.80
        Confidence level for the interval (default 0.80 uses z=1.28).
    top_n_drivers : int, default=3
        Number of top driving features to include in the attribution breakdown.

    Returns
    -------
    PredictionInterval (if single row) or pd.DataFrame (if multi-row)
    """
    model = get_model()
    pipeline = model.regressor_
    prep = pipeline.named_steps['prep']
    reg = pipeline.named_steps['regressor']
    _, feat_names = get_explainer()

    # Determine z-multiplier
    if np.isclose(confidence, 0.80):
        z = 1.28
    else:
        z = stats.norm.ppf(1.0 - (1.0 - confidence) / 2.0)

    # Convert single row dict or Series to DataFrame
    is_single_record = False
    if isinstance(X_raw, dict):
        X_df = pd.DataFrame([X_raw])
        is_single_record = True
    elif isinstance(X_raw, pd.Series):
        X_df = pd.DataFrame([X_raw.to_dict()])
        is_single_record = True
    elif isinstance(X_raw, pd.DataFrame):
        X_df = X_raw.copy()
        if len(X_df) == 1:
            is_single_record = True
    else:
        raise ValueError("X_raw must be a dict, pd.Series, or pd.DataFrame")

    # Generate point predictions (already in true LKR scale via TransformedTargetRegressor)
    preds = model.predict(X_df[FEATURES])
    
    # Pre-transform features for SHAP
    X_trans = prep.transform(X_df[FEATURES])

    intervals = []
    for idx, (_, row) in enumerate(X_df.iterrows()):
        pred = max(0.0, float(preds[idx]))
        yr = row.get('Year_Start', None)
        fx = row.get('USD_LKR_Rate', None)

        # 1. Stratify log-residual std by the 3 macroeconomic regimes
        if yr in [2021, 2022, 2023]:
            base_sigma = SIGMA_LOG_CRISIS
        elif yr in [2024, 2025]:
            base_sigma = SIGMA_LOG_POST
        elif yr is not None and yr <= 2020:
            base_sigma = SIGMA_LOG_STABLE
        else:
            base_sigma = SIGMA_LOG_ALL

        # 2. Check foreign exchange extrapolation (outside training range [USD_MIN_TRAINING, USD_MAX_TRAINING])
        if fx is not None and not pd.isna(fx):
            is_out_of_range = (fx < USD_MIN_TRAINING) or (fx > USD_MAX_TRAINING)
        else:
            is_out_of_range = False

        if is_out_of_range:
            low_conf_reason = (
                f"USD/LKR rate {fx} is outside the training range [{USD_MIN_TRAINING:.2f}, {USD_MAX_TRAINING:.2f}]. "
                f"The model is extrapolating."
            )
        else:
            low_conf_reason = None

        # Widen by 1.5x and flag low_confidence if currency is outside training range
        multiplier = 1.5 if is_out_of_range else 1.0
        eff_sigma = base_sigma * multiplier

        # 3. Multiplicative Interval in Log Space
        log_pred = np.log1p(pred)
        log_low = log_pred - z * eff_sigma
        log_high = log_pred + z * eff_sigma

        # Inverse transform back to true LKR
        low = np.expm1(log_low)
        high = np.expm1(log_high)

        # Guarantee strict positivity for cultivation cost
        low = max(1.0, low)

        # 4. Local SHAP Feature Attribution
        row_trans = X_trans[idx:idx+1]
        top_drivers = compute_feature_drivers(row_trans, feat_names, reg, top_n=top_n_drivers) if top_n_drivers > 0 else []

        interval_obj = PredictionInterval(
            low=low,
            prediction=pred,
            high=high,
            low_confidence=is_out_of_range,
            low_confidence_reason=low_conf_reason,
            top_drivers=top_drivers,
            eff_sigma=eff_sigma,
            z_score=z,
            model_version=MODEL_VERSION
        )
        intervals.append(interval_obj)

    if is_single_record:
        return intervals[0]
    else:
        return pd.DataFrame([inv.to_dict() for inv in intervals])


def run_sanity_check(sample_size=10, random_state=42):
    """Run sanity check on random rows from coc_model_ready.csv and report driver details."""
    print("=" * 90)
    print(f"SANITY CHECK & SHAP FEATURE DRIVERS: {sample_size} Rows from coc_model_ready.csv")
    print("=" * 90)
    df = pd.read_csv(DATA_PATH)
    sample = df.sample(n=sample_size, random_state=random_state).copy()

    inside_count = 0
    zero_bound_count = 0
    records = []
    results = []

    for _, row in sample.iterrows():
        actual = row['Total_Cost_Incl_Imputed']
        res = predict_with_interval(row, confidence=0.80)
        low, pred, high = res
        inside = (low <= actual <= high)
        if inside:
            inside_count += 1
        if low <= 0.0:
            zero_bound_count += 1

        results.append((row, res, actual, inside))
        records.append({
            "Crop": row['Crop'],
            "District": row['District'],
            "Year": int(row['Year_Start']),
            "Actual_Cost": f"Rs {actual:,.1f}",
            "Predicted": f"Rs {pred:,.1f}",
            "Interval_Low": f"Rs {low:,.1f}",
            "Interval_High": f"Rs {high:,.1f}",
            "Top_Driver": f"{res.top_drivers[0]['feature']} ({res.top_drivers[0]['contribution_pct']}%, {res.top_drivers[0]['direction']})",
            "Low_Conf": "True" if res.low_confidence else "False",
            "Inside": "YES" if inside else "NO"
        })

    check_df = pd.DataFrame(records)
    print(check_df.to_string(index=False))

    coverage_pct = (inside_count / sample_size) * 100.0
    print("-" * 90)
    print(f"Coverage Result: {inside_count}/{sample_size} ({coverage_pct:.1f}%) within 80% Prediction Interval.")
    print(f"Zero Lower Bounds Detected: {zero_bound_count}")
    print("=" * 90)

    # Detailed inspection of 3 representative records:
    # 1. Stable year (e.g. 2017 Kandy Paddy)
    # 2. Crisis year (e.g. 2022 Hambantota Paddy)
    # 3. High-cost vegetable crop (e.g. 2024 Nuwara Eliya Potato)
    print("\n" + "=" * 90)
    print("DETAILED SHAP ATTRIBUTION INSPECTION FOR 3 REPRESENTATIVE REGIMES")
    print("=" * 90)

    selected_indices = [5, 1, 7]  # 5: Kandy Paddy (2017), 1: Hambantota Paddy (2022), 7: Nuwara Eliya Potato (2024)
    labels = ["Stable Year Baseline (2017 Stable)", "Crisis Year Inflation Shock (2022 Crisis)", "High-Cost Up-Country Vegetable (2024 Recovery)"]

    for idx_pos, label in zip(selected_indices, labels):
        row_sel, res_sel, act_sel, inside_sel = results[idx_pos]
        print(f"\n--- Regime Case: {label} ---")
        print(f"Crop / District / Year: {row_sel['Crop']} | {row_sel['District']} | Year {int(row_sel['Year_Start'])} (Season: {row_sel['Season']}, {row_sel['Irrigation_Type']})")
        print(f"Actual Cost: Rs {act_sel:,.1f} | USD/LKR Rate: {row_sel['USD_LKR_Rate']:.2f}")
        print(f"Output Object:\n{json.dumps(res_sel.to_dict(), indent=4)}")

    return check_df, coverage_pct


def plot_calibration_curve(output_filename="interval_calibration.png"):
    """
    Plots dual-panel calibration diagnostics with multiplicative intervals:
    Panel A: Calibration curve across nominal confidence levels (10% to 95%).
    Panel B: Empirical coverage sorted by interval width with decile analysis.
    """
    df = pd.read_csv(DATA_PATH)
    preds = predict_with_interval(df, confidence=0.80)
    df['Predicted'] = preds['prediction']
    df['Low'] = preds['low']
    df['High'] = preds['high']
    df['Width'] = preds['interval_width']
    df['Low_Conf'] = preds['low_confidence']
    df['Inside'] = (df['Low'] <= df['Total_Cost_Incl_Imputed']) & (df['Total_Cost_Incl_Imputed'] <= df['High'])

    # 1. Calibration across nominal confidence levels
    conf_levels = np.linspace(0.10, 0.95, 18)
    emp_coverages = []
    
    for c in conf_levels:
        c_preds = predict_with_interval(df, confidence=c, top_n_drivers=0)
        inside_c = (c_preds['low'] <= df['Total_Cost_Incl_Imputed']) & (df['Total_Cost_Incl_Imputed'] <= c_preds['high'])
        emp_coverages.append(inside_c.mean())

    # Set up matplotlib figure
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')

    # Panel 1: Calibration Curve (Nominal vs Empirical)
    ax1.plot([0.05, 1.0], [0.05, 1.0], linestyle='--', color='#94a3b8', linewidth=2, label='Perfect Calibration (y = x)')
    ax1.plot(conf_levels, emp_coverages, marker='o', color='#2563eb', linewidth=2.5, markersize=6, label='Empirical Coverage (Multiplicative)')

    # Highlight 80% confidence level
    idx_80 = np.argmin(np.abs(conf_levels - 0.80))
    c_80 = conf_levels[idx_80]
    emp_80 = emp_coverages[idx_80]
    ax1.scatter([c_80], [emp_80], color='#dc2626', s=120, zorder=5)
    ax1.annotate(
        f'80% Nominal Target\n(Empirical: {emp_80*100:.1f}%)',
        xy=(c_80, emp_80),
        xytext=(c_80 - 0.25, emp_80 - 0.12),
        arrowprops=dict(facecolor='#dc2626', shrink=0.08, width=1.5, headwidth=7),
        fontsize=10, fontweight='bold', color='#991b1b',
        bbox=dict(boxstyle='round,pad=0.4', facecolor='#fee2e2', edgecolor='#f87171')
    )

    ax1.set_xlim(0.05, 1.0)
    ax1.set_ylim(0.20, 1.02)
    ax1.set_xlabel('Nominal / Predicted Coverage (Confidence Level)', fontsize=11, fontweight='semibold')
    ax1.set_ylabel('Empirical Coverage (Fraction of Actuals Inside)', fontsize=11, fontweight='semibold')
    ax1.set_title('A: Multiplicative Interval Calibration Curve', fontsize=13, fontweight='bold', pad=10)
    ax1.legend(loc='lower right', frameon=True)

    # Panel 2: Coverage by Interval Width (Sorted)
    df_sorted = df.sort_values('Width').reset_index(drop=True)
    df_sorted['Cumulative_Coverage'] = df_sorted['Inside'].expanding().mean()

    # Decile binning
    df_sorted['Width_Decile'] = pd.qcut(df_sorted['Width'], q=8, duplicates='drop')
    decile_stats = df_sorted.groupby('Width_Decile', observed=False).agg(
        mean_width=('Width', 'mean'),
        coverage=('Inside', 'mean')
    ).reset_index()

    ax2.plot(
        df_sorted['Width'] / 1000, 
        df_sorted['Cumulative_Coverage'], 
        color='#059669', 
        linewidth=2.5, 
        label='Cumulative Empirical Coverage'
    )
    ax2.axhline(0.80, color='#dc2626', linestyle='--', linewidth=1.8, label='Nominal 80% Target Benchmark')

    # Scatter decile points
    ax2.scatter(
        decile_stats['mean_width'] / 1000, 
        decile_stats['coverage'], 
        color='#d97706', 
        s=60, 
        zorder=4, 
        label='Decile Group Coverage'
    )

    ax2.set_xlabel('Interval Width (Thousands LKR / acre)', fontsize=11, fontweight='semibold')
    ax2.set_ylabel('Empirical Coverage Fraction', fontsize=11, fontweight='semibold')
    ax2.set_title('B: Empirical Coverage Sorted by Interval Width', fontsize=13, fontweight='bold', pad=10)
    ax2.set_ylim(0.50, 1.02)
    ax2.legend(loc='lower right', frameon=True)

    plt.tight_layout()
    output_dir = WORKSPACE / "figures" if (WORKSPACE / "figures").exists() else WORKSPACE
    output_path = output_dir / output_filename
    plt.savefig(output_path, dpi=300)
    plt.close()
    print(f"Calibration plot successfully saved to {output_path}")

    # Also copy to artifact directory for presentation
    artifact_dir = Path("C:/Users/MSI/.gemini/antigravity-ide/brain/4f6f62a4-d53f-4f1c-a400-d77028301849")
    if artifact_dir.exists():
        import shutil
        shutil.copy2(output_path, artifact_dir / output_filename)
        print(f"Copied calibration plot to artifact directory: {artifact_dir / output_filename}")


if __name__ == "__main__":
    print(f"Executing predict_with_intervals.py with SHAP feature attributions on {DATA_PATH}...")
    run_sanity_check(sample_size=10, random_state=42)
    plot_calibration_curve("interval_calibration.png")
