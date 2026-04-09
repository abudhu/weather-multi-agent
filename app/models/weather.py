from pydantic import BaseModel, Field
from typing import Optional


class CurrentWeatherResponse(BaseModel):
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    timezone: str
    time: str
    temperature_c: float = Field(description="Temperature in Celsius")
    feels_like_c: float = Field(description="Apparent temperature in Celsius")
    humidity_pct: float = Field(description="Relative humidity percentage")
    precipitation_mm: float = Field(description="Precipitation in mm")
    rain_mm: float = Field(description="Rain in mm")
    snowfall_cm: float = Field(description="Snowfall in cm")
    weather_code: int = Field(description="WMO weather interpretation code")
    weather_description: str = Field(description="Human-readable weather description")
    cloud_cover_pct: float = Field(description="Cloud cover percentage")
    wind_speed_kmh: float = Field(description="Wind speed in km/h")
    wind_direction_deg: float = Field(description="Wind direction in degrees")
    wind_gusts_kmh: float = Field(description="Wind gusts in km/h")
    pressure_msl_hpa: float = Field(description="Sea level pressure in hPa")
    is_day: bool


class DailyForecast(BaseModel):
    date: str
    weather_code: int
    weather_description: str
    temperature_max_c: float
    temperature_min_c: float
    feels_like_max_c: float
    feels_like_min_c: float
    sunrise: str
    sunset: str
    precipitation_sum_mm: float
    rain_sum_mm: float
    snowfall_sum_cm: float
    precipitation_hours: float
    wind_speed_max_kmh: float
    wind_gusts_max_kmh: float
    wind_direction_dominant_deg: float
    uv_index_max: Optional[float] = None


class ForecastResponse(BaseModel):
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    timezone: str
    daily: list[DailyForecast]


class DailyHistorical(BaseModel):
    date: str
    weather_code: Optional[int] = None
    weather_description: Optional[str] = None
    temperature_max_c: Optional[float] = None
    temperature_min_c: Optional[float] = None
    feels_like_max_c: Optional[float] = None
    feels_like_min_c: Optional[float] = None
    sunrise: Optional[str] = None
    sunset: Optional[str] = None
    precipitation_sum_mm: Optional[float] = None
    rain_sum_mm: Optional[float] = None
    snowfall_sum_cm: Optional[float] = None
    precipitation_hours: Optional[float] = None
    wind_speed_max_kmh: Optional[float] = None
    wind_gusts_max_kmh: Optional[float] = None
    wind_direction_dominant_deg: Optional[float] = None


class HistoricalResponse(BaseModel):
    latitude: float
    longitude: float
    elevation: Optional[float] = None
    timezone: str
    daily: list[DailyHistorical]
