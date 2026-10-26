#!/usr/bin/env python3
"""
Deduplication and Feature Regeneration Pipeline
===============================================
Investigates suspected duplicate records across seasons in coc_features.csv,
removes duplicate placeholder records, and regenerates all downstream
features for ML training.
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

def main():
    print("=" * 80)
    print("STEP 1: Reading coc_features.csv & Defining Duplicate Key")
    print("=" * 80)
    workspace = Path(__file__).resolve().parent.parent
    if not (workspace / "data").exists():
        workspace = Path(r"c:\Users\MSI\Desktop\Research\COC folder")
    data_dir = workspace / "data" / "processed" if (workspace / "data" / "processed").exists() else workspace
    input_csv = data_dir / "coc_features.csv"
    output_csv = data_dir / "coc_features_dedup.csv"
    
    if not input_csv.exists():
        print(f"Error: {input_csv} does not exist!")
        sys.exit(1)
        
    df = pd.read_csv(input_csv)
    print(f"Decision: Loaded {len(df)} rows and {len(df.columns)} columns from {input_csv.name}.")
    
    # Define duplicate key
    dup_cols = [
        "Crop", "District", "Irrigation_Type",
        "Total_Cost_Incl_Imputed", "Labour_Cost", "Machinery_Cost", "Material_Cost",
        "Average_Yield_kg_ac", "Price_of_Produce"
    ]
    print(f"Decision: Duplicate key defined across 9 columns:")
    for c in dup_cols:
        print(f"  - {c}")

    # --------------------------------------------------------------------------
    # STEP 2: Find ALL Duplicate Groups
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 2: Scanning for Cross-Season Duplicates")
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

    # Groupby with dropna=False
    groups = df.groupby(dup_cols, dropna=False)
    dup_groups = []
    
    for k, grp in groups:
        if len(grp) > 1:
            dup_groups.append(grp)
            
    total_dup_groups = len(dup_groups)
    total_affected_rows = sum(len(g) for g in dup_groups)
    
    print(f"Duplicate Scan Results:")
    print(f"  - Total duplicate groups found : {total_dup_groups}")
    print(f"  - Total rows affected          : {total_affected_rows}")
    print("\nDetailed Listing of Duplicate Groups:")
    
    for i, grp in enumerate(dup_groups, 1):
        c = grp['Crop'].iloc[0]
        d = grp['District'].iloc[0]
        irr = grp['Irrigation_Type'].iloc[0]
        years_involved = sorted(grp['Year_Start'].unique().tolist())
        print(f"\nGroup {i:2d}: Crop='{c}', District='{d}', Irrigation='{irr}' | Year_Start involved: {years_involved}")
        for idx, r in grp.iterrows():
            print(f"   [Row {idx:3d}] Season: {r['Season']:4s} {r['Year_Range']:7s} (Year_Start {r['Year_Start']}) | "
                  f"Cost: Rs {r['Total_Cost_Incl_Imputed']:,.1f} | Yield: {r['Average_Yield_kg_ac']} kg | Price: Rs {r['Price_of_Produce']} | "
                  f"File: '{r['Source_File']}' | Sheet: '{r['Source_Sheet']}'")

    # --------------------------------------------------------------------------
    # STEP 3: Per-Crop Duplicate Summary Table
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 3: Per-Crop Duplicate Summary Table")
    print("=" * 80)
    df_affected = pd.concat(dup_groups)
    crop_counts_affected = df_affected.groupby("Crop").size().reset_index(name="Affected_Rows")
    crop_counts_affected["Duplicate_Groups"] = [
        sum(1 for g in dup_groups if g["Crop"].iloc[0] == c) for c in crop_counts_affected["Crop"]
    ]
    crop_counts_affected["Rows_To_Drop"] = crop_counts_affected["Affected_Rows"] - crop_counts_affected["Duplicate_Groups"]
    crop_counts_affected = crop_counts_affected.sort_values(by="Affected_Rows", ascending=False).reset_index(drop=True)
    
    print(crop_counts_affected.to_string(index=False))

    # --------------------------------------------------------------------------
    # STEP 4: Deduplication Rule Execution
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 4: Applying Deduplication Rule")
    print("=" * 80)
    print("Decision: Deduplication Rule Applied:")
    print("  - For each duplicate group, sort occurrences chronologically by season timeline (_season_order_idx).")
    print("  - KEEP the row from the LATER season (e.g. '2015-16 Maha' from authoritative workbook '2015-2016 Maha.xlsx').")
    print("  - DROP the earlier season row (e.g. '2015 Yala' placeholder from '2015Y-COC-DC-OFC-final sheet - Copy.xlsx').")
    print("  - If both rows have the exact same season, keep the first occurrence.")

    drop_indices = []
    for grp in dup_groups:
        grp_sorted = grp.sort_values(by="_season_order_idx")
        # Keep the latest season (last row), drop all earlier ones
        drop_indices.extend(grp_sorted.index[:-1].tolist())

    print(f"Decision: Identified {len(drop_indices)} earlier placeholder rows to drop:")
    for d_idx in drop_indices:
        r = df.loc[d_idx]
        print(f"  - Dropping Row {d_idx:3d}: {r['Crop']:12s} in {r['District']:15s} | Season: {r['Season']:4s} {r['Year_Range']:7s} | File: '{r['Source_File']}'")

    # Drop rows
    df_clean = df.drop(index=drop_indices).reset_index(drop=True)
    print(f"Decision: Dropped {len(drop_indices)} rows. Dataset reduced from {len(df)} to {len(df_clean)} rows.")

    # --------------------------------------------------------------------------
    # STEP 5: Regenerate Downstream Features
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 5: Regenerating Downstream Features on Cleaned Data")
    print("=" * 80)
    
    # 5.1 Re-sort chronologically within each group
    group_cols = ["Crop", "District", "Irrigation_Type"]
    print(f"Decision: Re-sorting cleaned dataset by {group_cols}, Year_Start, and Season Chronological Order.")
    df_clean = df_clean.sort_values(by=["Crop", "District", "Irrigation_Type", "Year_Start", "_season_order_idx"]).reset_index(drop=True)
    
    # 5.2 Re-compute Lag Features
    print("Decision: Re-computing group-level lag features (Prev_Season_Total_Cost_Incl_Imputed, Prev_Season_Year, Cost_Pct_Change_From_Prev_Season).")
    g_clean = df_clean.groupby(group_cols, dropna=False)
    
    df_clean["Prev_Season_Total_Cost_Incl_Imputed"] = g_clean["Total_Cost_Incl_Imputed"].shift(1)
    df_clean["Prev_Season_Year"] = g_clean["Year_Start"].shift(1)
    
    prev_cost = df_clean["Prev_Season_Total_Cost_Incl_Imputed"]
    curr_cost = df_clean["Total_Cost_Incl_Imputed"]
    df_clean["Cost_Pct_Change_From_Prev_Season"] = np.where(
        prev_cost.notna() & (prev_cost > 0),
        ((curr_cost - prev_cost) / prev_cost) * 100.0,
        np.nan
    )
    
    # 5.3 Re-compute Ratio Features
    print("Decision: Re-computing cost component ratios guarded against divide-by-zero.")
    tot_cost = df_clean["Total_Cost_Incl_Imputed"].replace(0, np.nan)
    df_clean["Fertilizer_Cost_Pct_of_Total"] = df_clean["Material_Cost"] / tot_cost
    df_clean["Labour_Cost_Pct_of_Total"] = df_clean["Labour_Cost"] / tot_cost
    df_clean["Machinery_Cost_Pct_of_Total"] = df_clean["Machinery_Cost"] / tot_cost
    
    # 5.4 Re-assign Crop_Sample_Size_Category
    print("Decision: Re-assigning 'Crop_Sample_Size_Category' ('High' >= 15, 'Medium' 5-14, 'Low' < 5) on deduplicated dataset.")
    crop_counts_updated = df_clean["Crop"].value_counts()
    
    def get_updated_category(crop_name):
        cnt = crop_counts_updated.get(crop_name, 0)
        if cnt >= 15:
            return "High"
        elif 5 <= cnt <= 14:
            return "Medium"
        else:
            return "Low"
            
    df_clean["Crop_Sample_Size_Category"] = df_clean["Crop"].apply(get_updated_category)
    
    # Drop temporary sorting helper column
    df_clean = df_clean.drop(columns=["_season_order_idx"])

    # --------------------------------------------------------------------------
    # STEP 6: Save Cleaned Dataset
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 6: Saving Cleaned Dataset as coc_features_dedup.csv")
    print("=" * 80)
    df_clean.to_csv(output_csv, index=False, encoding="utf-8-sig")
    print(f"Decision: Saved cleaned dataset to {output_csv.name} (coc_features.csv preserved as backup).")

    # --------------------------------------------------------------------------
    # STEP 7: Validation Reporting
    # --------------------------------------------------------------------------
    print("\n" + "=" * 80)
    print("STEP 7: Validation Reporting")
    print("=" * 80)
    
    print(f"1. Dataset Shapes:")
    print(f"   - Original coc_features.csv : {df.shape}")
    print(f"   - Cleaned coc_features_dedup.csv : {df_clean.shape}")
    print(f"   - Duplicate rows removed    : {len(drop_indices)}")

    print("\n2. Updated Crop-Count Table with Categories:")
    crop_table_updated = pd.DataFrame({
        "Crop": crop_counts_updated.index,
        "Record_Count": crop_counts_updated.values,
        "Crop_Sample_Size_Category": [get_updated_category(c) for c in crop_counts_updated.index]
    })
    print(crop_table_updated.to_string(index=False))
    
    print("\n3. Category Level Summary:")
    cat_summary = crop_table_updated.groupby("Crop_Sample_Size_Category").agg(
        Crops_Count=("Crop", "count"),
        Rows_Count=("Record_Count", "sum")
    ).loc[["High", "Medium", "Low"]]
    print(cat_summary.to_string())

    print("\n4. Updated Null-Count Summary for Lag and Ratio Columns:")
    lag_cols = [
        "Prev_Season_Total_Cost_Incl_Imputed",
        "Prev_Season_Year",
        "Cost_Pct_Change_From_Prev_Season",
        "Fertilizer_Cost_Pct_of_Total",
        "Labour_Cost_Pct_of_Total",
        "Machinery_Cost_Pct_of_Total",
        "Crop_Sample_Size_Category"
    ]
    for lc in lag_cols:
        nc = df_clean[lc].isnull().sum()
        pct = (nc / len(df_clean)) * 100.0
        print(f"   {lc:35s}: {nc:4d} nulls ({pct:5.2f}%)")

    # 5. Check if any group became single-season-only
    df_before_g = df.groupby(group_cols, dropna=False).size().reset_index(name="count_before")
    df_after_g = df_clean.groupby(group_cols, dropna=False).size().reset_index(name="count_after")
    merged_g = df_before_g.merge(df_after_g, on=group_cols, how="left")
    merged_g["count_after"] = merged_g["count_after"].fillna(0).astype(int)
    
    became_single = merged_g[(merged_g["count_before"] >= 2) & (merged_g["count_after"] == 1)]
    print(f"\n5. Groups that became single-season-only after dedup: {len(became_single)}")
    if len(became_single) > 0:
        for _, r in became_single.iterrows():
            print(f"   - {r['Crop']} | {r['District']} | {r['Irrigation_Type']} (was {r['count_before']} -> now {r['count_after']})")
    else:
        print("   -> None! All 71 multi-season groups continue to have at least 2 seasons.")

    print(f"\n6. Summary Statement:")
    valid_lag = df_clean["Prev_Season_Total_Cost_Incl_Imputed"].notna().sum()
    invalid_lag = df_clean["Prev_Season_Total_Cost_Incl_Imputed"].isna().sum()
    print(f"   \"{valid_lag} rows have a valid Prev_Season_Total_Cost_Incl_Imputed, {invalid_lag} rows do not.\"")

if __name__ == "__main__":
    main()
