from fastapi import APIRouter, Query, HTTPException
import httpx

from app.models.weather import CurrentWeatherResponse, ForecastResponse, HistoricalResponse
from app.services.open_meteo import get_current_weather, get_forecast, get_historical_weather

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("/current", response_model=CurrentWeatherResponse)
async def current_weather(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (WGS84)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (WGS84)"),
):
    """Get current weather conditions for a location."""
    try:
        return await get_current_weather(latitude, longitude)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.get("/forecast", response_model=ForecastResponse)
async def seven_day_forecast(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (WGS84)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (WGS84)"),
):
    """Get a 7-day weather forecast for a location."""
    try:
        return await get_forecast(latitude, longitude)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))


@router.get("/historical", response_model=HistoricalResponse)
async def historical_weather(
    latitude: float = Query(..., ge=-90, le=90, description="Latitude (WGS84)"),
    longitude: float = Query(..., ge=-180, le=180, description="Longitude (WGS84)"),
    start_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="Start date (YYYY-MM-DD)"),
    end_date: str = Query(..., pattern=r"^\d{4}-\d{2}-\d{2}$", description="End date (YYYY-MM-DD)"),
):
    """Get historical weather data for a location and date range."""
    try:
        return await get_historical_weather(latitude, longitude, start_date, end_date)
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=str(e))
