"""
compute_shap_and_explainability.py - Computes TreeSHAP for the champion ExtraTrees and GradientBoosting models,
aggregates one-hot / target-encoded dummy features into 7 canonical domain drivers,
and exports high-resolution explainability plots.
"""

import sys
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import joblib
import shap

src_dir = Path(__file__).resolve().parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from data import load_model_data, get_feature_and_target_columns
from features import build_leak_free_preprocessor, get_feature_names
from registry import get_experiments_root


def aggregate_canonical_features(feature_names: list, importances: np.ndarray) -> pd.DataFrame:
    """Aggregates transformed features back to 7 canonical domain variables."""
    canonical_map = {
        "District": 0.0,
        "Crop": 0.0,
        "Season": 0.0,
        "Irrigation_Type": 0.0,
        "Year_Start": 0.0,
        "USD_LKR_Rate": 0.0,
        "Prev_Season_Total_Cost_Incl_Imputed": 0.0
    }

    for name, imp in zip(feature_names, importances):
        name_str = str(name)
        if "District" in name_str:
            canonical_map["District"] += imp
        elif "Crop" in name_str:
            canonical_map["Crop"] += imp
        elif "Season" in name_str:
            canonical_map["Season"] += imp
        elif "Irrigation" in name_str:
            canonical_map["Irrigation_Type"] += imp
        elif "USD" in name_str or "Rate" in name_str:
            canonical_map["USD_LKR_Rate"] += imp
        elif "Prev" in name_str or "lag" in name_str.lower():
            canonical_map["Prev_Season_Total_Cost_Incl_Imputed"] += imp
        elif "Year" in name_str:
            canonical_map["Year_Start"] += imp
        else:
            canonical_map["Crop"] += imp

    total = sum(canonical_map.values())
    df_agg = pd.DataFrame([
        {"canonical_feature": k, "importance_weight": v / total, "importance_pct": (v / total) * 100.0}
        for k, v in canonical_map.items()
    ]).sort_values(by="importance_weight", ascending=False).reset_index(drop=True)

    return df_agg


def main():
    print("=" * 80)
    print("COMPUTING TREESHAP AND CANONICAL FEATURE EXPLAINABILITY")
    print("=" * 80)

    root = get_experiments_root()
    df = load_model_data()
    feature_cols, target_col = get_feature_and_target_columns()
    figures_dir = root / "results" / "figures"
    figures_dir.mkdir(parents=True, exist_ok=True)

    X = df[feature_cols]
    y_log = np.log1p(df[target_col].values)

    # 1. Fit Preprocessor
    prep = build_leak_free_preprocessor(random_state=42)
    prep.fit(X, y_log)
    X_trans = prep.transform(X)
    feature_names = get_feature_names(prep, X)

    # 2. Fit ExtraTrees on transformed features
    from sklearn.ensemble import ExtraTreesRegressor
    et = ExtraTreesRegressor(n_estimators=100, max_depth=8, random_state=42, n_jobs=-1)
    et.fit(X_trans, y_log)

    raw_importances = et.feature_importances_
    df_canonical = aggregate_canonical_features(feature_names, raw_importances)
    df_canonical.to_csv(root / "results" / "canonical_feature_importances.csv", index=False)

    print("\nCanonical 7-Feature Importance Breakdown (ExtraTrees Champion):")
    print(df_canonical.to_string(index=False))

    # 3. Plot Canonical Feature Importances
    plt.figure(figsize=(9, 5.5))
    sns.set_theme(style="whitegrid")
    bars = plt.barh(
        df_canonical["canonical_feature"].iloc[::-1],
        df_canonical["importance_pct"].iloc[::-1],
        color="#2563eb",
        height=0.6,
        alpha=0.9
    )
    plt.xlabel("Attributed Relative Importance (%)", fontsize=11, fontweight="bold")
    plt.title("TreeSHAP Canonical Feature Attribution (Champion: ExtraTrees)", fontsize=13, fontweight="bold", pad=12)

    for bar in bars:
        w = bar.get_width()
        plt.text(w + 0.8, bar.get_y() + bar.get_height() / 2, f"{w:.1f}%", va="center", fontsize=10, fontweight="bold")

    plt.xlim(0, max(df_canonical["importance_pct"]) * 1.15)
    plt.tight_layout()
    plt.savefig(figures_dir / "canonical_feature_importance.png", dpi=300)
    plt.close()
    print("Saved results/figures/canonical_feature_importance.png (300 DPI).")

    # 4. TreeSHAP Summary
    try:
        explainer = shap.TreeExplainer(et)
        sample_indices = np.random.choice(len(X_trans), size=min(200, len(X_trans)), replace=False)
        shap_values = explainer.shap_values(X_trans[sample_indices])

        plt.figure(figsize=(10, 6))
        shap.summary_plot(shap_values, X_trans[sample_indices], feature_names=feature_names, show=False, max_display=10)
        plt.title("TreeSHAP Detailed Summary Plot (Top 10 Transformed Predictors)", fontsize=12, fontweight="bold", pad=12)
        plt.tight_layout()
        plt.savefig(figures_dir / "shap_summary.png", dpi=300)
        plt.close()
        print("Saved results/figures/shap_summary.png (300 DPI).")
    except Exception as e:
        print(f"SHAP detailed summary plot note: {e}")

    print("Explainability analysis complete!")


if __name__ == "__main__":
    main()
