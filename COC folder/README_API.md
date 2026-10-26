# Agricultural Cultivation Cost Prediction REST API

Production-ready FastAPI prediction service for **IT4010 SO1: Intelligent Decision Support System for Agricultural Production Cost Prediction**.

This API wraps the trained gradient boosting pipeline (`best_model_pipeline.pkl`), providing point cost estimates, calibrated multiplicative prediction intervals in log-space, and local SHAP feature attributions.

---

## 1. Installation

Install required dependencies:

```bash
pip install fastapi uvicorn pydantic requests
```

*(Note: `shap`, `scikit-learn`, `pandas`, and `numpy` should already be present from model training).*

---

## 2. Server Startup

Launch the development server with hot-reload enabled:

```bash
uvicorn prediction_api:app --reload --port 8000
```

The service will start on `http://localhost:8000`. 
Interactive Swagger API documentation is automatically accessible at:
- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

---

## 3. API Endpoints & cURL Examples

### A. Health Check: `GET /health`
Returns service status, model version, pipeline load verification, and server uptime.

```bash
curl -X GET "http://localhost:8000/health"
```

**Response (200 OK):**
```json
{
    "status": "ok",
    "model_version": "gb_tuned_v1",
    "pipeline_loaded": true,
    "uptime_seconds": 128
}
```

---

### B. Metadata Discovery: `GET /metadata`
Returns supported categories (23 crops, 25 districts, water regimes, seasons) dynamically extracted from `coc_model_ready.csv` along with training hyperparameters.

```bash
curl -X GET "http://localhost:8000/metadata"
```

**Response (200 OK):**
```json
{
    "model_version": "gb_tuned_v1",
    "crops_supported": [
        "Big Onion", "Bitter Gourd", "Black Gram", "Brinjal", "Cabbage", "Capsicum",
        "Carrot", "Cowpea", "Gingelly", "Green Chilli", "Green Gram", "Groundnut",
        "Kurakkan", "Maize", "Manioc", "Paddy", "Pole Bean", "Potato", "Pumpkin",
        "Red Onion", "Soybean", "Sweet Potato", "Tomato"
    ],
    "districts_supported": [
        "Ampara", "Ampara (East)", "Ampara (West)", "Anuradhapura", "Badulla",
        "Batticaloa", "Gampaha", "Hambantota", "Jaffna", "Kalutara", "Kandy",
        "Kurunegala", "Mahaweli System B", "Mahaweli System C", "Mahaweli System H",
        "Mannar", "Matale", "Monaragala", "Nuwara Eliya", "Polonnaruwa", "Puttalam",
        "Trincomalee", "Udawalawa", "Vavuniya", "Whole Island"
    ],
    "seasons_supported": ["Maha", "Yala"],
    "irrigation_types_supported": ["Irrigated", "Rainfed", "Unspecified"],
    "training_year_range": [2014, 2025],
    "training_usd_lkr_mean": 217.03,
    "low_confidence_threshold_pct": 30
}
```

---

### C. Cost Prediction & Intervals: `POST /predict`
Generates full economic cost prediction (`predicted_cost`), multiplicative 80% prediction interval (`interval_low`, `interval_high`), macroeconomic risk assessment (`low_confidence`), and the top 3 SHAP drivers.

```bash
curl -X POST "http://localhost:8000/predict" \
     -H "Content-Type: application/json" \
     -d '{
       "district": "Nuwara Eliya",
       "crop": "Potato",
       "season": "Maha",
       "irrigation_type": "Irrigated",
       "year_start": 2024,
       "usd_lkr_rate": 301.68,
       "prev_season_cost": 810000.0
     }'
```

**Response (200 OK):**
```json
{
    "request_id": "f676e0c1-ba71-4f65-a41e-c93e35ff8fce",
    "timestamp": "2026-09-24T15:12:07.859745+00:00",
    "predicted_cost": 872879.3,
    "interval_low": 628576.4,
    "interval_high": 1212132.9,
    "low_confidence": true,
    "top_drivers": [
        {
            "feature": "Prev_Season_Total_Cost_Incl_Imputed",
            "contribution_pct": 65.4,
            "direction": "+"
        },
        {
            "feature": "Crop",
            "contribution_pct": 16.0,
            "direction": "+"
        },
        {
            "feature": "Year_Start",
            "contribution_pct": 7.8,
            "direction": "+"
        }
    ],
    "model_version": "gb_tuned_v1"
}
```

---

## 4. Full POST /predict Schema Reference

### Request Body Schema

| Field | Type | Required | Constraints | Description |
|:---|:---:|:---:|:---|:---|
| `district` | `string` | **Yes** | Must be in `districts_supported` (25 regions) | Cultivation location (e.g. `"Nuwara Eliya"`, `"Kandy"`, `"Ampara (East)"`) |
| `crop` | `string` | **Yes** | Must be in `crops_supported` (23 crops) | Target commercial crop (e.g. `"Potato"`, `"Paddy"`, `"Maize"`) |
| `season` | `string` | **Yes** | `"Maha"` or `"Yala"` | Agrarian season (`Maha` = wet, `Yala` = dry) |
| `irrigation_type` | `string` | **Yes** | `"Irrigated"`, `"Rainfed"`, or `"Unspecified"` | Water regime |
| `year_start` | `integer`| **Yes** | $2014 \le \text{year} \le 2025$ | Calendar year cultivation commenced |
| `usd_lkr_rate` | `float`  | **Yes** | $100.0 \le \text{rate} \le 400.0$ | Annual average LKR/USD foreign exchange rate |
| `prev_season_cost`| `float` / `null` | No | $\ge 0.0$ or `null` | Prior season cultivation cost in LKR (pass `null` for new crops) |

### Response Body Schema

| Field | Type | Description |
|:---|:---:|:---|
| `request_id` | `string` (UUID4) | Unique identifier generated for the transaction |
| `timestamp` | `string` (ISO-8601 UTC) | Request processing timestamp |
| `predicted_cost` | `float` (LKR/acre) | Point estimate of total cultivation cost including imputed costs |
| `interval_low` | `float` (LKR/acre) | Lower bound of the 80% prediction interval (strictly $> 0$) |
| `interval_high` | `float` (LKR/acre) | Upper bound of the 80% prediction interval |
| `low_confidence` | `boolean` | `true` if `usd_lkr_rate` deviates $>30\%$ from training mean (217.03), triggering 1.5× interval widening |
| `top_drivers` | `array[object]` | Top 3 features ranked by relative SHAP contribution percentage |
| `top_drivers[].feature` | `string` | Name of the driving feature |
| `top_drivers[].contribution_pct` | `float` | Relative percentage impact ($\frac{|\phi_j|}{\sum |\phi_k|} \times 100\%$) |
| `top_drivers[].direction` | `string` | `"+"` (cost-increasing) or `"-"` (cost-decreasing) |
| `model_version` | `string` | Deployment identifier (`"gb_tuned_v1"`) |

---

## 5. HTTP Error Code Reference

| Status Code | Reason | Cause & Resolution |
|:---|:---|:---|
| **`200 OK`** | Success | Request was valid; predictions, intervals, and SHAP drivers computed successfully. |
| **`422 Unprocessable Entity`** | Validation Error | Input violated schema constraints (e.g., unsupported crop, year outside 2014–2025, negative cost). The response contains detailed field-level error messages. |
| **`500 Internal Server Error`** | Server Error | Unhandled pipeline exception during preprocessing or inference. Check server console logs. |

### Example 422 Validation Error Response
```json
{
    "detail": [
        {
            "type": "value_error",
            "loc": ["body", "crop"],
            "msg": "Value error, Crop 'Avocado' is not supported. Supported crops (23): ['Big Onion', ...]",
            "input": "Avocado"
        }
    ]
}
```

---

## 6. Audit Logging (`predictions.log`)

Every inference request is automatically appended as a JSON line to `predictions.log` in the root workspace directory for full regulatory and traceability compliance:

```json
{"request_id": "f676e0c1-ba71-4f65-a41e-c93e35ff8fce", "timestamp": "2026-09-24T15:12:07.859745+00:00", "input": {"district": "Nuwara Eliya", "crop": "Potato", "season": "Maha", "irrigation_type": "Irrigated", "year_start": 2024, "usd_lkr_rate": 301.68, "prev_season_cost": 810000.0}, "output": {"request_id": "f676e0c1-ba71-4f65-a41e-c93e35ff8fce", "timestamp": "2026-09-24T15:12:07.859745+00:00", "predicted_cost": 872879.3, "interval_low": 628576.4, "interval_high": 1212132.9, "low_confidence": true, "top_drivers": [{"feature": "Prev_Season_Total_Cost_Incl_Imputed", "contribution_pct": 65.4, "direction": "+"}, {"feature": "Crop", "contribution_pct": 16.0, "direction": "+"}, {"feature": "Year_Start", "contribution_pct": 7.8, "direction": "+"}], "model_version": "gb_tuned_v1"}}
```

---

## 7. Troubleshooting & FAQ

1. **Slow First Request (SHAP / Numba JIT Warm-up)**:
   - *Symptom*: The initial inference request takes ~1–2 seconds, while subsequent requests complete in < 25 ms.
   - *Resolution*: The service lifespan hook automatically executes a warm-up inference during startup. If reload triggers a cold restart, the first query compiles the tree explainer; subsequent calls are fast.
2. **Missing Crop / District (HTTP 422)**:
   - *Cause*: A user requested a commodity like `Avocado` or `Beetroot` (which only had 1 record in the dataset and was excluded during 'High'/'Medium' tier filtering).
   - *Resolution*: Query `GET /metadata` to retrieve the current catalog of supported agricultural commodities.
3. **CORS Rejection from Frontend**:
   - *Resolution*: CORS is pre-configured to allow `http://localhost:3000` (Next.js/React) and `http://localhost:5173` (Vite). If your client runs on a different port, update the `allow_origins` array in `prediction_api.py`.
4. **Model Version Mismatch**:
   - Verify `GET /health` returns `"model_version": "gb_tuned_v1"` and `"pipeline_loaded": true`. If `pipeline_loaded` is `false`, ensure `best_model_pipeline.pkl` exists in the application root directory.
