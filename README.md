# Weather Multi-Agent API

A REST API providing current, forecast, and historical weather data powered by [Open-Meteo](https://open-meteo.com/). Built with **FastAPI**, deployed as an **Azure Function**, and exposed through **Azure API Management (APIM)**.

## Architecture

```
Client → Azure APIM → Azure Function (FastAPI) → Open-Meteo APIs
```

| Component | Technology |
|-----------|-----------|
| Runtime | Azure Functions v2 (Python 3.11, Linux) |
| Framework | FastAPI (ASGI via `AsgiFunctionApp`) |
| Gateway | Azure API Management (Consumption tier) |
| Weather Data | Open-Meteo (free, no API key required) |
| Monitoring | Application Insights + Log Analytics |
| IaC | Terraform |

## API Endpoints

All endpoints accept `latitude` and `longitude` as required query parameters (WGS84 coordinates).

### `GET /weather/current`

Returns current weather conditions for a location.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `latitude` | float | Yes | Latitude (-90 to 90) |
| `longitude` | float | Yes | Longitude (-180 to 180) |

**Example:**
```
GET /weather/current?latitude=40.7128&longitude=-74.0060
```

**Response:**
```json
{
  "latitude": 40.71,
  "longitude": -73.99,
  "elevation": 32.0,
  "timezone": "America/New_York",
  "time": "2026-04-08T20:30",
  "temperature_c": 3.4,
  "feels_like_c": -0.9,
  "humidity_pct": 65.0,
  "precipitation_mm": 0.0,
  "rain_mm": 0.0,
  "snowfall_cm": 0.0,
  "weather_code": 0,
  "weather_description": "Clear sky",
  "cloud_cover_pct": 1.0,
  "wind_speed_kmh": 12.0,
  "wind_direction_deg": 134.0,
  "wind_gusts_kmh": 27.4,
  "pressure_msl_hpa": 1035.3,
  "is_day": false
}
```

### `GET /weather/forecast`

Returns a 7-day daily weather forecast.

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `latitude` | float | Yes | Latitude (-90 to 90) |
| `longitude` | float | Yes | Longitude (-180 to 180) |

**Example:**
```
GET /weather/forecast?latitude=47.6062&longitude=-122.3321
```

**Response:**
```json
{
  "latitude": 47.61,
  "longitude": -122.33,
  "elevation": 56.0,
  "timezone": "America/Los_Angeles",
  "daily": [
    {
      "date": "2026-04-08",
      "weather_code": 3,
      "weather_description": "Overcast",
      "temperature_max_c": 12.5,
      "temperature_min_c": 5.2,
      "feels_like_max_c": 10.1,
      "feels_like_min_c": 2.8,
      "sunrise": "2026-04-08T06:32",
      "sunset": "2026-04-08T19:52",
      "precipitation_sum_mm": 0.0,
      "rain_sum_mm": 0.0,
      "snowfall_sum_cm": 0.0,
      "precipitation_hours": 0.0,
      "wind_speed_max_kmh": 18.1,
      "wind_gusts_max_kmh": 37.4,
      "wind_direction_dominant_deg": 200.0,
      "uv_index_max": 5.2
    }
  ]
}
```

### `GET /weather/historical`

Returns historical daily weather data for a given date range (data available from 1940 to present).

**Parameters:**

| Name | Type | Required | Description |
|------|------|----------|-------------|
| `latitude` | float | Yes | Latitude (-90 to 90) |
| `longitude` | float | Yes | Longitude (-180 to 180) |
| `start_date` | string | Yes | Start date (`YYYY-MM-DD`) |
| `end_date` | string | Yes | End date (`YYYY-MM-DD`) |

**Example:**
```
GET /weather/historical?latitude=40.7128&longitude=-74.0060&start_date=2026-03-01&end_date=2026-03-07
```

**Response:** Same structure as forecast but without `uv_index_max`.

### `GET /health`

Health check endpoint. Returns `{"status": "ok"}`.

### `GET /openapi.json`

Auto-generated OpenAPI 3.1 specification. Can be imported directly into APIM or used with Swagger UI.

## Project Structure

```
weather-multi-agent/
├── function_app.py              # Azure Function entry point (ASGI wrapper)
├── host.json                    # Azure Functions host configuration
├── local.settings.json          # Local development settings
├── requirements.txt             # Python dependencies (Weather API)
├── .gitignore
├── weather_api/
│   ├── main.py                  # FastAPI app definition + health endpoint
│   ├── routers/
│   │   └── weather.py           # Weather API route handlers
│   ├── services/
│   │   └── open_meteo.py        # Open-Meteo API client + WMO code mapping
│   └── models/
│       └── weather.py           # Pydantic request/response models
└── infra/
    ├── main.tf                  # Core Azure resources (RG, Storage, Function, App Insights)
    ├── foundry.tf               # Microsoft Foundry, model deployment, project, ACR
    ├── apim.tf                  # API Management + API operations
    ├── variables.tf             # Terraform input variables
    ├── outputs.tf               # Terraform outputs (URLs, deploy command)
    └── terraform.tfvars.example # Example variable values
```

## Prerequisites

- **Python 3.11+**
- **Azure Functions Core Tools v4** — `npm install -g azure-functions-core-tools@4`
- **Terraform >= 1.5**
- **Azure CLI** — authenticated with `az login`

## Local Development

1. **Create a virtual environment and install dependencies:**

   **Linux / macOS:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

   **Windows (PowerShell):**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements.txt
   ```

2. **Run locally with uvicorn (for fast iteration):**
   ```bash
   uvicorn weather_api.main:app --reload --port 8000
   ```
   API available at `http://localhost:8000`. Swagger UI at `http://localhost:8000/docs`.

3. **Run locally as an Azure Function:**
   ```bash
   func start
   ```

## Deploy to Azure

### 1. Provision Infrastructure

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your values (publisher name/email, etc.)
terraform init
terraform plan
terraform apply
```

This creates:
- Resource Group
- Storage Account
- Log Analytics Workspace + Application Insights
- App Service Plan (Linux Basic B1)
- Azure Function App (Python 3.11)
- Azure API Management (Developer tier)
- APIM Weather API with all operations configured
- Microsoft Foundry resource (AI Services) with GPT model deployment
- Foundry Project for agents
- Azure Container Registry
- Capability Host for hosted agents

### 2. Deploy Function Code

After infrastructure is provisioned, create a deployment package and deploy:

**Linux / macOS:**
```bash
zip -r deploy.zip function_app.py host.json requirements.txt local.settings.json weather_api/
az webapp deploy --name <function-app-name> --resource-group <resource-group-name> --src-path deploy.zip --type zip --async false
```

**Windows (PowerShell):**
```powershell
Compress-Archive -Path function_app.py, host.json, requirements.txt, local.settings.json, weather_api -DestinationPath deploy.zip -Force
az webapp deploy --name <function-app-name> --resource-group <resource-group-name> --src-path deploy.zip --type zip --async false
```

The exact function app name is available in the Terraform output:
```bash
cd infra && terraform output function_app_name
```

### 3. Verify

```bash
# Direct Function App URL
curl "https://<function-app-name>.azurewebsites.net/weather/current?latitude=47.6062&longitude=-122.3321"

# Via APIM
curl "https://<apim-name>.azure-api.net/weather/weather/current?latitude=47.6062&longitude=-122.3321"
```

## Weather Data Source

This API uses [Open-Meteo](https://open-meteo.com/) — a free, open-source weather API:

- **No API key required** for non-commercial use (< 10,000 daily calls)
- Forecast data from multiple national weather services (DWD, NOAA, ECMWF, Météo-France, etc.)
- Historical data from ERA5/ERA5-Land reanalysis datasets back to 1940
- 9 km spatial resolution (ECMWF IFS) for modern data

Weather conditions are returned using [WMO Weather Interpretation Codes](https://open-meteo.com/en/docs) with human-readable descriptions mapped automatically.

## Next Steps

This API serves as the foundation for a broader multi-agent system using Azure AI services. The Terraform configuration provisions a Microsoft Foundry resource with a GPT model deployment and project — create your agents in the [Foundry portal](https://ai.azure.com/) and connect them to the Weather API via MCP.
