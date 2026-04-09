# ─── API Management ──────────────────────────────────────────────────────────

resource "azurerm_api_management" "main" {
  name                          = "apim-${local.name_suffix}"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  publisher_name                = var.apim_publisher_name
  publisher_email               = var.apim_publisher_email
  sku_name                      = var.apim_sku_name
  tags                          = local.default_tags
}

# ─── APIM Backend pointing to the Function App ──────────────────────────────

resource "azurerm_api_management_backend" "func" {
  name                = "weather-func-backend"
  resource_group_name = azurerm_resource_group.main.name
  api_management_name = azurerm_api_management.main.name
  protocol            = "http"
  url                 = "https://${azurerm_linux_function_app.main.default_hostname}"
}

# ─── Weather API definition in APIM ─────────────────────────────────────────

resource "azurerm_api_management_api" "weather" {
  name                  = "weather-api"
  resource_group_name   = azurerm_resource_group.main.name
  api_management_name   = azurerm_api_management.main.name
  revision              = "1"
  display_name          = "Weather API"
  description           = "Current, forecast, and historical weather data via Open-Meteo"
  path                  = "weather"
  protocols             = ["https"]
  service_url           = "https://${azurerm_linux_function_app.main.default_hostname}"
  subscription_required = false
}

# ─── API Operations ──────────────────────────────────────────────────────────

resource "azurerm_api_management_api_operation" "current_weather" {
  operation_id        = "get-current-weather"
  api_name            = azurerm_api_management_api.weather.name
  api_management_name = azurerm_api_management.main.name
  resource_group_name = azurerm_resource_group.main.name
  display_name        = "Get Current Weather"
  method              = "GET"
  url_template        = "/weather/current"
  description         = "Get current weather conditions for a location"

  request {
    query_parameter {
      name     = "latitude"
      type     = "number"
      required = true
    }
    query_parameter {
      name     = "longitude"
      type     = "number"
      required = true
    }
  }

  response {
    status_code = 200
    description = "Current weather data"
  }
}

resource "azurerm_api_management_api_operation" "forecast" {
  operation_id        = "get-weather-forecast"
  api_name            = azurerm_api_management_api.weather.name
  api_management_name = azurerm_api_management.main.name
  resource_group_name = azurerm_resource_group.main.name
  display_name        = "Get 7-Day Forecast"
  method              = "GET"
  url_template        = "/weather/forecast"
  description         = "Get a 7-day weather forecast for a location"

  request {
    query_parameter {
      name     = "latitude"
      type     = "number"
      required = true
    }
    query_parameter {
      name     = "longitude"
      type     = "number"
      required = true
    }
  }

  response {
    status_code = 200
    description = "7-day forecast data"
  }
}

resource "azurerm_api_management_api_operation" "historical" {
  operation_id        = "get-historical-weather"
  api_name            = azurerm_api_management_api.weather.name
  api_management_name = azurerm_api_management.main.name
  resource_group_name = azurerm_resource_group.main.name
  display_name        = "Get Historical Weather"
  method              = "GET"
  url_template        = "/weather/historical"
  description         = "Get historical weather data for a location and date range"

  request {
    query_parameter {
      name     = "latitude"
      type     = "number"
      required = true
    }
    query_parameter {
      name     = "longitude"
      type     = "number"
      required = true
    }
    query_parameter {
      name     = "start_date"
      type     = "string"
      required = true
    }
    query_parameter {
      name     = "end_date"
      type     = "string"
      required = true
    }
  }

  response {
    status_code = 200
    description = "Historical weather data"
  }
}

resource "azurerm_api_management_api_operation" "health" {
  operation_id        = "health-check"
  api_name            = azurerm_api_management_api.weather.name
  api_management_name = azurerm_api_management.main.name
  resource_group_name = azurerm_resource_group.main.name
  display_name        = "Health Check"
  method              = "GET"
  url_template        = "/health"
  description         = "API health check"

  response {
    status_code = 200
    description = "Service is healthy"
  }
}
