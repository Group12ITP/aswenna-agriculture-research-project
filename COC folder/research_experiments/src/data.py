"""
data.py - Data ingestion, series formatting, and temporal indexing for IT4010 COC.
"""

from pathlib import Path
import pandas as pd
import numpy as np


def get_project_root() -> Path:
    """Returns the root directory of the COC project."""
    current = Path(__file__).resolve()
    for parent in [current] + list(current.parents):
        if (parent / "data" / "processed" / "coc_model_ready.csv").exists():
            return parent
    return Path(r"c:\Users\MSI\Desktop\Research\Profit Folder\COC folder")


def load_model_data() -> pd.DataFrame:
    """
    Loads coc_model_ready.csv, builds the chronological time index,
    and sets canonical series keys.
    """
    root = get_project_root()
    data_path = root / "data" / "processed" / "coc_model_ready.csv"
    if not data_path.exists():
        raise FileNotFoundError(f"Missing model dataset: {data_path}")

    df = pd.read_csv(data_path)

    # 1. Irrigation Type normalization
    df["Irrigation_Type"] = df["Irrigation_Type"].fillna("Unspecified")

    # 2. Chronological sequence order index:
    # 2014-15 Maha -> 2014*2 + 1 = 4029
    # 2015 Yala    -> 2015*2 + 0 = 4030
    # 2015-16 Maha -> 2015*2 + 1 = 4031
    # 2016 Yala    -> 2016*2 + 0 = 4032
    df["season_order_key"] = df["Year_Start"] * 2 + np.where(df["Season"] == "Yala", 0, 1)

    # 3. Calendar date mapping for Prophet and Time-Series models
    # Yala -> May 1st, Maha -> Oct 1st
    df["calendar_date"] = pd.to_datetime(
        df["Year_Start"].astype(str) + np.where(df["Season"] == "Yala", "-05-01", "-10-01")
    )

    # 4. Canonical series key: Crop | District | Irrigation_Type
    df["series_key"] = df["Crop"] + " | " + df["District"] + " | " + df["Irrigation_Type"]

    # 5. Economic Regime classification
    conditions = [
        df["Year_Start"] <= 2020,
        (df["Year_Start"] >= 2021) & (df["Year_Start"] <= 2023),
        df["Year_Start"] >= 2024
    ]
    choices = ["Stable", "Crisis", "Post-Crisis"]
    df["economic_regime"] = np.select(conditions, choices, default="Stable")

    # Sort strictly chronologically
    df = df.sort_values(by=["series_key", "season_order_key"]).reset_index(drop=True)
    df["row_id"] = np.arange(len(df))

    return df


def get_feature_and_target_columns():
    """Returns canonical leak-free feature names and target name."""
    feature_cols = [
        "District", "Crop", "Season", "Irrigation_Type",
        "Year_Start", "USD_LKR_Rate", "Prev_Season_Total_Cost_Incl_Imputed"
    ]
    target_col = "Total_Cost_Incl_Imputed"
    return feature_cols, target_col


def get_crop_level_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes national crop-level aggregate series per season.
    Useful for macro-level time series forecasting.
    """
    agg = df.groupby(["Crop", "Year_Start", "Season", "season_order_key", "calendar_date"]).agg({
        "Total_Cost_Incl_Imputed": "mean",
        "USD_LKR_Rate": "mean"
    }).reset_index()
    agg["series_key"] = agg["Crop"] + " | National_Mean | Irrigated"
    return agg
