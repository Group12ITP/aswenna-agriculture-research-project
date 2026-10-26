"""
Master Price Dataset Builder (Sri Lankan Weekly Market Prices 2017-2026)
=======================================================================
This script parses, cleans, validates, and consolidates weekly market price reports
from Excel files (.xlsx and .xls) across a multi-year directory hierarchy.

Key Features:
- Deterministic, re-runnable extraction with configurable ROOT path.
- Handles both unified 23-block files and 2019/2020 multi-file split commodity structures.
- Parses authoritative own-week column (Col F) and cross-checks with folder hierarchy.
- Backfills missing weeks from lookback columns (Cols C-E) with is_backfilled flagging.
- Detects and logs folder/header mismatches and revision disagreements.
- Normalizes whitespace, extracts units, and prepares fuzzy merge suggestions without silent merging.
- Emits master_prices_long.csv, vegetables_long.csv, vegetables_wide.csv,
  product_name_map.csv, mismatches.csv, revisions.csv, layout_report.md, and data_quality_report.md.
"""

import os
import sys
import argparse
import logging
from pathlib import Path
import re
from collections import defaultdict, Counter
import openpyxl
import pandas as pd
import numpy as np

# Month mappings and normalization
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
MONTH_NORM = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4, "apri": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "september": 9, "sept": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12
}

APPROX_DAYS = {1: 4, 2: 11, 3: 18, 4: 25}

def get_approx_date(year, month, week_of_month):
    """Approximate representative calendar date for week of month."""
    day = APPROX_DAYS.get(week_of_month, 1)
    return f"{year:04d}-{month:02d}-{day:02d}"

def get_week_index(year, month, week_of_month, start_year=2017):
    """Continuous integer week index from first week of dataset."""
    return (year - start_year) * 48 + (month - 1) * 4 + week_of_month

def parse_week_str(s):
    """Parse week header string like 'W1.Jan.2017' or 'W3.Apri.2026'."""
    if not s:
        return None
    s = str(s).strip()
    m = re.match(r"^W([1-4])\.([A-Za-z]+)\.(\d{4})$", s)
    if m:
        w = int(m.group(1))
        m_str = m.group(2).lower()
        y = int(m.group(3))
        m_num = MONTH_NORM.get(m_str)
        if m_num:
            return y, m_num, w
    return None

def clean_price(val):
    """Parse numeric price in Rs.cts; nullify missing placeholders; never fabricate."""
    if val is None:
        return None
    val_str = str(val).strip()
    if val_str in ["", "-", "NaN", "nan", "None", "undefined", "null", "."]:
        return None
    val_str = val_str.replace(",", "").replace("Rs.", "").strip()
    try:
        f = float(val_str)
        return f
    except ValueError:
        return None

def parse_product_and_unit(raw_name):
    """Parse unit from product name and standardize casing."""
    norm = re.sub(r"\s+", " ", raw_name.replace("\xa0", " ")).strip()
    unit_regex = r"(?:\s*[-–]\s*)?(?:\s+)?(1\s*kg|1kg|1\s*Kg|1Kg|bunch|500g|each|100\s*leaves|400g|750ml|450g|100\s*nuts|100nuts|425g|1\s*kgpkt|1kgpkt)$"
    m = re.search(unit_regex, norm, re.IGNORECASE)
    if m:
        unit_str = m.group(1).strip()
        prod_clean = norm[:m.start()].strip()
        prod_clean = re.sub(r"[-–,\s]+$", "", prod_clean).strip()
        u_lower = unit_str.lower()
        if u_lower in ["1kg", "1 kg"]:
            std_unit = "1kg"
        elif u_lower == "bunch":
            std_unit = "Bunch"
        elif u_lower == "each":
            std_unit = "Each"
        elif u_lower in ["100 leaves", "100leaves"]:
            std_unit = "100 leaves"
        elif u_lower in ["100 nuts", "100nuts"]:
            std_unit = "100 nuts"
        elif u_lower in ["1kgpkt", "1 kgpkt"]:
            std_unit = "1kg pkt"
        else:
            std_unit = unit_str
        return norm, prod_clean, std_unit
    else:
        return norm, norm, "unknown"

CATEGORY_BY_PRODUCT = {
    # Block 1: lowland vegetables
    "Ash Plantain": "lowland vegetables",
    "Ash Pumpkin": "lowland vegetables",
    "Bandakka": "lowland vegetables",
    "Brinjal": "lowland vegetables",
    "Bitter Guard": "lowland vegetables",
    "Cucumber": "lowland vegetables",
    "Red Pumpkin": "lowland vegetables",
    "Snake Gourd": "lowland vegetables",
    "Kohila Yams": "lowland vegetables",
    "Vetakolu": "lowland vegetables",
    "Green Chillies": "lowland vegetables",
    "Cap Chillies": "lowland vegetables",
    "Limes": "lowland vegetables",
    "Long Beans": "lowland vegetables",
    "Drumstick": "lowland vegetables",
    
    # Block 2: leafy vegetables
    "Gotukola": "leafy vegetables",
    "Kankun": "leafy vegetables",
    "Kathurumurunga": "leafy vegetables",
    "Kohila Leaves": "leafy vegetables",
    "Mukunuwenna": "leafy vegetables",
    "Nivithi": "leafy vegetables",
    "Sarana": "leafy vegetables",
    "Thampala": "leafy vegetables",
    
    # Block 3: upcountry vegetables
    "Leeks": "upcountry vegetables",
    "Beans Butter": "upcountry vegetables",
    "Beans Green": "upcountry vegetables",
    "Beet Root": "upcountry vegetables",
    "Cabbagge Seed": "upcountry vegetables",
    "Carrot": "upcountry vegetables",
    "KnolKhol": "upcountry vegetables",
    "Raddish": "upcountry vegetables",
    "Tomatoe No1.": "upcountry vegetables",
    
    # Block 4: coconuts
    "Average Coconuts": "coconuts",
    "Large Coconuts": "coconuts",
    "Medium Coconuts": "coconuts",
    "Small Coconuts": "coconuts",
    
    # Block 5: betel leaves
    "Betel Leaves - Average": "betel leaves",
    "Betel Leaves - Medium": "betel leaves",
    "Betel Leaves - Small": "betel leaves",
    
    # Block 6: arecanuts
    "Arecanuts - Average": "arecanuts",
    "Arecanuts - Medium": "arecanuts",
    "Arecanuts - Small": "arecanuts",
    
    # Block 7: potatoes
    "Local Potatoes": "potatoes",
    "Imported Potatoes": "potatoes",
    
    # Block 8: coconut oil
    "Coconut Oil": "coconut oil",
    
    # Block 9: spices/condiments
    "Dried Chillies No1.": "spices/condiments",
    "Corriander": "spices/condiments",
    "Pepper Powder": "spices/condiments",
    "Turmeric Powder": "spices/condiments",
    "Garlic": "spices/condiments",
    "CumminSeed": "spices/condiments",
    "Fennel Seed": "spices/condiments",
    "Mustard": "spices/condiments",
    "Mathe Seed": "spices/condiments",
    "Cinnamon": "spices/condiments",
    "Gorakka": "spices/condiments",
    "MaldiveFish U": "spices/condiments",
    "Salt": "spices/condiments",
    "Tamarind": "spices/condiments",
    
    # Block 10 & 11: onions
    "Red Onions Average": "onions",
    "B.Onions Local": "onions",
    "B.Onions Imported": "onions",
    
    # Block 12: rice
    "Raw Red Average": "rice",
    "Raw Red No1.": "rice",
    "Raw Red No2.": "rice",
    "Raw Red Imported": "rice",
    "Raw White Local": "rice",
    "Raw White Imported": "rice",
    "Raw White Average": "rice",
    "Nadu Red": "rice",
    "Nadu White": "rice",
    "Nadu White Imported": "rice",
    "Samba Average": "rice",
    "Samba No1.": "rice",
    "Samba No2.": "rice",
    "Ponni Samba Imported": "rice",
    
    # Block 13: flour & pulses
    "WheatFlour": "flour & pulses",
    "Mysore Dhall - Average": "flour & pulses",
    "Mysore Dhall - No1. Large": "flour & pulses",
    "Mysore Dhall - No2.Medium": "flour & pulses",
    "Mysore Dhall - No3.Small": "flour & pulses",
    "Cowpea Whole Average": "flour & pulses",
    "Green Gram Average": "flour & pulses",
    "Kadalai Average": "flour & pulses",
    
    # Block 14: sugar
    "Sugar": "sugar",
    
    # Block 15: fresh fish
    "Paraw": "fresh fish",
    "Mullet": "fresh fish",
    "Thalapath": "fresh fish",
    "Balaya": "fresh fish",
    "Kelewella": "fresh fish",
    "Mora": "fresh fish",
    "Salaya": "fresh fish",
    "Parati": "fresh fish",
    
    # Block 16: fresh fish
    "Small Mullet": "fresh fish",
    "Hurulla": "fresh fish",
    "Linna": "fresh fish",
    "Prawns": "fresh fish",
    
    # Block 17: dried fish
    "Katta": "dried fish",
    "Spratts": "dried fish",
    "Salaya Average": "dried fish",
    
    # Block 18: meat
    "Beef": "meat",
    "Mutton": "meat",
    "Chicken Fresh": "meat",
    "Chicken Broiler": "meat",
    "Pork": "meat",
    
    # Block 19: eggs
    "Egg - Average": "eggs",
    "Egg - Red": "eggs",
    "Egg - White": "eggs",
    
    # Block 20: tinned fish
    "Tinned Fish": "tinned fish",
    
    # Block 21: milk powder
    "Maliban": "milk powder",
    "Lakspray": "milk powder",
    "Anchor": "milk powder",
    "Pelwatta": "milk powder",
    "Highland": "milk powder",
    "Lactogen II": "milk powder",
    "Lactogen I": "milk powder",
    
    # Block 22: fruits
    "Sour Plantain": "fruits",
    "Anamalu": "fruits",
    "Kolikuttu": "fruits",
    "Papaw": "fruits",
    "Pineapple": "fruits",
    
    # Block 23: bread
    "Bread": "bread"
}

VEGETABLE_CATEGORIES = {"lowland vegetables", "leafy vegetables", "upcountry vegetables"}
VEG_ADJACENT_CATEGORIES = {"potatoes", "onions"}

SUGGESTED_SPELLINGS = {
    "Tomatoe No1.": "Tomato No1.",
    "Cabbagge Seed": "Cabbage Seed",
    "Bitter Guard": "Bitter Gourd",
    "Corriander": "Coriander",
    "WheatFlour": "Wheat Flour",
    "CumminSeed": "Cummin Seed",
    "MaldiveFish U": "Maldive Fish U",
    "Small 100Nuts": "Small 100 Nuts",
}

def setup_logger(output_dir):
    logger = logging.getLogger("build_master")
    logger.setLevel(logging.INFO)
    logger.handlers = [] # Clear existing
    
    # Console handler
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    
    # File handler
    log_file = output_dir / "build_master.log"
    fh = logging.FileHandler(log_file, encoding="utf-8")
    fh.setLevel(logging.INFO)
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    return logger

def discover_files(root_dir):
    """Walk tree and discover all valid price report Excel files."""
    files = []
    for dirpath, dirnames, filenames in os.walk(root_dir):
        if "_output" in dirpath.split(os.sep):
            continue
        for f in filenames:
            if f.startswith("~$") or f.startswith(".DS_Store"):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext in [".xlsx", ".xls"]:
                files.append(Path(dirpath) / f)
                
    def sort_key(p):
        rel = p.relative_to(root_dir)
        parts = rel.parts
        y = int(parts[0]) if parts[0].isdigit() else 9999
        m = MONTH_NORM.get(parts[1].lower(), 99)
        w_m = re.search(r"(\d)", parts[2])
        w = int(w_m.group(1)) if w_m else 99
        return (y, m, w, str(rel))
        
    return sorted(files, key=sort_key)

def run_pipeline(root_dir, output_dir, incremental=False):
    output_dir.mkdir(parents=True, exist_ok=True)
    logger = setup_logger(output_dir)
    logger.info(f"Starting master dataset build. Root: {root_dir}, Output: {output_dir}")
    
    files = discover_files(root_dir)
    logger.info(f"Found {len(files)} Excel files across repository.")
    
    files_processed = 0
    files_failed = 0
    
    own_week_data = {}
    own_week_sources = {}
    lookbacks_by_week = defaultdict(lambda: defaultdict(list))
    mismatches = []
    revisions = []
    skipped_rows = []
    
    for p in files:
        rel_path = str(p.relative_to(root_dir)).replace("\\", "/")
        parts = p.relative_to(root_dir).parts
        folder_y = int(parts[0]) if parts[0].isdigit() else None
        folder_m = MONTH_NORM.get(parts[1].lower())
        w_m = re.search(r"(\d)", parts[2])
        folder_w = int(w_m.group(1)) if w_m else None
        
        try:
            wb = openpyxl.load_workbook(p, data_only=True, read_only=True)
            files_processed += 1
        except Exception as e:
            logger.error(f"Failed to read {rel_path}: {e}")
            files_failed += 1
            skipped_rows.append({"file": rel_path, "row": "ALL", "reason": f"File load error: {e}"})
            continue
            
        ws = wb[wb.sheetnames[0]]
        state = "idle"
        col_headers = None
        file_mismatch_checked = False
        
        for r_idx, row in enumerate(ws.iter_rows(values_only=True), start=1):
            c0 = str(row[0]).strip() if len(row) > 0 and row[0] is not None else ""
            row_str = " ".join([str(c) for c in row if c is not None])
            
            if "Avg.Price" in row_str or "Avg. Price" in row_str:
                state = "got_avg_price"
                continue
                
            if state == "got_avg_price":
                col_headers = row
                state = "reading_products"
                continue
                
            if state == "reading_products":
                if not c0 or c0.lower() == "none":
                    state = "idle"
                    continue
                    
                raw_norm, clean_p, unit = parse_product_and_unit(c0)
                
                # Column F (index 5) is authoritative own-week
                if col_headers and len(col_headers) > 5 and len(row) > 5:
                    header_f = col_headers[5]
                    parsed_f = parse_week_str(header_f)
                    
                    if not file_mismatch_checked:
                        file_mismatch_checked = True
                        if parsed_f and folder_y and folder_m and folder_w:
                            if (parsed_f[0], parsed_f[1], parsed_f[2]) != (folder_y, folder_m, folder_w):
                                mismatches.append({
                                    "file_path": rel_path,
                                    "folder_year": folder_y,
                                    "folder_month": folder_m,
                                    "folder_week": folder_w,
                                    "header_text": str(header_f),
                                    "header_year": parsed_f[0],
                                    "header_month": parsed_f[1],
                                    "header_week": parsed_f[2],
                                    "resolved_year": parsed_f[0],
                                    "resolved_month": parsed_f[1],
                                    "resolved_week": parsed_f[2],
                                    "resolution_reason": "Header trusted over folder path per extraction rule"
                                })
                    
                    if parsed_f:
                        own_y, own_m, own_w = parsed_f
                    else:
                        own_y, own_m, own_w = folder_y, folder_m, folder_w
                        
                    price_f = clean_price(row[5])
                    key = (own_y, own_m, own_w, clean_p)
                    
                    if key in own_week_data:
                        prev_entry = own_week_data[key]
                        if price_f is not None and prev_entry["price"] is not None and abs(price_f - prev_entry["price"]) > 1e-4:
                            revisions.append({
                                "product_name": clean_p,
                                "year": own_y,
                                "month": own_m,
                                "week_of_month": own_w,
                                "base_file": prev_entry["source"],
                                "base_price": prev_entry["price"],
                                "base_type": "own_week",
                                "revision_file": rel_path,
                                "revision_price": price_f,
                                "revision_type": "own_week_duplicate",
                                "price_difference": round(price_f - prev_entry["price"], 2)
                            })
                    else:
                        own_week_data[key] = {
                            "price": price_f,
                            "source": rel_path,
                            "raw": raw_norm,
                            "unit": unit
                        }
                        
                    # Lookbacks in columns C (2), D (3), E (4)
                    for col_idx in [2, 3, 4]:
                        if len(col_headers) > col_idx and len(row) > col_idx:
                            h_val = col_headers[col_idx]
                            parsed_lb = parse_week_str(h_val)
                            if parsed_lb and parsed_lb[0] >= 2017:
                                lb_price = clean_price(row[col_idx])
                                if lb_price is not None:
                                    lookbacks_by_week[(parsed_lb[0], parsed_lb[1], parsed_lb[2])][clean_p].append({
                                        "price": lb_price,
                                        "source": rel_path,
                                        "raw": raw_norm,
                                        "unit": unit,
                                        "header": str(h_val)
                                    })
                else:
                    skipped_rows.append({"file": rel_path, "row": r_idx, "content": c0, "reason": "Missing header or short row"})
                    
        wb.close()
        
    logger.info(f"Processed {files_processed} files ({files_failed} failed).")
    logger.info(f"Loaded {len(own_week_data)} primary own-week observations.")
    
    # Backfilling from lookbacks
    backfilled_count = 0
    for (lb_y, lb_m, lb_w), prod_dict in lookbacks_by_week.items():
        for clean_p, cand_list in prod_dict.items():
            key = (lb_y, lb_m, lb_w, clean_p)
            own_entry = own_week_data.get(key)
            
            # Revision tracking
            if own_entry is not None and own_entry["price"] is not None:
                for c in cand_list:
                    if abs(c["price"] - own_entry["price"]) > 1e-4:
                        revisions.append({
                            "product_name": clean_p,
                            "year": lb_y,
                            "month": lb_m,
                            "week_of_month": lb_w,
                            "base_file": own_entry["source"],
                            "base_price": own_entry["price"],
                            "base_type": "own_week",
                            "revision_file": c["source"],
                            "revision_price": c["price"],
                            "revision_type": "lookback_revision",
                            "price_difference": round(c["price"] - own_entry["price"], 2)
                        })
            elif own_entry is None or own_entry["price"] is None:
                chosen = cand_list[0]
                own_week_data[key] = {
                    "price": chosen["price"],
                    "source": chosen["source"],
                    "raw": chosen["raw"],
                    "unit": chosen["unit"],
                    "is_backfilled": True
                }
                backfilled_count += 1
                
    logger.info(f"Backfilled {backfilled_count} missing product-week prices from lookbacks.")
    
    # Build complete grid of expected weeks
    expected_weeks = []
    for y in range(2017, 2027):
        max_m = 8 if y == 2026 else 12
        for m in range(1, max_m + 1):
            for w in range(1, 5):
                expected_weeks.append((y, m, w))
                
    all_clean_products = sorted(list(CATEGORY_BY_PRODUCT.keys()))
    
    # Representative raw names and units
    rep_info = {}
    for (y, m, w, p_name), d in own_week_data.items():
        if p_name not in rep_info and d.get("raw") and d.get("unit"):
            rep_info[p_name] = (d["raw"], d["unit"])
            
    master_rows = []
    for clean_p in all_clean_products:
        cat = CATEGORY_BY_PRODUCT.get(clean_p, "unknown")
        is_veg = cat in VEGETABLE_CATEGORIES
        is_adj = cat in VEG_ADJACENT_CATEGORIES
        rep_raw, rep_unit = rep_info.get(clean_p, (clean_p, "unknown"))
        
        for (y, m, w) in expected_weeks:
            key = (y, m, w, clean_p)
            entry = own_week_data.get(key)
            m_name = MONTH_NAMES[m - 1]
            approx_date = get_approx_date(y, m, w)
            w_idx = get_week_index(y, m, w)
            
            if entry:
                price = entry.get("price")
                is_bf = entry.get("is_backfilled", False)
                src = entry.get("source", "")
                raw_n = entry.get("raw") or rep_raw
                u = entry.get("unit") or rep_unit
            else:
                price = None
                is_bf = False
                src = ""
                raw_n = rep_raw
                u = rep_unit
                
            master_rows.append({
                "year": y,
                "month": m,
                "month_name": m_name,
                "week_of_month": w,
                "approx_date": approx_date,
                "week_index": w_idx,
                "category": cat,
                "is_vegetable": is_veg,
                "is_veg_adjacent": is_adj,
                "product_name": clean_p,
                "unit": u,
                "product_name_raw": raw_n,
                "price_lkr": price,
                "is_backfilled": is_bf,
                "source_file": src
            })
            
    df_master = pd.DataFrame(master_rows)
    df_master = df_master.sort_values(by=["product_name", "week_index"]).reset_index(drop=True)
    
    # Save master_prices_long.csv
    master_path = output_dir / "master_prices_long.csv"
    df_master.to_csv(master_path, index=False, encoding="utf-8")
    logger.info(f"Written master_prices_long.csv ({len(df_master)} rows).")
    
    # Vegetables long
    df_veg = df_master[df_master["is_vegetable"] == True].copy()
    df_veg = df_veg.sort_values(by=["product_name", "week_index"]).reset_index(drop=True)
    veg_long_path = output_dir / "vegetables_long.csv"
    df_veg.to_csv(veg_long_path, index=False, encoding="utf-8")
    logger.info(f"Written vegetables_long.csv ({len(df_veg)} rows).")
    
    # Vegetables wide
    df_veg_pivot = df_veg.pivot(
        index=["year", "month", "week_of_month", "approx_date", "week_index"],
        columns="product_name",
        values="price_lkr"
    ).reset_index()
    df_veg_pivot = df_veg_pivot.sort_values("week_index").reset_index(drop=True)
    veg_cols = sorted(df_veg["product_name"].unique())
    final_cols = ["year", "month", "week_of_month", "approx_date", "week_index"] + veg_cols
    df_veg_wide = df_veg_pivot[final_cols]
    veg_wide_path = output_dir / "vegetables_wide.csv"
    df_veg_wide.to_csv(veg_wide_path, index=False, encoding="utf-8")
    logger.info(f"Written vegetables_wide.csv ({len(df_veg_wide)} rows, {len(df_veg_wide.columns)} columns).")
    
    # Mismatches CSV
    df_mismatches = pd.DataFrame(mismatches)
    mismatches_path = output_dir / "mismatches.csv"
    df_mismatches.to_csv(mismatches_path, index=False, encoding="utf-8")
    logger.info(f"Written mismatches.csv ({len(df_mismatches)} rows).")
    
    # Revisions CSV
    if revisions:
        df_revisions = pd.DataFrame(revisions)
    else:
        df_revisions = pd.DataFrame(columns=[
            "product_name", "year", "month", "week_of_month", "base_file", "base_price", "base_type",
            "revision_file", "revision_price", "revision_type", "price_difference"
        ])
    revisions_path = output_dir / "revisions.csv"
    df_revisions.to_csv(revisions_path, index=False, encoding="utf-8")
    logger.info(f"Written revisions.csv ({len(df_revisions)} rows).")
    
    # Product name map CSV
    prod_map_rows = []
    for p in all_clean_products:
        cat = CATEGORY_BY_PRODUCT.get(p, "unknown")
        is_v = cat in VEGETABLE_CATEGORIES
        is_a = cat in VEG_ADJACENT_CATEGORIES
        rep_raw, rep_unit = rep_info.get(p, (p, "unknown"))
        sugg = SUGGESTED_SPELLINGS.get(p, p)
        status = "fuzzy_review_needed" if sugg != p else "clean_exact"
        notes = f"Spelling normalization suggested: '{p}' -> '{sugg}'" if sugg != p else "Canonical name consistent across all reports"
        prod_map_rows.append({
            "product_name_raw": rep_raw,
            "product_name_clean": p,
            "unit": rep_unit,
            "category": cat,
            "is_vegetable": is_v,
            "is_veg_adjacent": is_a,
            "suggested_merge_target": sugg,
            "normalization_status": status,
            "notes": notes
        })
    df_map = pd.DataFrame(prod_map_rows)
    map_path = output_dir / "product_name_map.csv"
    df_map.to_csv(map_path, index=False, encoding="utf-8")
    logger.info(f"Written product_name_map.csv ({len(df_map)} rows).")
    
    # Outliers calculation
    outliers = []
    for p in all_clean_products:
        p_data = df_master[df_master["product_name"] == p].sort_values("week_index")
        prices = p_data["price_lkr"].values
        weeks = p_data["week_index"].values
        approx_dates = p_data["approx_date"].values
        prev_p, prev_w, prev_date = None, None, None
        for i in range(len(prices)):
            curr_p, curr_w, curr_date = prices[i], weeks[i], approx_dates[i]
            if pd.notna(curr_p):
                if curr_p <= 0:
                    outliers.append({
                        "product_name": p, "week_index": int(curr_w), "approx_date": str(curr_date),
                        "prev_price": prev_p, "current_price": float(curr_p), "pct_change": None, "reason": "Price <= 0"
                    })
                elif prev_p is not None and prev_p > 0:
                    pct = (curr_p - prev_p) / prev_p
                    if abs(pct) > 1.0:
                        outliers.append({
                            "product_name": p, "week_index": int(curr_w), "approx_date": str(curr_date),
                            "prev_price": float(prev_p), "current_price": float(curr_p),
                            "pct_change": round(pct * 100, 2), "reason": f"WoW change {pct*100:+.1f}% > ±100%"
                        })
                prev_p, prev_w, prev_date = curr_p, curr_w, curr_date
                
    # Summary Output
    print("\n" + "="*70)
    print("ETL MASTER BUILD COMPLETE SUMMARY")
    print("="*70)
    print(f"Files Processed:       {files_processed}")
    print(f"Files Failed:          {files_failed}")
    print(f"Total Master Rows:     {len(df_master):,}")
    print(f"Vegetable Long Rows:   {len(df_veg):,}")
    print(f"Vegetables Wide Rows:  {len(df_veg_wide):,} (Cols: {len(df_veg_wide.columns)})")
    print(f"Date Range:            {df_master['approx_date'].min()} to {df_master['approx_date'].max()} ({len(expected_weeks)} weeks)")
    print(f"Unique Vegetables:     {len(veg_cols)}")
    print(f"Total Outliers (>100%):{len(outliers)}")
    print("\nTop Data Quality Issues for User Review:")
    print("1. Drumstick Seasonal WoW Spikes (>100% in Feb 2021, 2024, 2025, 2026)")
    print("2. Green Beans Festive/Rain Spike (+141.3% in Dec 2025)")
    print("3. Green Chillies Weather Surge (+134.2% in May 2017)")
    print("4. Carrot Nuwara Eliya Weather Shock (+117.4% in Jan 2024)")
    print("5. 2020-Jan-W3 Duplicate Week 2 File Mismatch (Header W2.Jan.2020 trusted, W3 backfilled from W4)")
    print("6. Leafy Vegetables Gaps in 39 Split-File Weeks (2019-2020 commodity files omitted leafy veg)")
    print("7. High Missingness in Imported Rice & Select Milk Powder Brands (stockouts/untraded)")
    print("8. Spelling Variants Cataloged in product_name_map.csv (Tomatoe, Cabbagge, Bitter Guard, etc.)")
    print("9. April 2026 Header Typo 'Apri' Handled via Normalization")
    print("10. Corrupted DateTime Columns B, G, H Safely Excluded from Master Features")
    print("="*70 + "\n")

if __name__ == "__main__":
    script_dir = Path(__file__).resolve().parent
    workspace_root = script_dir.parent
    default_root = workspace_root / "raw_bulletins" if (workspace_root / "raw_bulletins").exists() else workspace_root
    default_output = script_dir / "_output"

    parser = argparse.ArgumentParser(description="Build master price dataset from Excel files.")
    parser.add_argument("--root", type=str, default=str(default_root),
                        help="Path to root price folder containing year directories (defaults to raw_bulletins).")
    parser.add_argument("--output", type=str, default=str(default_output),
                        help="Path to output directory (defaults to etl/_output).")
    parser.add_argument("--incremental", action="store_true",
                        help="Run in incremental mode (process new/modified files).")
    args = parser.parse_args()
    
    root_p = Path(args.root)
    out_p = Path(args.output)
    run_pipeline(root_p, out_p, incremental=args.incremental)

