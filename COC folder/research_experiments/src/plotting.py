"""
plotting.py - Publication-grade figures (300 DPI) for thesis and reports.
"""

from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd


def set_publication_style():
    """Sets consistent academic styling for figures."""
    sns.set_theme(style="whitegrid", font="sans-serif")
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
    plt.rcParams["axes.edgecolor"] = "#333333"
    plt.rcParams["axes.linewidth"] = 0.8


def plot_residuals(y_true: np.ndarray, y_pred: np.ndarray, years: np.ndarray, model_name: str, output_path: Path):
    """Generates out-of-fold actual vs. predicted plot colored by year."""
    set_publication_style()
    fig, ax = plt.subplots(figsize=(8, 6.5))

    y_t_k = y_true / 1000.0
    y_p_k = y_pred / 1000.0

    scatter = ax.scatter(y_t_k, y_p_k, c=years, cmap="viridis", alpha=0.8, edgecolors="none", s=50)
    cbar = fig.colorbar(scatter, ax=ax)
    cbar.set_label("Cultivation Start Year", fontsize=10, fontweight="bold")

    max_val = max(y_t_k.max(), y_p_k.max()) * 1.05
    ax.plot([0, max_val], [0, max_val], color="#dc2626", linestyle="--", linewidth=1.8, label="Ideal 1:1 Line")

    ax.set_xlim(0, max_val)
    ax.set_ylim(0, max_val)
    ax.set_xlabel("Actual Cultivation Cost (Thousand LKR/acre)", fontsize=11, fontweight="bold")
    ax.set_ylabel("Predicted Cultivation Cost (Thousand LKR/acre)", fontsize=11, fontweight="bold")
    ax.set_title(f"Actual vs. Predicted Costs (LOSO)\nModel: {model_name}", fontsize=12, fontweight="bold", pad=12)
    ax.legend(loc="upper left", frameon=True)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_leaderboard(df_leaderboard: pd.DataFrame, output_path: Path):
    """Plots horizontal bar chart ranking models by LOSO MAE."""
    set_publication_style()
    df_sorted = df_leaderboard.sort_values(by="LOSO_MAE", ascending=False)

    fig, ax = plt.subplots(figsize=(10, max(6, len(df_sorted) * 0.4)))

    palette = {
        "Statistical": "#3b82f6",
        "Shallow_ML": "#10b981",
        "Deep_Learning": "#8b5cf6",
        "Foundation": "#f59e0b"
    }
    colors = [palette.get(f, "#6b7280") for f in df_sorted["family"]]

    bars = ax.barh(df_sorted["model_name"], df_sorted["LOSO_MAE"], color=colors, height=0.6, alpha=0.9)
    ax.set_xlabel("Mean Absolute Error (LKR / acre)", fontsize=11, fontweight="bold")
    ax.set_title("Primary Benchmark Leaderboard: Leave-One-Season-Year-Out (LOSO)", fontsize=13, fontweight="bold", pad=12)

    for bar in bars:
        w = bar.get_width()
        ax.text(w + 1000, bar.get_y() + bar.get_height() / 2, f"Rs {w:,.0f}", va="center", fontsize=9, fontweight="bold")

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()


def plot_regime_comparison(df_regimes: pd.DataFrame, output_path: Path):
    """Compares top models across Stable, Crisis, and Post-Crisis regimes."""
    set_publication_style()
    fig, ax = plt.subplots(figsize=(10, 6))

    sns.barplot(data=df_regimes, x="model_name", y="MAE", hue="economic_regime", palette="Blues_d", ax=ax)
    ax.set_ylabel("MAE (LKR / acre)", fontsize=11, fontweight="bold")
    ax.set_xlabel("Model Name", fontsize=11, fontweight="bold")
    ax.set_title("Performance by Macroeconomic Regime (Stable vs Crisis vs Post-Crisis)", fontsize=13, fontweight="bold", pad=12)
    plt.xticks(rotation=30, ha="right")
    ax.legend(title="Regime", frameon=True)

    plt.tight_layout()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300)
    plt.close()
