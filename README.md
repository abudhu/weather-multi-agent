# Weather Multi-Agent

A multi-agent system that combines real-time weather data with web search to answer questions about any place. Built with the **Microsoft Agent Framework**, **Azure AI Foundry**, and a **FastAPI** weather API deployed as an Azure Function.

## How It Works

```
User Question
     │
     ▼
┌──────────────────────────────┐
│     Concurrent Workflow      │
│                              │
│  ┌───────────┐ ┌───────────┐│
│  │ Weather   │ │ Fun Fact  ││
│  │ Agent     │ │ Agent     ││
│  │           │ │(Web Search)│
│  └─────┬─────┘ └─────┬─────┘│
│        │              │      │
│   ┌────┴────┐         │      │
│   │ KB MCP  │         │      │
│   │(AI Search)        │      │
│   │    │    │         │      │
│   │ fallback│         │      │
│   │    ▼    │         │      │
│   │ Live MCP│         │      │
│   │(Weather │         │      │
│   │  API)   │         │      │
│   └─────────┘         │      │
│        │               │     │
│        ▼               ▼     │
│  ┌───────────────────────┐   │
│  │   Summarizer Agent    │   │
│  │(combines both results)│   │
│  └───────────────────────┘   │
└──────────────────────────────┘
```

| Component | Purpose |
|-----------|---------|
| **WeatherAgent** | Gets current/forecast/historical weather via Knowledge Base (cached) or MCP tool (live) |
| **FunFactAgent** | Finds interesting facts via Bing web search |
| **Summarizer** | Combines both into a single conversational response |
| **Weather API** | FastAPI app on Azure Functions, fronted by APIM with MCP support |
| **Knowledge IQ** | Azure AI Search knowledge base indexing cached forecasts from blob storage |

## Project Structure

```
weather-multi-agent/
├── agents/
│   ├── main.py              # Agent definitions + concurrent workflow
│   ├── requirements.txt     # Agent dependencies
│   └── .env                 # Agent config (create from template below)
├── data_loader/
│   ├── load_weather.py      # Fetches forecasts from Open-Meteo → blob storage
│   ├── setup_knowledge_base.py # Creates AI Search knowledge source/base + Foundry connection
│   └── requirements.txt     # Data loader dependencies
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
    ├── search.tf            # Azure AI Search + RBAC for Knowledge IQ
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

This creates: Resource Group, Storage Account, App Service Plan (B1), Function App, APIM (Developer), Application Insights, Log Analytics, AI Foundry + GPT model deployment, Foundry Project, ACR, Capability Host, Azure AI Search (with semantic ranker), and all RBAC assignments.

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
WEATHER_KB_MCP_URL=<knowledge base MCP endpoint from setup_knowledge_base.py output>
WEATHER_KB_CONNECTION_NAME=weather-kb-mcp
```

Get the values from Terraform:
```bash
cd infra
terraform output foundry_project_endpoint
terraform output weather_mcp_url
```

### 4. Load Weather Data & Set Up Knowledge IQ

```bash
cd data_loader
pip install -r requirements.txt

# Fetch 7-day forecasts for Seattle, Chicago, LA → upload to blob storage
python load_weather.py

# Create AI Search knowledge source, knowledge base, and Foundry project connection
pip install httpx azure-identity
python setup_knowledge_base.py
```

This creates:
- A blob knowledge source on AI Search indexing the `weather-data` container
- A knowledge base (`weather-kb`) referencing the knowledge source
- A Foundry project connection (`weather-kb-mcp`) for MCP access

### 5. Run the Agents

```bash
cd agents
pip install -r requirements.txt
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

## Knowledge IQ (Foundry IQ)

The WeatherAgent checks a **knowledge base** on Azure AI Search before calling the live API. This provides faster responses for cities with cached data (Seattle, Chicago, Los Angeles).

The pipeline:
1. `data_loader/load_weather.py` — fetches 7-day forecasts from Open-Meteo and uploads JSON to blob storage (`weather-data` container)
2. AI Search **blob knowledge source** — auto-indexes blobs into a search index with semantic ranker
3. AI Search **knowledge base** — orchestrates agentic retrieval over the knowledge source
4. **Foundry project connection** — exposes the KB as an MCP endpoint the agent can call

The WeatherAgent tries the KB first (via `knowledge_base_retrieve` MCP tool). If the city isn't cached, it falls back to the live Weather MCP.

## MCP Endpoint

The Weather API is also exposed as an MCP server at:
```
https://<apim-name>.azure-api.net/weather-mcp/mcp
```

This is what the WeatherAgent connects to via `FoundryChatClient.get_mcp_tool()`.
