from fastapi import FastAPI

from app.routers import weather

app = FastAPI(
    title="Weather API",
    description="REST API for current, forecast, and historical weather data via Open-Meteo",
    version="1.0.0",
)

app.include_router(weather.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
