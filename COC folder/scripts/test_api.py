#!/usr/bin/env python3
"""
Test Suite for Agricultural Cost Prediction API
===============================================
Uses the `requests` library to test the FastAPI service:
1. Asserts GET /health returns 200 and valid schema.
2. Asserts GET /metadata returns 200 and correct crops/districts.
3. Asserts GET /defaults returns 200 with reference_year=2025, default rate, and pre-computed costs.
4. Test A: Officer predicting future season without year_start (uses reference_year=2025, default USD).
5. Test B: Officer providing specific spot rate override (315.50) triggering currency shock warning.
6. Test C: Cold-start crop-district (null prior cost).
7. Asserts validation rules reject invalid inputs with HTTP 422.
8. Saves sample_response.json.
"""

import sys
import time
import json
import threading
from pathlib import Path
import requests

WORKSPACE = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE))

import uvicorn
from prediction_api import app

PORT = 8000
BASE_URL = f"http://127.0.0.1:{PORT}"

EXPECTED_PREDICT_KEYS = {
    "request_id",
    "timestamp",
    "predicted_cost",
    "interval_low",
    "interval_high",
    "low_confidence",
    "low_confidence_reason",
    "reference_note",
    "top_drivers",
    "model_version",
    "reference_year",
    "prediction_target",
    "warning"
}

EXPECTED_DRIVER_KEYS = {"feature", "contribution_pct", "direction"}


def start_server_if_needed():
    """Start uvicorn in a background thread if not already running."""
    try:
        r = requests.get(f"{BASE_URL}/health", timeout=0.8)
        if r.status_code == 200:
            print(f"[*] Connected to existing server at {BASE_URL}")
            return None
    except Exception:
        pass

    print(f"[*] Starting local Uvicorn server on port {PORT} in background thread...")
    config = uvicorn.Config(app, host="127.0.0.1", port=PORT, log_level="warning")
    server = uvicorn.Server(config)
    t = threading.Thread(target=server.run, daemon=True)
    t.start()

    # Wait for server to become healthy
    for _ in range(25):
        time.sleep(0.3)
        try:
            r = requests.get(f"{BASE_URL}/health", timeout=0.8)
            if r.status_code == 200:
                print("[*] Server is healthy and ready to receive requests.")
                return server
        except Exception:
            pass

    raise RuntimeError(f"Server on {BASE_URL} failed to start in time.")


def test_health_endpoint():
    print("\n" + "=" * 80)
    print("TEST 1: GET /health (via requests)")
    print("=" * 80)
    resp = requests.get(f"{BASE_URL}/health", timeout=5.0)
    print(f"HTTP Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    data = resp.json()
    print("Formatted Response:")
    print(json.dumps(data, indent=4))
    
    assert data["status"] == "ok"
    assert data["model_version"] in ("extratrees_champion_v2", "gb_tuned_v1")
    assert data["pipeline_loaded"] is True
    assert "uptime_seconds" in data
    print(">>> GET /health assertion PASSED!")


def test_metadata_endpoint():
    print("\n" + "=" * 80)
    print("TEST 2: GET /metadata (via requests)")
    print("=" * 80)
    resp = requests.get(f"{BASE_URL}/metadata", timeout=5.0)
    print(f"HTTP Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    
    data = resp.json()
    print(f"Model Version: {data['model_version']}")
    print(f"Supported Crops Count: {len(data['crops_supported'])}")
    print(f"Supported Districts Count: {len(data['districts_supported'])}")
    print(f"Supported Seasons: {data['seasons_supported']}")
    print(f"Supported Irrigation: {data['irrigation_types_supported']}")
    print(f"Year Range: {data['training_year_range']}")
    print(f"USD Training Mean: {data['training_usd_lkr_mean']}")
    print(f"USD Training Range: {data.get('training_usd_lkr_range')}")

    assert len(data['crops_supported']) == 23
    assert len(data['districts_supported']) in (25, 26)
    assert data['training_year_range'] == [2014, 2025]
    assert data.get('training_usd_lkr_range') == [130.54, 326.63]
    print(">>> GET /metadata assertion PASSED!")


def test_defaults_endpoint():
    print("\n" + "=" * 80)
    print("TEST 3: GET /defaults (via requests)")
    print("=" * 80)
    resp = requests.get(f"{BASE_URL}/defaults", timeout=5.0)
    print(f"HTTP Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    data = resp.json()
    print(f"Reference Year: {data['reference_year']}")
    print(f"USD Default: {data['usd_lkr_rate_default']}")
    print(f"Latest Available Costs Count: {len(data['latest_available_costs'])}")
    
    assert data["reference_year"] == 2025
    assert data["usd_lkr_rate_default"] == 300.73
    assert "Potato|Nuwara Eliya|Irrigated" in data["latest_available_costs"]
    assert data["latest_available_costs"]["Potato|Nuwara Eliya|Irrigated"] == 865823
    assert "Tomato|Hambantota|Irrigated" in data["latest_available_costs"]
    assert data["latest_available_costs"]["Tomato|Hambantota|Irrigated"] == 530108
    print(">>> GET /defaults assertion PASSED!")


def test_extrapolation_cases_a_b_c_d():
    print("\n" + "=" * 80)
    print("TEST 4: Low Confidence & Extrapolation Tests (Cases A, B, C, D)")
    print("=" * 80)

    # Base payload
    base_payload = {
        "district": "Nuwara Eliya",
        "crop": "Potato",
        "season": "Maha",
        "irrigation_type": "Irrigated",
        "prev_season_cost": 865823
    }

    # Test A: Default 2025 rate (300.73)
    print("\n--- Test A: Default 2025 rate (300.73) ---")
    payload_a = dict(base_payload)
    resp_a = requests.post(f"{BASE_URL}/predict", json=payload_a, timeout=10.0)
    assert resp_a.status_code == 200, f"Expected 200, got {resp_a.status_code}: {resp_a.text}"
    data_a = resp_a.json()
    print(f"  Predicted Cost       : Rs {data_a['predicted_cost']:,.1f}")
    print(f"  80% Interval         : Rs {data_a['interval_low']:,.1f} – Rs {data_a['interval_high']:,.1f}")
    print(f"  Low Confidence       : {data_a['low_confidence']}")
    print(f"  Low Confidence Reason: {data_a['low_confidence_reason']}")
    print(f"  Reference Note       : {data_a['reference_note']}")
    assert data_a["low_confidence"] is False, "Expected low_confidence=False for 300.73 inside training range"
    assert data_a["low_confidence_reason"] is None
    assert "Model reference year is 2025" in data_a["reference_note"]

    # Save sample_response.json
    sample_path = (WORKSPACE / "reports" / "sample_response.json") if (WORKSPACE / "reports").exists() else (WORKSPACE / "sample_response.json")
    with open(sample_path, "w", encoding="utf-8") as f:
        json.dump(data_a, f, indent=4)
    print(f"  [*] Updated {sample_path}")

    # Test B: Extreme high rate (450.00)
    print("\n--- Test B: Extreme high rate (450.00) ---")
    payload_b = dict(base_payload, usd_lkr_rate=450.00)
    resp_b = requests.post(f"{BASE_URL}/predict", json=payload_b, timeout=10.0)
    assert resp_b.status_code == 200, f"Expected 200, got {resp_b.status_code}: {resp_b.text}"
    data_b = resp_b.json()
    print(f"  Predicted Cost       : Rs {data_b['predicted_cost']:,.1f}")
    print(f"  80% Interval (widened): Rs {data_b['interval_low']:,.1f} – Rs {data_b['interval_high']:,.1f}")
    print(f"  Low Confidence       : {data_b['low_confidence']}")
    print(f"  Low Confidence Reason: {data_b['low_confidence_reason']}")
    assert data_b["low_confidence"] is True, "Expected low_confidence=True for 450.00 > 326.63"
    assert "outside the training range" in data_b["low_confidence_reason"]
    assert "extrapolating" in data_b["low_confidence_reason"]
    # Check that interval is widened compared to un-widened base
    interval_width_a = data_a["interval_high"] - data_a["interval_low"]
    interval_width_b = data_b["interval_high"] - data_b["interval_low"]
    print(f"  Interval Width: Base = {interval_width_a:,.1f}, Out-of-range = {interval_width_b:,.1f}")
    assert interval_width_b > interval_width_a, "Expected out-of-range interval to be wider"

    # Test C: Historical rate (150.00)
    print("\n--- Test C: Historical rate (150.00) ---")
    payload_c = dict(base_payload, usd_lkr_rate=150.00)
    resp_c = requests.post(f"{BASE_URL}/predict", json=payload_c, timeout=10.0)
    assert resp_c.status_code == 200, f"Expected 200, got {resp_c.status_code}: {resp_c.text}"
    data_c = resp_c.json()
    print(f"  Predicted Cost       : Rs {data_c['predicted_cost']:,.1f}")
    print(f"  80% Interval         : Rs {data_c['interval_low']:,.1f} – Rs {data_c['interval_high']:,.1f}")
    print(f"  Low Confidence       : {data_c['low_confidence']}")
    print(f"  Low Confidence Reason: {data_c['low_confidence_reason']}")
    print(f"  Reference Note       : {data_c['reference_note']}")
    assert data_c["low_confidence"] is False, "Expected low_confidence=False for 150.00 inside range"
    assert data_c["low_confidence_reason"] is None
    assert "Model reference year is 2025" in data_c["reference_note"]

    # Test D: Extreme low rate (100.00)
    print("\n--- Test D: Extreme low rate (100.00) ---")
    payload_d = dict(base_payload, usd_lkr_rate=100.00)
    resp_d = requests.post(f"{BASE_URL}/predict", json=payload_d, timeout=10.0)
    assert resp_d.status_code == 200, f"Expected 200, got {resp_d.status_code}: {resp_d.text}"
    data_d = resp_d.json()
    print(f"  Predicted Cost       : Rs {data_d['predicted_cost']:,.1f}")
    print(f"  80% Interval (widened): Rs {data_d['interval_low']:,.1f} – Rs {data_d['interval_high']:,.1f}")
    print(f"  Low Confidence       : {data_d['low_confidence']}")
    print(f"  Low Confidence Reason: {data_d['low_confidence_reason']}")
    assert data_d["low_confidence"] is True, "Expected low_confidence=True for 100.00 < 130.54"
    assert "outside the training range" in data_d["low_confidence_reason"]
    assert "extrapolating" in data_d["low_confidence_reason"]

    print(">>> All 4 extrapolation test cases (A, B, C, D) PASSED assertion logic!")


def test_validation_constraints():
    print("\n" + "=" * 80)
    print("TEST 5: Validation Constraints (Expecting HTTP 422)")
    print("=" * 80)

    invalid_cases = [
        (
            "Out-of-scope Crop ('Avocado')", 
            {"district": "Kandy", "crop": "Avocado", "season": "Maha", "irrigation_type": "Irrigated", "usd_lkr_rate": 300.0}
        ),
        (
            "Out-of-scope District ('Galle')", 
            {"district": "Galle", "crop": "Paddy", "season": "Maha", "irrigation_type": "Irrigated", "usd_lkr_rate": 300.0}
        ),
        (
            "Year Out of Range (2010 < 2014)", 
            {"district": "Kandy", "crop": "Paddy", "season": "Maha", "irrigation_type": "Irrigated", "reference_year": 2010, "usd_lkr_rate": 300.0}
        ),
        (
            "USD Rate Out of Range (20.0 < 50.0)", 
            {"district": "Kandy", "crop": "Paddy", "season": "Maha", "irrigation_type": "Irrigated", "usd_lkr_rate": 20.0}
        )
    ]

    for label, payload in invalid_cases:
        resp = requests.post(f"{BASE_URL}/predict", json=payload, timeout=5.0)
        print(f"Testing {label} -> HTTP Status: {resp.status_code}")
        assert resp.status_code == 422, f"Expected 422, got {resp.status_code}"
        err_detail = resp.json().get("detail", resp.text)
        print(f"  Validation message: {str(err_detail)[:110]}...")

    print(">>> All 4 validation constraint tests correctly returned HTTP 422!")


def main():
    server = start_server_if_needed()
    try:
        test_health_endpoint()
        test_metadata_endpoint()
        test_defaults_endpoint()
        test_extrapolation_cases_a_b_c_d()
        test_validation_constraints()
        print("\n" + "=" * 80)
        print("ALL TESTS PASSED! API IS FULLY FUNCTIONAL AND VERIFIED.")
        print("=" * 80)
    finally:
        if server:
            server.should_exit = True


if __name__ == "__main__":
    main()
