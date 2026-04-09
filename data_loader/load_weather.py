import json
import asyncio
from datetime import date, timedelta

import httpx
from azure.identity import AzureCliCredential
from azure.storage.blob import BlobServiceClient

STORAGE_ACCOUNT = "ambudhuweatherapidev"
CONTAINER_NAME = "weather-data"

CITIES = {
    "seattle": {"latitude": 47.6062, "longitude": -122.3321},
    "chicago": {"latitude": 41.8781, "longitude": -87.6298},
    "los-angeles": {"latitude": 34.0522, "longitude": -118.2437},
}

OPEN_METEO_BASE = "https://api.open-meteo.com/v1/forecast"

DAILY_VARS = [
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
]


async def fetch_forecast(client: httpx.AsyncClient, city: str, coords: dict) -> dict:
    """Fetch 7-day forecast from Open-Meteo for a city."""
    params = {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "daily": ",".join(DAILY_VARS),
        "timezone": "auto",
        "forecast_days": 7,
    }
    resp = await client.get(OPEN_METEO_BASE, params=params)
    resp.raise_for_status()
    data = resp.json()
    return {
        "city": city,
        "latitude": data["latitude"],
        "longitude": data["longitude"],
        "elevation": data.get("elevation"),
        "timezone": data.get("timezone"),
        "fetched_at": date.today().isoformat(),
        "daily": _reshape_daily(data["daily"]),
    }


def _reshape_daily(daily: dict) -> list[dict]:
    """Reshape Open-Meteo's columnar daily data into a list of day records."""
    dates = daily["time"]
    records = []
    for i, d in enumerate(dates):
        record = {"date": d}
        for key in DAILY_VARS:
            record[key] = daily.get(key, [None] * len(dates))[i]
        records.append(record)
    return records


def upload_to_blob(blob_service: BlobServiceClient, city: str, data: dict):
    """Upload city weather JSON to blob storage."""
    blob_name = f"{date.today().isoformat()}/{city}.json"
    container_client = blob_service.get_container_client(CONTAINER_NAME)
    container_client.upload_blob(
        name=blob_name,
        data=json.dumps(data, indent=2),
        overwrite=True,
    )
    print(f"  Uploaded: {blob_name}")


async def main():
    credential = AzureCliCredential()
    blob_service = BlobServiceClient(
        account_url=f"https://{STORAGE_ACCOUNT}.blob.core.windows.net",
        credential=credential,
    )

    print(f"Fetching 7-day forecasts for {len(CITIES)} cities...")
    async with httpx.AsyncClient(timeout=30) as client:
        for city, coords in CITIES.items():
            print(f"  {city}...")
            data = await fetch_forecast(client, city, coords)
            upload_to_blob(blob_service, city, data)

    print("Done!")


if __name__ == "__main__":
    asyncio.run(main())
