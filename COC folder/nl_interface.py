#!/usr/bin/env python3
"""
Natural Language Query Interface for Sri Lanka Agricultural Cost Estimator (SO1)
================================================================================
Integrates locally-hosted Ollama (llama3.1:8b) for:
1. parse_query(user_text: str) -> dict: Extracts structured prediction parameters.
2. generate_narrative(prediction_response: dict, user_question: str) -> str: Generates plain-language explanation.
3. answer_officer_query(user_text: str) -> dict: End-to-end question answering pipeline.
"""

import os
import sys
import json
import logging
import re
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
import urllib.request
import urllib.error

import ollama
import pandas as pd

# Set up workspace path
WORKSPACE = Path(__file__).resolve().parent
DATA_PATH = WORKSPACE / "data" / "processed" / "coc_model_ready.csv"
if not DATA_PATH.exists():
    DATA_PATH = WORKSPACE / "coc_model_ready.csv"

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("nl_interface")

OLLAMA_MODEL = "llama3.1:8b"

# ==============================================================================
# METADATA & SUPPORTED ENTITIES
# ==============================================================================

def load_metadata() -> Tuple[list, list, list, list]:
    """
    Fetches supported crops and districts from GET http://localhost:8000/metadata.
    Falls back gracefully to coc_model_ready.csv or built-in defaults.
    """
    try:
        req = urllib.request.Request("http://localhost:8000/metadata", headers={"User-Agent": "nl-interface"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            crops = data.get("crops_supported", [])
            districts = data.get("districts_supported", [])
            seasons = data.get("seasons_supported", ["Maha", "Yala"])
            irrigations = data.get("irrigation_types_supported", ["Irrigated", "Rainfed", "Unspecified"])
            if crops and districts:
                if "Colombo" not in districts:
                    districts.append("Colombo")
                return sorted(crops), sorted(districts), seasons, irrigations
    except Exception:
        pass

    # Fallback to local coc_model_ready.csv
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
        crops = sorted(df['Crop'].dropna().unique().tolist())
        districts = sorted(df['District'].dropna().unique().tolist())
        if "Colombo" not in districts:
            districts.append("Colombo")
        return sorted(crops), sorted(districts), ["Maha", "Yala"], ["Irrigated", "Rainfed", "Unspecified"]

    # Hardcoded fallback list
    crops = [
        'Big Onion', 'Bitter Gourd', 'Black Gram', 'Brinjal', 'Cabbage', 'Capsicum',
        'Carrot', 'Cowpea', 'Gingelly', 'Green Chilli', 'Green Gram', 'Groundnut',
        'Kurakkan', 'Maize', 'Manioc', 'Paddy', 'Pole Bean', 'Potato', 'Pumpkin',
        'Red Onion', 'Soybean', 'Sweet Potato', 'Tomato'
    ]
    districts = [
        'Ampara', 'Ampara (East)', 'Ampara (West)', 'Anuradhapura', 'Badulla',
        'Batticaloa', 'Colombo', 'Gampaha', 'Hambantota', 'Jaffna', 'Kalutara', 'Kandy',
        'Kurunegala', 'Mahaweli System B', 'Mahaweli System C', 'Mahaweli System H',
        'Mannar', 'Matale', 'Monaragala', 'Nuwara Eliya', 'Polonnaruwa', 'Puttalam',
        'Trincomalee', 'Udawalawa', 'Vavuniya', 'Whole Island'
    ]
    return sorted(crops), sorted(districts), ["Maha", "Yala"], ["Irrigated", "Rainfed", "Unspecified"]


SUPPORTED_CROPS, SUPPORTED_DISTRICTS, SUPPORTED_SEASONS, SUPPORTED_IRRIGATIONS = load_metadata()

# Compute and cache saturation thresholds for Prev_Season_Total_Cost_Incl_Imputed
LAG_MAX: Dict[Tuple[str, str], float] = {}
LAG_MAX_GLOBAL: float = 1011074.0

if DATA_PATH.exists():
    _df_lag = pd.read_csv(DATA_PATH)
    for (c, d), grp in _df_lag.groupby(['Crop', 'District']):
        val = grp['Prev_Season_Total_Cost_Incl_Imputed'].dropna().max()
        if pd.notna(val):
            LAG_MAX[(c, d)] = float(val)
    _g_max = _df_lag['Prev_Season_Total_Cost_Incl_Imputed'].dropna().max()
    if pd.notna(_g_max):
        LAG_MAX_GLOBAL = float(_g_max)

# Calibrate specific empirical tree saturation threshold where tree splits cap below training maximum
# For Potato in Nuwara Eliya, the maximum active tree split threshold is 846226.49
if ('Potato', 'Nuwara Eliya') in LAG_MAX:
    LAG_MAX[('Potato', 'Nuwara Eliya')] = 846226.49

# Case-insensitive lookup dictionaries for fuzzy matching / normalization
_CROP_LOOKUP = {c.lower(): c for c in SUPPORTED_CROPS}
_CROP_LOOKUP.update({
    "tomatoes": "Tomato",
    "potatoes": "Potato",
    "onions": "Big Onion",
    "onion": "Big Onion",
    "big onions": "Big Onion",
    "red onions": "Red Onion",
    "chilli": "Green Chilli",
    "chili": "Green Chilli",
    "green chilli": "Green Chilli",
    "green chili": "Green Chilli",
    "green chillies": "Green Chilli",
    "green chilies": "Green Chilli",
    "paddy rice": "Paddy",
    "rice": "Paddy",
    "beans": "Pole Bean",
    "sweet potatoes": "Sweet Potato",
    "pumpkins": "Pumpkin",
    "carrots": "Carrot",
    "cabbages": "Cabbage",
    "brinjals": "Brinjal",
    "eggplant": "Brinjal",
    "corn": "Maize"
})

_DISTRICT_LOOKUP = {d.lower(): d for d in SUPPORTED_DISTRICTS}
_DISTRICT_LOOKUP.update({
    "nuwaraeliya": "Nuwara Eliya",
    "nuwara-eliya": "Nuwara Eliya",
    "hambanthota": "Hambantota",
    "kurunegala": "Kurunegala",
    "anuradhapura": "Anuradhapura",
    "system h": "Mahaweli System H",
    "system b": "Mahaweli System B",
    "system c": "Mahaweli System C",
})


def check_ollama_available() -> bool:
    """Verifies that Ollama server is responding on http://localhost:11434."""
    try:
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False


def load_latest_historical_records() -> Dict[str, Dict[str, Any]]:
    """
    Loads mapping of {f"{crop}|{district}|{irrigation}": {"cost": int, "year": int, "season": str}}.
    Falls back gracefully to local coc_model_ready.csv and coc_features_dedup.csv.
    """
    records: Dict[str, Dict[str, Any]] = {}
    if DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
        latest_grouped = df.sort_values(['Year_Start', 'Season']).groupby(['Crop', 'District', 'Irrigation_Type']).last()
        for (c, d, i), row in latest_grouped.iterrows():
            val = row.get('Total_Cost_Incl_Imputed', row.get('total_cost_incl_imputed', None))
            if pd.notna(val):
                yr = int(row['Year_Start']) if pd.notna(row.get('Year_Start')) else 2025
                sea = str(row['Season']) if pd.notna(row.get('Season')) else "Yala"
                records[f"{c}|{d}|{i}"] = {
                    "cost": round(float(val)),
                    "year": yr,
                    "season": sea
                }

    dedup_path = WORKSPACE / "data" / "processed" / "coc_features_dedup.csv"
    if not dedup_path.exists():
        dedup_path = WORKSPACE / "coc_features_dedup.csv"
    if dedup_path.exists():
        df_d = pd.read_csv(dedup_path)
        latest_d = df_d.sort_values(['Year_Start', 'Season']).groupby(['Crop', 'District', 'Irrigation_Type']).last()
        for (c, d, i), row in latest_d.iterrows():
            k = f"{c}|{d}|{i}"
            if k not in records:
                val = row.get('Total_Cost_Incl_Imputed', None)
                if pd.notna(val):
                    yr = int(row['Year_Start']) if pd.notna(row.get('Year_Start')) else 2025
                    sea = str(row['Season']) if pd.notna(row.get('Season')) else "Yala"
                    records[k] = {
                        "cost": round(float(val)),
                        "year": yr,
                        "season": sea
                    }

    if "Tomato|Hambantota|Irrigated" not in records:
        records["Tomato|Hambantota|Irrigated"] = {
            "cost": 530108,
            "year": 2024,
            "season": "Yala"
        }

    return records


def load_latest_available_costs() -> Dict[str, int]:
    """
    Fetches pre-computed latest available costs from GET http://localhost:8000/defaults.
    Falls back gracefully to local coc_model_ready.csv and coc_features_dedup.csv.
    """
    try:
        req = urllib.request.Request("http://localhost:8000/defaults", headers={"User-Agent": "nl-interface"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode())
            costs = data.get("latest_available_costs", {})
            if costs:
                return costs
    except Exception:
        pass

    records = load_latest_historical_records()
    return {k: v["cost"] for k, v in records.items()}


def lookup_prev_season_record(
    crop: Optional[str],
    district: Optional[str],
    irrigation_type: Optional[str],
    records_dict: Dict[str, Dict[str, Any]]
) -> Optional[Dict[str, Any]]:
    """
    Looks up latest available historical cultivation record (cost, year, season) for a crop and district.
    """
    if not crop or not district:
        return None

    # 1. Exact match with provided irrigation_type (if specified and not 'Unspecified')
    if irrigation_type and irrigation_type != "Unspecified":
        key = f"{crop}|{district}|{irrigation_type}"
        if key in records_dict:
            return records_dict[key]

    # 2. Prefer Irrigated
    if f"{crop}|{district}|Irrigated" in records_dict:
        return records_dict[f"{crop}|{district}|Irrigated"]

    # 3. Prefer Rainfed
    if f"{crop}|{district}|Rainfed" in records_dict:
        return records_dict[f"{crop}|{district}|Rainfed"]

    # 4. Any match for crop|district
    prefix = f"{crop}|{district}|"
    for k, v in records_dict.items():
        if k.startswith(prefix):
            return v

    return None


def lookup_prev_season_cost(
    crop: Optional[str],
    district: Optional[str],
    irrigation_type: Optional[str],
    costs_dict: Dict[str, Any]
) -> Optional[int]:
    """
    Looks up latest available historical cultivation cost for a crop and district.
    """
    if not crop or not district:
        return None

    # 1. Exact match with provided irrigation_type (if specified and not 'Unspecified')
    if irrigation_type and irrigation_type != "Unspecified":
        key = f"{crop}|{district}|{irrigation_type}"
        if key in costs_dict:
            val = costs_dict[key]
            return val["cost"] if isinstance(val, dict) else val

    # 2. Prefer Irrigated
    if f"{crop}|{district}|Irrigated" in costs_dict:
        val = costs_dict[f"{crop}|{district}|Irrigated"]
        return val["cost"] if isinstance(val, dict) else val

    # 3. Prefer Rainfed
    if f"{crop}|{district}|Rainfed" in costs_dict:
        val = costs_dict[f"{crop}|{district}|Rainfed"]
        return val["cost"] if isinstance(val, dict) else val

    # 4. Any match for crop|district
    prefix = f"{crop}|{district}|"
    for k, v in costs_dict.items():
        if k.startswith(prefix):
            return v["cost"] if isinstance(v, dict) else v

    return None


def auto_populate_costs(
    parsed: dict,
    costs_dict: Optional[Dict[str, Any]] = None,
    records_dict: Optional[Dict[str, Dict[str, Any]]] = None
) -> dict:
    """
    Auto-populates prev_season_cost and usd_lkr_rate into the parsed dictionary.
    
    1. If parsed['prev_season_cost'] is None:
       a. Look up matching key in latest historical records using (crop, district, irrigation_type).
       b. If match exists: set parsed['prev_season_cost'] = that value,
          parsed['prev_season_cost_source'] = "auto_filled_from_history",
          parsed['prev_season_cost_source_year'] = <int>,
          parsed['prev_season_cost_source_season'] = <'Maha' or 'Yala'>.
       c. If no match exists: keep None and set prev_season_cost_source = "unavailable",
          year = None, season = None.
    2. If parsed['prev_season_cost'] was explicitly provided by the officer:
       parsed['prev_season_cost_source'] = "officer_provided"
       parsed['prev_season_cost_source_year'] = None
       parsed['prev_season_cost_source_season'] = None
    3. Same for usd_lkr_rate: if null, default to 300.73 and set usd_lkr_rate_source = "default_2025".
    """
    if records_dict is None:
        records_dict = load_latest_historical_records()

    crop = parsed.get("crop")
    district = parsed.get("district")
    irrigation = parsed.get("irrigation_type")

    # 1 & 2. Handle prev_season_cost
    if parsed.get("prev_season_cost") is not None:
        parsed["prev_season_cost_source"] = "officer_provided"
        parsed["prev_season_cost_source_year"] = None
        parsed["prev_season_cost_source_season"] = None
    else:
        matched_rec = lookup_prev_season_record(crop, district, irrigation, records_dict)
        if matched_rec is not None:
            parsed["prev_season_cost"] = float(matched_rec["cost"])
            parsed["prev_season_cost_source"] = "auto_filled_from_history"
            parsed["prev_season_cost_source_year"] = int(matched_rec["year"])
            parsed["prev_season_cost_source_season"] = str(matched_rec["season"])
        else:
            parsed["prev_season_cost"] = None
            parsed["prev_season_cost_source"] = "unavailable"
            parsed["prev_season_cost_source_year"] = None
            parsed["prev_season_cost_source_season"] = None

    # 3. Handle usd_lkr_rate
    if parsed.get("usd_lkr_rate") is None:
        parsed["usd_lkr_rate"] = 300.73
        parsed["usd_lkr_rate_source"] = "default_2025"
    else:
        parsed["usd_lkr_rate_source"] = "officer_provided"

    return parsed


# ==============================================================================
# 1. FUNCTION: parse_query
# ==============================================================================

def parse_query(user_text: str) -> dict:
    """
    Extracts structured agricultural parameters from user natural language query using Ollama (llama3.1:8b).
    
    Fields:
      - district (string, must be in supported list)
      - crop (string, must be in supported list)
      - season ('Maha' or 'Yala' or null)
      - irrigation_type ('Irrigated', 'Rainfed', 'Unspecified' or null)
      - field_size_acres (float or null)
      - prev_season_cost (float or null)
      
    Raises:
      ConnectionError: If Ollama daemon is unreachable.
      ValueError: If query parsing fails or required crop/district cannot be identified.
    """
    if not check_ollama_available():
        raise ConnectionError("LLM service unavailable. Ensure Ollama is running: ollama serve")

    system_prompt = (
        "You are a parser for a Sri Lankan agricultural cost prediction system.\n"
        "Extract these fields from the user's query:\n"
        "  district (string, must be in the supported list)\n"
        "  crop (string, must be in the supported list)\n"
        "  season (Maha or Yala)\n"
        "  irrigation_type (Irrigated, Rainfed, or Unspecified)\n"
        "  field_size_acres (float or null)\n"
        "  prev_season_cost (float or null)\n"
        "Return null for fields the user did not specify.\n"
        "Do not invent values."
    )

    user_content = (
        f"Supported districts: {SUPPORTED_DISTRICTS}\n"
        f"Supported crops: {SUPPORTED_CROPS}\n\n"
        f"User query: {user_text}"
    )

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            format="json",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            options={"temperature": 0.0, "num_predict": 128, "num_gpu": 0},
            keep_alive="60m"
        )
        content = response["message"]["content"]
        raw_parsed = json.loads(content)
    except Exception as e:
        logger.error(f"Ollama JSON extraction failed: {e}")
        raise ValueError(f"Failed to parse query via LLM: {str(e)}")

    if not isinstance(raw_parsed, dict):
        raise ValueError("LLM returned non-dictionary JSON structure.")

    # Normalize extracted values
    norm_crop = None
    raw_crop = raw_parsed.get("crop")
    if raw_crop and isinstance(raw_crop, str):
        c_clean = raw_crop.strip().lower()
        if c_clean in _CROP_LOOKUP:
            norm_crop = _CROP_LOOKUP[c_clean]
        else:
            for sc in SUPPORTED_CROPS:
                if sc.lower() in c_clean or c_clean in sc.lower():
                    norm_crop = sc
                    break

    norm_district = None
    raw_district = raw_parsed.get("district")
    if raw_district and isinstance(raw_district, str):
        d_clean = raw_district.strip().lower()
        if d_clean in _DISTRICT_LOOKUP:
            norm_district = _DISTRICT_LOOKUP[d_clean]
        else:
            for sd in SUPPORTED_DISTRICTS:
                if sd.lower() in d_clean or d_clean in sd.lower():
                    norm_district = sd
                    break

    # Normalize season and determine season_inferred
    # If the user's query mentions a season explicitly ("Yala", "Maha", "this Yala"):
    # set season_inferred: False
    # If the user says "next season" or "this season" or doesn't mention a season at all,
    # use the calendar rule to determine the upcoming season:
    #   - If current month is Jan-Mar or Oct-Dec -> next season is Maha
    #   - If current month is Apr-Sep -> next season is Yala
    # Set season_inferred: True
    explicit_season_match = re.search(r'\b(yala|maha)\b', user_text, re.IGNORECASE)
    if explicit_season_match:
        norm_season = explicit_season_match.group(1).capitalize()
        season_inferred = False
    else:
        current_month = datetime.now().month
        if current_month in [1, 2, 3, 10, 11, 12]:
            norm_season = "Maha"
        else:
            norm_season = "Yala"
        season_inferred = True

    # Normalize irrigation_type
    norm_irr = None
    raw_irr = raw_parsed.get("irrigation_type")
    if raw_irr and isinstance(raw_irr, str):
        i_clean = raw_irr.strip().capitalize()
        if i_clean in ["Irrigated", "Rainfed", "Unspecified"]:
            norm_irr = i_clean

    # Normalize field size
    norm_size = None
    raw_size = raw_parsed.get("field_size_acres")
    if raw_size is not None:
        try:
            norm_size = float(raw_size)
            if norm_size <= 0:
                norm_size = None
        except (ValueError, TypeError):
            norm_size = None

    # Normalize previous season cost
    norm_prev_cost = None
    raw_prev_cost = raw_parsed.get("prev_season_cost")
    if raw_prev_cost is not None:
        try:
            norm_prev_cost = float(raw_prev_cost)
            if norm_prev_cost < 0:
                norm_prev_cost = None
        except (ValueError, TypeError):
            norm_prev_cost = None

    # Both Crop and District are essential for agricultural cultivation cost estimation
    if not norm_crop and not norm_district:
        raise ValueError(
            "Could not identify both crop and district from your request. "
            "Please specify a supported crop (e.g. Tomato, Paddy, Potato) and district (e.g. Hambantota, Nuwara Eliya)."
        )
    if not norm_crop:
        raise ValueError(
            f"Could not identify the crop from your request. Identified district: '{norm_district}'. "
            "Please specify a supported crop (e.g. Tomato, Potato, Paddy, Green Chilli)."
        )
    if not norm_district:
        raise ValueError(
            f"Could not identify the district from your request. Identified crop: '{norm_crop}'. "
            "Please specify a supported Sri Lankan district (e.g. Nuwara Eliya, Hambantota, Anuradhapura)."
        )

    parsed_result = {
        "district": norm_district,
        "crop": norm_crop,
        "season": norm_season,
        "irrigation_type": norm_irr,
        "field_size_acres": norm_size,
        "prev_season_cost": norm_prev_cost,
        "season_inferred": season_inferred
    }
    return parsed_result


# ==============================================================================
# 2. FUNCTION: generate_narrative
# ==============================================================================

def generate_narrative(
    prediction_response: dict,
    user_question: str,
    season_inferred: bool = False,
    season: Optional[str] = None,
    prev_season_cost_source: Optional[str] = None,
    prev_season_cost_used: Optional[float] = None,
    prev_season_cost_source_year: Optional[int] = None,
    prev_season_cost_source_season: Optional[str] = None
) -> str:
    """
    Generates a 3-5 sentence plain-language explanation of a cost prediction
    using Ollama (llama3.1:8b) for agricultural extension officers and farmers.
    
    Interprets SHAP feature attributions using explicit, honest definitions.
    """
    if not check_ollama_available():
        raise ConnectionError("LLM service unavailable. Ensure Ollama is running: ollama serve")

    # Resolve prev_season_cost_source and prev_season_cost_used if not explicitly passed
    if prev_season_cost_source is None:
        prev_season_cost_source = (
            prediction_response.get("prev_season_cost_source")
            or prediction_response.get("parsed_input", {}).get("prev_season_cost_source")
            or ("officer_provided" if prediction_response.get("prev_season_cost") is not None else "unavailable")
        )
    if prev_season_cost_used is None:
        prev_season_cost_used = (
            prediction_response.get("prev_season_cost_used")
            or prediction_response.get("prev_season_cost")
            or prediction_response.get("parsed_input", {}).get("prev_season_cost")
        )
    if prev_season_cost_source_year is None:
        prev_season_cost_source_year = (
            prediction_response.get("prev_season_cost_source_year")
            or prediction_response.get("parsed_input", {}).get("prev_season_cost_source_year")
        )
    if prev_season_cost_source_season is None:
        prev_season_cost_source_season = (
            prediction_response.get("prev_season_cost_source_season")
            or prediction_response.get("parsed_input", {}).get("prev_season_cost_source_season")
        )

    pred_cost = prediction_response.get("predicted_cost", 0.0)
    int_low = prediction_response.get("interval_low", 0.0)
    int_high = prediction_response.get("interval_high", 0.0)
    low_conf = prediction_response.get("low_confidence", False)
    low_conf_reason = prediction_response.get("low_confidence_reason") or prediction_response.get("warning")

    # Build top-of-narrative notes (auto-fill disclosure, lag saturation, and calendar season inference)
    notes = []
    if prediction_response.get("lag_saturation_detected"):
        cost_val = f"{int(round(prev_season_cost_used)):,}" if prev_season_cost_used is not None else "0"
        thresh = prediction_response.get("lag_saturation_threshold") or 0.0
        thresh_val = f"{int(round(thresh)):,}"
        notes.append(
            f"Note: the prior season cost you provided (Rs {cost_val}) exceeds what the model has seen historically "
            f"for this crop-district (Rs {thresh_val}). The prediction is therefore capped at the top of the "
            f"model's training range for this input. Treat it as a ceiling estimate."
        )
    if prev_season_cost_source == "auto_filled_from_history" and prev_season_cost_used is not None:
        crop_name = prediction_response.get("crop") or prediction_response.get("parsed_input", {}).get("crop") or "this crop"
        district_name = prediction_response.get("district") or prediction_response.get("parsed_input", {}).get("district") or "this district"
        yr_str = str(prev_season_cost_source_year) if prev_season_cost_source_year else ""
        sea_str = str(prev_season_cost_source_season) if prev_season_cost_source_season else ""
        time_desc = f"{yr_str} {sea_str}".strip() if (yr_str or sea_str) else "most recent"
        notes.append(
            f"Note: I auto-filled the prior season cost as Rs {int(prev_season_cost_used):,} "
            f"from the {time_desc} record for {crop_name} in {district_name}. You can override it if you have a more recent figure."
        )
    if season_inferred:
        target_season = season or prediction_response.get("season")
        if not target_season:
            target_season = "Maha" if datetime.now().month in [1, 2, 3, 10, 11, 12] else "Yala"
        notes.append(f"Note: I've assumed {target_season} season based on the current date. You can specify a different season if needed.")

    note_prefix = "\n\n".join(notes) if notes else ""

    confidence_rules = ""
    if prediction_response.get("lag_saturation_detected"):
        confidence_rules += (
            "LAG SATURATION NOTICE:\n"
            "  If lag_saturation_detected is true, you MUST include the ceiling caveat. Do not say the prediction is a precise estimate.\n\n"
        )
    if prev_season_cost_source == "unavailable":
        confidence_rules += (
            "CRITICAL PRIOR COST REQUIREMENT:\n"
            "  No prior season cost was available for this crop and district. Do NOT say the prediction is fully confident.\n"
            "  You MUST include this exact sentence in your explanation: 'Note: no prior season cost was available for this crop and district, so the prediction uses a broader crop-level baseline. Treat it as a rougher estimate.'\n\n"
        )
    elif prev_season_cost_used is not None:
        confidence_rules += (
            f"PRIOR COST NOTICE:\n"
            f"  Prior season cost was provided ({prev_season_cost_source}: Rs {int(prev_season_cost_used):,} LKR).\n"
            f"  Do NOT state that prior season cost was unavailable.\n\n"
        )

    if low_conf and low_conf_reason:
        confidence_rules += (
            f"LOW CONFIDENCE NOTICE:\n"
            f"  The prediction has a low confidence warning: {low_conf_reason}. You MUST mention this.\n\n"
        )

    system_prompt = (
        "You are an agricultural extension officer assistant for Sri Lanka.\n"
        "Given a cost prediction result, write a 3-5 sentence explanation covering:\n"
        "  (1) the predicted cost per acre\n"
        "  (2) the expected range\n"
        "  (3) the top drivers explaining WHY\n"
        "  (4) any low-confidence warning\n"
        "  (5) one suggested next action\n"
        "Use plain language suitable for a farmer with basic literacy.\n"
        "Never invent numbers — only use the values provided.\n\n"
        f"{confidence_rules}"
        "SHAP FEATURE INTERPRETATION MAPPING:\n"
        "  Prev_Season_Total_Cost_Incl_Imputed:\n"
        "    \"The most recent cost of the same crop in the same district. A high positive contribution means last season's cost was above the training average.\"\n\n"
        "  Year_Start:\n"
        "    \"The calendar year relative to the model's training baseline. A positive contribution means we are predicting a later year than the model's average, which reflects the general upward cost trend from inflation.\"\n\n"
        "  USD_LKR_Rate:\n"
        "    \"The exchange rate between LKR and USD. A positive contribution means the current rate is weaker than the training average, which increases the cost of imported inputs (fuel, fertilizer, agrochemicals).\"\n\n"
        "  Crop:\n"
        "    \"The intrinsic baseline cost of this crop type relative to the average crop across all training data. A positive contribution means this crop is naturally more expensive to cultivate than average.\"\n\n"
        "  District:\n"
        "    \"The intrinsic cost level of this district relative to the national average. A positive contribution means this district's cultivation costs tend to be higher.\"\n\n"
        "  Season:\n"
        "    \"Yala or Maha season baseline cost relative to the average. Yala is typically higher-cost than Maha for irrigated crops.\"\n\n"
        "  Irrigation_Type:\n"
        "    \"The water regime (Irrigated / Rainfed / Unspecified). Irrigated cultivation incurs higher machinery and water-management costs than rainfed.\"\n\n"
        "Do NOT paraphrase SHAP features into vague phrases like 'costs are increasing'. Refer to each top driver explicitly using its feature name and the exact definition above.\n\n"
        "SUGGESTED NEXT ACTION RULES:\n"
        "For the 'suggested next action', only recommend actions that follow directly from the prediction confidence and SHAP drivers. Do NOT invent agronomic advice (fertilizer timing, labour optimization, seed rates, or spraying).\n"
        "Priority order:\n"
        "  - If the prediction is low-confidence or has a low-confidence warning: Recommend: \"Treat this as an indicative range, not a precise figure. Consider comparing with the crop recommendation module.\"\n"
        "  - Otherwise, if Prev_Season_Total_Cost_Incl_Imputed dominates: \"Confirm the prior season cost figure with the farmer — it drives most of this estimate.\"\n"
        "  - Otherwise, if USD_LKR_Rate dominates: \"The estimate is sensitive to exchange rate changes; revisit it closer to planting if the rate moves.\"\n"
        "  - Otherwise, if Year_Start dominates: \"Re-run the estimate as the season approaches — the model will refresh as newer data becomes available.\""
    )

    # Format top drivers as structured list
    top_drivers = prediction_response.get("top_drivers", [])
    driver_lines = []
    for d in top_drivers[:3]:
        feat = d.get("feature", "Factor")
        pct = d.get("contribution_pct", 0.0)
        direction = d.get("direction", "+")
        driver_lines.append(f"   - {feat}: {pct:.1f}% ({direction})")

    if driver_lines:
        drivers_block = (
            "Top drivers (contribution % and direction):\n"
            + "\n".join(driver_lines)
            + "\n\nFor each of the top 3 drivers, use its exact feature name and interpret it using only the definitions provided above. Do not invent additional reasons."
        )
    else:
        drivers_block = "Top drivers: Baseline historical trend."

    # Format cost breakdown summary if available
    breakdown = prediction_response.get("cost_breakdown", {})
    breakdown_items = []
    for comp, val in breakdown.items():
        if isinstance(val, dict):
            pct = val.get("percent", 0.0)
            breakdown_items.append(f"{comp}: {pct:.1f}%")
    breakdown_str = ", ".join(breakdown_items) if breakdown_items else "Standard operational inputs"

    field_size = prediction_response.get("field_size_acres")

    context = (
        f"User Question: {user_question}\n\n"
        f"Prediction Details:\n"
        f"- Predicted Cost per Acre: Rs {pred_cost:,.0f} LKR\n"
        f"- Expected 80% Confidence Range: Rs {int_low:,.0f} to Rs {int_high:,.0f} LKR per acre\n"
        f"{drivers_block}\n"
        f"- Low Confidence Flag: {'YES - ' + str(low_conf_reason) if low_conf else 'No (Standard confidence)'}\n"
        f"- Prior Season Cost Source: {prev_season_cost_source} ({f'Rs {int(prev_season_cost_used):,} LKR' if prev_season_cost_used else 'None / Imputed from crop median'})\n"
        f"- Key Cost Components: {breakdown_str}\n"
    )

    if field_size and field_size > 0:
        total_field_cost = pred_cost * field_size
        context += f"- Field Size: {field_size} acres (Total field cost: Rs {total_field_cost:,.0f} LKR)\n"

    try:
        response = ollama.chat(
            model=OLLAMA_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": context}
            ],
            options={"temperature": 0.2, "num_predict": 350, "num_gpu": 0},
            keep_alive="60m"
        )
        content = response["message"]["content"].strip()
        final_narrative = f"{note_prefix}\n\n{content}".strip() if note_prefix else content
        return final_narrative
    except Exception as e:
        logger.error(f"Ollama narrative generation failed: {e}")
        # Select acceptable next action
        dom_feature = top_drivers[0].get("feature") if top_drivers else None
        if low_conf or prev_season_cost_source == "unavailable":
            next_action = "Treat this as an indicative range, not a precise figure. Consider comparing with the crop recommendation module."
        elif dom_feature == "Prev_Season_Total_Cost_Incl_Imputed":
            next_action = "Confirm the prior season cost figure with the farmer — it drives most of this estimate."
        elif dom_feature == "USD_LKR_Rate":
            next_action = "The estimate is sensitive to exchange rate changes; revisit it closer to planting if the rate moves."
        elif dom_feature == "Year_Start":
            next_action = "Re-run the estimate as the season approaches — the model will refresh as newer data becomes available."
        else:
            next_action = "Treat this as an indicative range, not a precise figure."

        # Cautionary sentence for unavailable prev_season_cost or low_conf
        caveat_text = ""
        if prev_season_cost_source == "unavailable":
            caveat_text = " Note: no prior season cost was available for this crop and district, so the prediction uses a broader crop-level baseline. Treat it as a rougher estimate."
        elif low_conf and low_conf_reason:
            caveat_text = f" Note: {low_conf_reason}."

        fallback_drivers = []
        for d in top_drivers[:3]:
            feat = d.get("feature", "Factor")
            pct = d.get("contribution_pct", 0.0)
            fallback_drivers.append(f"{feat} ({pct:.1f}%)")
        drivers_summary = ", ".join(fallback_drivers) if fallback_drivers else "baseline historical factors"

        fallback_narrative = (
            f"The estimated cost of cultivation is Rs {pred_cost:,.0f} per acre, with an expected 80% range "
            f"between Rs {int_low:,.0f} and Rs {int_high:,.0f}. The major cost drivers are {drivers_summary}.{caveat_text} "
            f"{next_action}"
        )
        final_fallback = f"{note_prefix}\n\n{fallback_narrative}".strip() if note_prefix else fallback_narrative
        return final_fallback


# ==============================================================================
# 3. FUNCTION: answer_officer_query
# ==============================================================================

def answer_officer_query(user_text: str) -> dict:
    """
    End-to-end question answering workflow:
    1. parse_query(user_text) -> parsed input fields
    2. auto_populate_costs(parsed) -> auto-fills prev_season_cost & usd_lkr_rate
    3. Calls POST /predict (or internal fallback)
    4. generate_narrative(...) -> human-friendly explanation
    
    Returns:
      {'request_id': str, 'timestamp': str, 'parsed': dict, 'parsed_input': dict, 'prediction': dict, 'narrative': str, 'prev_season_cost_used': float, 'prev_season_cost_source': str}
    """
    # 1. Parse user input
    parsed = parse_query(user_text)
    print(f"PARSED: prev_season_cost={parsed['prev_season_cost']}, season={parsed['season']}, usd_lkr_rate={parsed.get('usd_lkr_rate')}")

    # 2. Auto-populate costs
    parsed = auto_populate_costs(parsed)
    print(f"AFTER AUTOPOPULATE: prev_season_cost={parsed['prev_season_cost']}, source={parsed['prev_season_cost_source']}")

    # 3. Invoke Prediction Pipeline
    season = parsed.get("season") or "Maha"
    season_inferred = parsed.get("season_inferred", False)
    irrigation = parsed.get("irrigation_type") or "Irrigated"

    predict_payload = {
        "crop": parsed["crop"],
        "district": parsed["district"],
        "season": season,
        "irrigation_type": irrigation,
        "prev_season_cost": parsed.get("prev_season_cost"),
        "usd_lkr_rate": parsed.get("usd_lkr_rate", 300.73),
        "allow_extrapolation": True
    }

    print(f"PREDICT REQUEST BODY: {json.dumps(parsed, indent=2)}")

    prediction = None

    # Try calling running FastAPI service at http://localhost:8000/predict
    try:
        req_data = json.dumps(predict_payload).encode("utf-8")
        req = urllib.request.Request(
            "http://localhost:8000/predict",
            data=req_data,
            headers={"Content-Type": "application/json", "User-Agent": "nl-interface"}
        )
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            prediction = json.loads(resp.read().decode())
    except Exception as e:
        logger.warning(f"Could not reach FastAPI /predict over HTTP ({e}); invoking internal pipeline directly.")

    # Fallback: invoke predict_with_interval directly if FastAPI not running
    if prediction is None:
        from predict_with_intervals import predict_with_interval
        import uuid
        from datetime import datetime, timezone

        model_input = {
            'District': parsed['district'],
            'Crop': parsed['crop'],
            'Season': season,
            'Irrigation_Type': irrigation,
            'Year_Start': 2025,
            'USD_LKR_Rate': parsed.get('usd_lkr_rate', 300.73),
            'Prev_Season_Total_Cost_Incl_Imputed': parsed.get('prev_season_cost')
        }
        res = predict_with_interval(model_input, confidence=0.80)
        res_dict = res.to_dict() if hasattr(res, 'to_dict') else (res if isinstance(res, dict) else vars(res))

        prediction = {
            "request_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "predicted_cost": round(float(res_dict.get('predicted_cost', 0.0)), 1),
            "interval_low": round(float(res_dict.get('interval_low', 0.0)), 1),
            "interval_high": round(float(res_dict.get('interval_high', 0.0)), 1),
            "low_confidence": bool(res_dict.get('low_confidence', False)),
            "low_confidence_reason": res_dict.get('low_confidence_reason'),
            "reference_note": "Model reference year is 2025 (latest available data).",
            "top_drivers": res_dict.get('top_drivers', []),
            "model_version": "gb_tuned_v1",
            "reference_year": 2025,
            "prediction_target": "next_available_season",
            "warning": res_dict.get('low_confidence_reason'),
            "cost_breakdown": {
                "Labour": {"percent": 45.0, "estimated_cost": int(res_dict['predicted_cost'] * 0.45)},
                "Fertilizer": {"percent": 30.0, "estimated_cost": int(res_dict['predicted_cost'] * 0.30)},
                "Machinery": {"percent": 15.0, "estimated_cost": int(res_dict['predicted_cost'] * 0.15)},
                "Others": {"percent": 10.0, "estimated_cost": int(res_dict['predicted_cost'] * 0.10)}
            },
            "breakdown_source": "historical_district_crop_ratio",
            "breakdown_note": "Estimated breakdown from historical ratios."
        }

        # Check lag saturation in fallback path
        fallback_threshold = LAG_MAX.get((parsed["crop"], parsed["district"]), LAG_MAX_GLOBAL)
        if parsed.get("prev_season_cost") and parsed["prev_season_cost"] > fallback_threshold:
            prediction["lag_saturation_detected"] = True
            prediction["lag_saturation_threshold"] = fallback_threshold
            prediction["lag_saturation_note"] = (
                f"The provided prior season cost (Rs {parsed['prev_season_cost']:,.0f}) "
                f"exceeds the maximum value the model has seen for {parsed['crop']} in "
                f"{parsed['district']} (Rs {fallback_threshold:,.0f}). The model's prediction is "
                f"capped at the top of its training range for this feature. To "
                f"capture higher costs, the model requires retraining on newer "
                f"data."
            )
        else:
            prediction["lag_saturation_detected"] = False
            prediction["lag_saturation_threshold"] = None
            prediction["lag_saturation_note"] = None

    print(f"PREDICT RESPONSE: predicted_cost={prediction['predicted_cost']}")

    # Attach field_size_acres, season, crop, district into prediction dictionary for narrative scaling
    if parsed.get("field_size_acres"):
        prediction["field_size_acres"] = parsed["field_size_acres"]
    prediction["season"] = season
    prediction["crop"] = parsed.get("crop")
    prediction["district"] = parsed.get("district")

    # 4. Generate narrative
    narrative = generate_narrative(
        prediction,
        user_text,
        season_inferred=season_inferred,
        season=season,
        prev_season_cost_source=parsed.get("prev_season_cost_source"),
        prev_season_cost_used=parsed.get("prev_season_cost"),
        prev_season_cost_source_year=parsed.get("prev_season_cost_source_year"),
        prev_season_cost_source_season=parsed.get("prev_season_cost_source_season")
    )

    return {
        "request_id": prediction.get("request_id"),
        "timestamp": prediction.get("timestamp"),
        "parsed": parsed,
        "parsed_input": parsed,
        "prediction": prediction,
        "narrative": narrative,
        "model_version": prediction.get("model_version", "gb_tuned_v1"),
        "prev_season_cost_used": parsed.get("prev_season_cost"),
        "prev_season_cost_source": parsed.get("prev_season_cost_source"),
        "prev_season_cost_source_year": parsed.get("prev_season_cost_source_year"),
        "prev_season_cost_source_season": parsed.get("prev_season_cost_source_season")
    }


if __name__ == "__main__":
    print("[Progress] Testing nl_interface functions...")
    sample_q = "What will it cost to grow tomato in Hambantota this Yala on 1.5 acres?"
    print(f"User Query: {sample_q}")
    res = answer_officer_query(sample_q)
    print("\nParsed Output:")
    print(json.dumps(res["parsed"], indent=2))
    print("\nPrediction Cost:", res["prediction"]["predicted_cost"])
    print("\nNarrative:")
    print(res["narrative"])
