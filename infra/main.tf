locals {
  name_suffix = "${var.project_name}-${var.environment}"
  default_tags = merge(var.tags, {
    project     = var.project_name
    environment = var.environment
    managed_by  = "terraform"
  })
}

terraform {
  required_version = ">= 1.5"

  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }
  }
}

provider "azurerm" {
  features {}
}

# ─── Resource Group ──────────────────────────────────────────────────────────

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_suffix}"
  location = var.location
  tags     = local.default_tags
}

# ─── Storage Account (required by Azure Functions) ───────────────────────────

resource "azurerm_storage_account" "func" {
  name                     = replace("st${var.project_name}${var.environment}", "-", "")
  resource_group_name      = azurerm_resource_group.main.name
  location                 = azurerm_resource_group.main.location
  account_tier             = "Standard"
  account_replication_type = "LRS"
  min_tls_version          = "TLS1_2"
  tags                     = local.default_tags
}

# ─── Application Insights ────────────────────────────────────────────────────

resource "azurerm_log_analytics_workspace" "main" {
  name                = "law-${local.name_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "PerGB2018"
  retention_in_days   = 30
  tags                = local.default_tags
}

resource "azurerm_application_insights" "main" {
  name                = "ai-${local.name_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  workspace_id        = azurerm_log_analytics_workspace.main.id
  application_type    = "other"
  tags                = local.default_tags
}

# ─── App Service Plan (Consumption for Functions) ────────────────────────────

resource "azurerm_service_plan" "func" {
  name                = "asp-${local.name_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "Y1"
  tags                = local.default_tags
}

# ─── Azure Function App ─────────────────────────────────────────────────────

resource "azurerm_linux_function_app" "main" {
  name                       = "func-${local.name_suffix}"
  resource_group_name        = azurerm_resource_group.main.name
  location                   = azurerm_resource_group.main.location
  service_plan_id            = azurerm_service_plan.func.id
  storage_account_name       = azurerm_storage_account.func.name
  storage_account_access_key = azurerm_storage_account.func.primary_access_key
  tags                       = local.default_tags

  site_config {
    application_stack {
      python_version = "3.11"
    }

    cors {
      allowed_origins = ["*"]
    }
  }

  app_settings = {
    "APPINSIGHTS_INSTRUMENTATIONKEY"        = azurerm_application_insights.main.instrumentation_key
    "APPLICATIONINSIGHTS_CONNECTION_STRING"  = azurerm_application_insights.main.connection_string
    "AzureWebJobsFeatureFlags"              = "EnableWorkerIndexing"
    "BUILD_FLAGS"                           = "UseExpressBuild"
    "SCM_DO_BUILD_DURING_DEPLOYMENT"        = "true"
    "ENABLE_ORYX_BUILD"                     = "true"
  }
}
