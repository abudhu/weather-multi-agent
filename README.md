# Weather Multi-Agent

A multi-agent system that combines real-time weather data with web search to answer questions about any place. Built with the **Microsoft Agent Framework**, **Azure AI Foundry**, and a **FastAPI** weather API deployed as an Azure Function.

## How It Works

```
User Question
     │
     ▼
┌─────────────────────────┐
│   Concurrent Workflow    │
│                         │
│  ┌───────────┐ ┌──────────────┐
│  │ Weather   │ │  Fun Fact    │
│  │ Agent     │ │  Agent       │
│  │ (MCP)     │ │ (Web Search) │
│  └─────┬─────┘ └──────┬───────┘
│        │               │
│        ▼               ▼
│  ┌─────────────────────────┐
│  │   Summarizer Agent      │
│  │ (combines both results) │
│  └─────────────────────────┘
└─────────────────────────┘
```

| Component | Purpose |
|-----------|---------|
| **WeatherAgent** | Gets current/forecast/historical weather via MCP tool → Weather API |
| **FunFactAgent** | Finds interesting facts via Bing web search |
| **Summarizer** | Combines both into a single conversational response |
| **Weather API** | FastAPI app on Azure Functions, fronted by APIM with MCP support |

## Project Structure

```
weather-multi-agent/
├── agents/
│   ├── main.py              # Agent definitions + concurrent workflow
│   ├── requirements.txt     # Agent dependencies
│   └── .env                 # Agent config (create from template below)
├── weather_api/
│   ├── main.py              # FastAPI app + health endpoint
│   ├── routers/weather.py   # Weather route handlers
│   ├── services/open_meteo.py # Open-Meteo API client
│   └── models/weather.py    # Pydantic models
├── function_app.py          # Azure Function entry point (ASGI wrapper)
├── host.json                # Azure Functions host config
├── requirements.txt         # Weather API dependencies
└── infra/
    ├── main.tf              # Core Azure resources
    ├── foundry.tf           # AI Foundry, model deployment, project
    ├── apim.tf              # API Management + MCP endpoint
    ├── variables.tf         # Input variables
    ├── outputs.tf           # Output values
    └── terraform.tfvars.example
```

## Prerequisites

- Python 3.11+
- [Terraform](https://developer.hashicorp.com/terraform/install) >= 1.5
- [Azure CLI](https://learn.microsoft.com/en-us/cli/azure/install-azure-cli) — authenticated via `az login`

## Deploy

### 1. Provision Infrastructure

```bash
cd infra
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set resource_prefix, publisher email, etc.
terraform init
terraform apply
```

This creates: Resource Group, Storage Account, App Service Plan (B1), Function App, APIM (Developer), Application Insights, Log Analytics, AI Foundry + GPT model deployment, Foundry Project, ACR, Capability Host, and all RBAC assignments.

### 2. Deploy the Weather API

**Linux / macOS:**
```bash
zip -r deploy.zip function_app.py host.json requirements.txt weather_api/
az webapp deploy \
  --name $(cd infra && terraform output -raw function_app_name) \
  --resource-group $(cd infra && terraform output -raw resource_group_name) \
  --src-path deploy.zip --type zip --async false
```

**Windows (PowerShell):**
```powershell
Compress-Archive -Path function_app.py, host.json, requirements.txt, weather_api -DestinationPath deploy.zip -Force
az webapp deploy `
  --name (cd infra; terraform output -raw function_app_name) `
  --resource-group (cd infra; terraform output -raw resource_group_name) `
  --src-path deploy.zip --type zip --async false
```

### 3. Configure the Agents

Create `agents/.env`:
```env
AZURE_AI_PROJECT_ENDPOINT=<foundry_project_endpoint from terraform output>
AZURE_AI_MODEL_DEPLOYMENT_NAME=<model deployment name, e.g. gpt-5-4-mini>
WEATHER_MCP_URL=<weather_mcp_url from terraform output>
```

Get the values from Terraform:
```bash
cd infra
terraform output foundry_project_endpoint
terraform output weather_mcp_url
```

Install agent dependencies:
```bash
cd agents
pip install -r requirements.txt
```

### 4. Run the Agents

```bash
cd agents
python main.py
```

Opens the dev UI at `http://localhost:8090`. You can interact with:
- **WeatherAgent** — ask about weather anywhere
- **FunFactAgent** — ask for fun facts about any topic
- **ConcurrentBuilder workflow** — ask about a place and get weather + fun facts combined

## Weather API Endpoints

Base URL: `https://<apim-name>.azure-api.net/weather`

| Endpoint | Description |
|----------|-------------|
| `GET /weather/current?latitude=47.6&longitude=-122.3` | Current conditions |
| `GET /weather/forecast?latitude=47.6&longitude=-122.3` | 7-day forecast |
| `GET /weather/historical?latitude=47.6&longitude=-122.3&start_date=2026-01-01&end_date=2026-01-07` | Historical data |
| `GET /health` | Health check |

Weather data from [Open-Meteo](https://open-meteo.com/) — free, no API key required.

## MCP Endpoint

The Weather API is also exposed as an MCP server at:
```
https://<apim-name>.azure-api.net/weather-mcp/mcp
```

This is what the WeatherAgent connects to via `FoundryChatClient.get_mcp_tool()`.
