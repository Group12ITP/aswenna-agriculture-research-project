import logging
from contextlib import asynccontextmanager
from typing import Optional
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .inference import get_service, ForecasterService

logger = logging.getLogger("backend.main")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load data and models once at startup
    logger.info("Starting up FastAPI Vegetable Price Forecasting API...")
    service = get_service()
    logger.info(f"Loaded {len(service.get_vegetables())} vegetables. Ready for requests.")
    yield
    logger.info("Shutting down Vegetable Price Forecasting API...")

app = FastAPI(
    title="Sri Lankan DCS Vegetable Price Forecaster API",
    description="Causal price forecasting API for 32 Sri Lankan vegetables using frozen DCS models",
    version="1.0.0",
    lifespan=lifespan
)

# Enable CORS for the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    service = get_service()
    return {
        "status": "online",
        "project": "Sri Lankan Vegetable Price Forecasting",
        "origin_week": service.origin_week,
        "origin_date": service.origin_date,
        "vegetables_count": len(service.vegetables_catalog),
        "endpoints": ["/vegetables", "/history", "/forecast"]
    }

@app.get("/vegetables")
def get_vegetables():
    """
    Returns list of 32 vegetables with their category, unit, and last observed price.
    """
    service = get_service()
    return service.get_vegetables()

@app.get("/history")
def get_history(
    vegetable: str = Query(..., description="Name of vegetable (e.g. Carrot, Brinjal, Mukunuwenna)"),
    weeks: int = Query(104, description="Number of recent weeks of historical retail prices (default: 104)")
):
    """
    Returns recent weekly retail price history for a specific vegetable.
    """
    service = get_service()
    try:
        return service.get_history(vegetable=vegetable, weeks=weeks)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error fetching history for {vegetable}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while retrieving price history.")

@app.get("/forecast")
def get_forecast(
    vegetable: str = Query(..., description="Name of vegetable (e.g. Carrot, Ash Plantain)"),
    horizon: int = Query(4, description="Forecast horizon in weeks: 1, 4, 8, or 12"),
    model: str = Query("selected", description="Model option: 'selected' (default), 'naive', or 'seasonal_mean_4yr'")
):
    """
    Generate point forecast, conformal prediction intervals, and comparative baseline predictions.
    """
    service = get_service()
    try:
        return service.get_forecast(vegetable=vegetable, horizon=horizon, model=model)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error computing forecast for {vegetable} (h={horizon}, model={model}): {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error while generating forecast.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
