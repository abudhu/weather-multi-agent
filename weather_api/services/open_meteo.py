import httpx

from weather_api.models.weather import (
    CurrentWeatherResponse,
    DailyForecast,
    DailyHistorical,
    ForecastResponse,
    HistoricalResponse,
)

FORECAST_BASE_URL = "https://api.open-meteo.com/v1/forecast"
HISTORICAL_BASE_URL = "https://archive-api.open-meteo.com/v1/archive"

WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def _weather_description(code: int) -> str:
    return WMO_CODES.get(code, f"Unknown ({code})")


async def get_current_weather(latitude: float, longitude: float) -> CurrentWeatherResponse:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "current": ",".join([
            "temperature_2m",
            "relative_humidity_2m",
            "apparent_temperature",
            "is_day",
            "precipitation",
            "rain",
            "showers",
            "snowfall",
            "weather_code",
            "cloud_cover",
            "pressure_msl",
            "surface_pressure",
            "wind_speed_10m",
            "wind_direction_10m",
            "wind_gusts_10m",
        ]),
        "timezone": "auto",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(FORECAST_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    current = data["current"]
    return CurrentWeatherResponse(
        latitude=data["latitude"],
        longitude=data["longitude"],
        elevation=data.get("elevation"),
        timezone=data.get("timezone", "UTC"),
        time=current["time"],
        temperature_c=current["temperature_2m"],
        feels_like_c=current["apparent_temperature"],
        humidity_pct=current["relative_humidity_2m"],
        precipitation_mm=current["precipitation"],
        rain_mm=current["rain"],
        snowfall_cm=current["snowfall"],
        weather_code=current["weather_code"],
        weather_description=_weather_description(current["weather_code"]),
        cloud_cover_pct=current["cloud_cover"],
        wind_speed_kmh=current["wind_speed_10m"],
        wind_direction_deg=current["wind_direction_10m"],
        wind_gusts_kmh=current["wind_gusts_10m"],
        pressure_msl_hpa=current["pressure_msl"],
        is_day=bool(current["is_day"]),
    )


async def get_forecast(latitude: float, longitude: float) -> ForecastResponse:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "sunrise",
            "sunset",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "precipitation_hours",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "wind_direction_10m_dominant",
            "uv_index_max",
        ]),
        "timezone": "auto",
        "forecast_days": 7,
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(FORECAST_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    daily = data["daily"]
    days = []
    for i in range(len(daily["time"])):
        days.append(DailyForecast(
            date=daily["time"][i],
            weather_code=daily["weather_code"][i],
            weather_description=_weather_description(daily["weather_code"][i]),
            temperature_max_c=daily["temperature_2m_max"][i],
            temperature_min_c=daily["temperature_2m_min"][i],
            feels_like_max_c=daily["apparent_temperature_max"][i],
            feels_like_min_c=daily["apparent_temperature_min"][i],
            sunrise=daily["sunrise"][i],
            sunset=daily["sunset"][i],
            precipitation_sum_mm=daily["precipitation_sum"][i],
            rain_sum_mm=daily["rain_sum"][i],
            snowfall_sum_cm=daily["snowfall_sum"][i],
            precipitation_hours=daily["precipitation_hours"][i],
            wind_speed_max_kmh=daily["wind_speed_10m_max"][i],
            wind_gusts_max_kmh=daily["wind_gusts_10m_max"][i],
            wind_direction_dominant_deg=daily["wind_direction_10m_dominant"][i],
            uv_index_max=daily["uv_index_max"][i],
        ))

    return ForecastResponse(
        latitude=data["latitude"],
        longitude=data["longitude"],
        elevation=data.get("elevation"),
        timezone=data.get("timezone", "UTC"),
        daily=days,
    )


async def get_historical_weather(
    latitude: float,
    longitude: float,
    start_date: str,
    end_date: str,
) -> HistoricalResponse:
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "start_date": start_date,
        "end_date": end_date,
        "daily": ",".join([
            "weather_code",
            "temperature_2m_max",
            "temperature_2m_min",
            "apparent_temperature_max",
            "apparent_temperature_min",
            "sunrise",
            "sunset",
            "precipitation_sum",
            "rain_sum",
            "snowfall_sum",
            "precipitation_hours",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "wind_direction_10m_dominant",
        ]),
        "timezone": "auto",
    }

    async with httpx.AsyncClient() as client:
        response = await client.get(HISTORICAL_BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()

    daily = data["daily"]
    days = []
    for i in range(len(daily["time"])):
        days.append(DailyHistorical(
            date=daily["time"][i],
            weather_code=daily["weather_code"][i],
            weather_description=_weather_description(daily["weather_code"][i]) if daily["weather_code"][i] is not None else None,
            temperature_max_c=daily["temperature_2m_max"][i],
            temperature_min_c=daily["temperature_2m_min"][i],
            feels_like_max_c=daily["apparent_temperature_max"][i],
            feels_like_min_c=daily["apparent_temperature_min"][i],
            sunrise=daily["sunrise"][i],
            sunset=daily["sunset"][i],
            precipitation_sum_mm=daily["precipitation_sum"][i],
            rain_sum_mm=daily["rain_sum"][i],
            snowfall_sum_cm=daily["snowfall_sum"][i],
            precipitation_hours=daily["precipitation_hours"][i],
            wind_speed_max_kmh=daily["wind_speed_10m_max"][i],
            wind_gusts_max_kmh=daily["wind_gusts_10m_max"][i],
            wind_direction_dominant_deg=daily["wind_direction_10m_dominant"][i],
        ))

    return HistoricalResponse(
        latitude=data["latitude"],
        longitude=data["longitude"],
        elevation=data.get("elevation"),
        timezone=data.get("timezone", "UTC"),
        daily=days,
    )
