#!/usr/bin/env python3
"""
Feature Engineering Pipeline for Cost of Cultivation (COC) Dataset
===================================================================
Produces coc_features.csv from coc_master_v2.csv.

Features:
1. Grouped time-series lag features (Prev_Season_Total_Cost_Incl_Imputed,
   Prev_Season_Year, Cost_Pct_Change_From_Prev_Season).
2. Cost component ratio features (Fertilizer/Material, Labour, Machinery).
3. Sample size tier categorization (Crop_Sample_Size_Category: High, Medium, Low).
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

def main():
    print("=" * 80)
    print("STARTING FEATURE ENGINEERING PIPELINE")
    print("=" * 80)
    workspace = Path(__file__).resolve().parent.parent
    if not (workspace / "data").exists():
        workspace = Path(r"c:\Users\MSI\Desktop\Research\COC folder")
    data_dir = workspace / "data" / "processed" if (workspace / "data" / "processed").exists() else workspace
    input_path = data_dir / "coc_master_v2.csv"
    output_path = data_dir / "coc_features.csv"
    
    if not input_path.exists():
        print(f"Error: {input_path} not found!")
        sys.exit(1)
        
    df = pd.read_csv(input_path)
    print(f"Decision: Loaded {len(df)} rows and {len(df.columns)} columns from {input_path.name}.")
    
    # --------------------------------------------------------------------------
    # PART 1: LAG FEATURES (Grouped Time Series)
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PART 1: LAG FEATURES (Grouped Time Series)")
    print("=" * 80)
    
    # Chronological season order across all 19 seasons (2014 to 2025)
    season_timeline = [
        ("2014-15", "Maha"),
        ("2015", "Yala"),
        ("2015-16", "Maha"),
        ("2016", "Yala"),
        ("2016-17", "Maha"),
        ("2017", "Yala"),
        ("2017-18", "Maha"),
        ("2018", "Yala"),
        ("2018-19", "Maha"),
        ("2019", "Yala"),
        ("2020", "Yala"),
        ("2021-22", "Maha"),
        ("2022", "Yala"),
        ("2022-23", "Maha"),
        ("2023", "Yala"),
        ("2023-24", "Maha"),
        ("2024", "Yala"),
        ("2024-25", "Maha"),
        ("2025", "Yala"),
    ]
    season_to_idx = {k: idx for idx, k in enumerate(season_timeline)}
    
    def get_season_order_idx(row):
        key = (str(row.get("Year_Range", "")), str(row.get("Season", "")))
        return season_to_idx.get(key, 999)
        
    df["_season_order_idx"] = df.apply(get_season_order_idx, axis=1)
    
    # Grouping columns: Crop, District, Irrigation_Type (cultivation_type)
    group_cols = ["Crop", "District", "Irrigation_Type"]
    print(f"Decision: Grouping by {group_cols} (using dropna=False to retain unstated/unspecified irrigation regimes).")
    
    # Sort chronologically within each group: Crop, District, Irrigation_Type, Year_Start, _season_order_idx
    print("Decision: Sorting dataset by Crop, District, Irrigation_Type, Year_Start, and Season Chronological Order.")
    df = df.sort_values(by=["Crop", "District", "Irrigation_Type", "Year_Start", "_season_order_idx"]).reset_index(drop=True)
    
    # Group analysis
    g = df.groupby(group_cols, dropna=False)
    group_sizes = g.size()
    total_groups = len(group_sizes)
    multi_season_groups = (group_sizes >= 2).sum()
    single_season_groups = (group_sizes == 1).sum()
    rows_in_multi = group_sizes[group_sizes >= 2].sum()
    rows_in_single = group_sizes[group_sizes == 1].sum()
    
    print(f"Group Analysis Summary:")
    print(f"  - Total (Crop, District, Irrigation_Type) groups : {total_groups}")
    print(f"  - Groups with >= 2 seasons                       : {multi_season_groups} ({rows_in_multi} rows)")
    print(f"  - Single-season-only groups                      : {single_season_groups} ({rows_in_single} rows)")
    
    # Shift within group
    print("Decision: Computing prior row's Total_Cost_Incl_Imputed and Year_Start using group-level shift(1).")
    df["Prev_Season_Total_Cost_Incl_Imputed"] = g["Total_Cost_Incl_Imputed"].shift(1)
    df["Prev_Season_Year"] = g["Year_Start"].shift(1)
    
    # Cost percentage change from prior season
    # Formula: (current - prev) / prev * 100. Leave NaN where prev is NaN.
    print("Decision: Computing Cost_Pct_Change_From_Prev_Season = (current - prev) / prev * 100.")
    prev_cost = df["Prev_Season_Total_Cost_Incl_Imputed"]
    curr_cost = df["Total_Cost_Incl_Imputed"]
    
    # Safe calculation
    df["Cost_Pct_Change_From_Prev_Season"] = np.where(
        prev_cost.notna() & (prev_cost > 0),
        ((curr_cost - prev_cost) / prev_cost) * 100.0,
        np.nan
    )
    
    # Drop temporary ordering helper column
    df = df.drop(columns=["_season_order_idx"])
    
    # --------------------------------------------------------------------------
    # PART 2: RATIO FEATURES
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PART 2: RATIO FEATURES")
    print("=" * 80)
    
    # Guard divide-by-zero
    tot_cost = df["Total_Cost_Incl_Imputed"].replace(0, np.nan)
    
    # Fertilizer / Material Cost % of Total
    # Note: Sri Lanka COC operation tables group inputs into Material Cost (fertilizers, agrochemicals, seed)
    df["Fertilizer_Cost_Pct_of_Total"] = df["Material_Cost"] / tot_cost
    print("Decision: Computed Fertilizer_Cost_Pct_of_Total = Material_Cost / Total_Cost_Incl_Imputed.")
    
    # Labour Cost % of Total
    df["Labour_Cost_Pct_of_Total"] = df["Labour_Cost"] / tot_cost
    print("Decision: Computed Labour_Cost_Pct_of_Total = Labour_Cost / Total_Cost_Incl_Imputed.")
    
    # Machinery Cost % of Total
    df["Machinery_Cost_Pct_of_Total"] = df["Machinery_Cost"] / tot_cost
    print("Decision: Computed Machinery_Cost_Pct_of_Total = Machinery_Cost / Total_Cost_Incl_Imputed.")
    
    # Seed Cost % of Total evaluation
    # User instruction: "skip if seed_cost column doesn't exist; tell me which you chose and why"
    has_seed_cost = any(col.lower() == "seed_cost" for col in df.columns)
    if has_seed_cost:
        df["Seed_Cost_Pct_of_Total"] = df["Seed_Cost"] / tot_cost
        print("Decision: Computed Seed_Cost_Pct_of_Total = Seed_Cost / Total_Cost_Incl_Imputed.")
    else:
        print("Decision: SKIPPED 'Seed_Cost_Pct_of_Total'.")
        print("Reason: No direct 'Seed_Cost' subtotal column exists in coc_master_v2.csv.")
        print("        The dataset tracks input usage via 'Seed_Quantity' and 'Seed_Unit_Price',")
        print("        while monetary seed expenditures are already consolidated inside 'Material_Cost'.")

    # Ratio sanity checks
    print("\nRatio Distribution Sanity Checks:")
    ratio_cols = ["Fertilizer_Cost_Pct_of_Total", "Labour_Cost_Pct_of_Total", "Machinery_Cost_Pct_of_Total"]
    for rcol in ratio_cols:
        r_series = df[rcol].dropna()
        r_min = r_series.min()
        r_med = r_series.median()
        r_max = r_series.max()
        r_gt1 = df[df[rcol] > 1.0]
        print(f"  {rcol:30s} -> Min: {r_min:7.4f} | Median: {r_med:7.4f} | Max: {r_max:7.4f} | Ratios > 1: {len(r_gt1)}")
        if len(r_gt1) > 0:
            print(f"  [FLAGGED] Rows with {rcol} > 1.0:")
            print(r_gt1[["Season", "Year_Range", "Crop", "District", rcol, "Total_Cost_Incl_Imputed"]].to_string())

    # --------------------------------------------------------------------------
    # PART 3: CROP SAMPLE SIZE CATEGORY
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PART 3: CROP SAMPLE SIZE CATEGORY")
    print("=" * 80)
    
    crop_counts = df["Crop"].value_counts()
    
    def get_crop_category(crop_name):
        cnt = crop_counts.get(crop_name, 0)
        if cnt >= 15:
            return "High"
        elif 5 <= cnt <= 14:
            return "Medium"
        else:
            return "Low"
            
    df["Crop_Sample_Size_Category"] = df["Crop"].apply(get_crop_category)
    print("Decision: Added 'Crop_Sample_Size_Category' ('High' >= 15, 'Medium' 5-14, 'Low' < 5).")
    
    # Build crop-count table
    crop_table = pd.DataFrame({
        "Crop": crop_counts.index,
        "Record_Count": crop_counts.values,
        "Crop_Sample_Size_Category": [get_crop_category(c) for c in crop_counts.index]
    })
    
    print("\nCrop Sample Size Tier Table (Sorted Descending):")
    print(crop_table.to_string(index=False))
    
    # Category totals
    cat_summary = crop_table.groupby("Crop_Sample_Size_Category").agg(
        Crops_Count=("Crop", "count"),
        Rows_Count=("Record_Count", "sum")
    ).loc[["High", "Medium", "Low"]]
    
    print("\nCategory Level Summary:")
    print(cat_summary.to_string())

    # --------------------------------------------------------------------------
    # PART 4: OUTPUT & FINAL REPORTING
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("PART 4: SAVING OUTPUT & VALIDATION")
    print("=" * 80)
    
    df.to_csv(output_path, index=False, encoding="utf-8-sig")
    print(f"Decision: Saved engineered dataset to {output_path.name}.")
    print(f"Dataset Shape: {df.shape} ({df.shape[0]} rows, {df.shape[1]} columns)")
    
    new_cols = [
        "Prev_Season_Total_Cost_Incl_Imputed",
        "Prev_Season_Year",
        "Cost_Pct_Change_From_Prev_Season",
        "Fertilizer_Cost_Pct_of_Total",
        "Labour_Cost_Pct_of_Total",
        "Machinery_Cost_Pct_of_Total",
        "Crop_Sample_Size_Category"
    ]
    
    print("\nNull-Count Summary for Newly Added Columns:")
    for ncol in new_cols:
        null_cnt = df[ncol].isnull().sum()
        pct = (null_cnt / len(df)) * 100.0
        print(f"  {ncol:35s}: {null_cnt:4d} nulls ({pct:5.2f}%)")
        
    valid_lag = df["Prev_Season_Total_Cost_Incl_Imputed"].notna().sum()
    invalid_lag = df["Prev_Season_Total_Cost_Incl_Imputed"].isna().sum()
    print(f"\n{valid_lag} rows have a valid Prev_Season_Total_Cost_Incl_Imputed, {invalid_lag} rows do not.")

    print("\nFirst 5 Rows of Feature Dataset (Sample of Key Columns):")
    key_cols_sample = ["Season", "Year_Range", "Crop", "District", "Irrigation_Type", 
                       "Total_Cost_Incl_Imputed", "Prev_Season_Total_Cost_Incl_Imputed", 
                       "Prev_Season_Year", "Cost_Pct_Change_From_Prev_Season",
                       "Fertilizer_Cost_Pct_of_Total", "Labour_Cost_Pct_of_Total", 
                       "Machinery_Cost_Pct_of_Total", "Crop_Sample_Size_Category"]
    print(df[key_cols_sample].head(5).to_string())

if __name__ == "__main__":
    main()
