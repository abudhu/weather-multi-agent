locals {
  name_suffix = var.resource_prefix != "" ? "${var.resource_prefix}-${var.project_name}-${var.environment}" : "${var.project_name}-${var.environment}"
  storage_prefix = var.resource_prefix != "" ? var.resource_prefix : "am"
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
    azapi = {
      source  = "azure/azapi"
      version = "~> 2.0"
    }
  }
}

provider "azurerm" {
  storage_use_azuread = true

  features {
    api_management {
      purge_soft_delete_on_destroy = true
    }
    key_vault {
      purge_soft_delete_on_destroy = true
    }
    log_analytics_workspace {
      permanently_delete_on_destroy = true
    }
    resource_group {
      prevent_deletion_if_contains_resources = false
    }
  }
}

# ─── Resource Group ──────────────────────────────────────────────────────────

resource "azurerm_resource_group" "main" {
  name     = "rg-${local.name_suffix}"
  location = var.location
  tags     = local.default_tags
}

# ─── Storage Account (required by Azure Functions) ───────────────────────────

resource "azurerm_storage_account" "func" {
  name                          = replace("${local.storage_prefix}${var.project_name}${var.environment}", "-", "")
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  account_tier                  = "Standard"
  account_replication_type      = "LRS"
  min_tls_version               = "TLS1_2"
  shared_access_key_enabled     = false
  tags                          = local.default_tags
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
  name                          = "ai-${local.name_suffix}"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  workspace_id                  = azurerm_log_analytics_workspace.main.id
  application_type              = "other"
  internet_ingestion_enabled    = true
  internet_query_enabled        = true
  force_customer_storage_for_profiler = false
  tags                          = local.default_tags
}

# ─── App Service Plan (Basic for Functions) ──────────────────────────────────

resource "azurerm_service_plan" "func" {
  name                = "asp-${local.name_suffix}"
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  os_type             = "Linux"
  sku_name            = "B1"
  tags                = local.default_tags
}

# ─── Azure Function App ─────────────────────────────────────────────────────

resource "azurerm_linux_function_app" "main" {
  name                          = "func-${local.name_suffix}"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  service_plan_id               = azurerm_service_plan.func.id
  storage_account_name          = azurerm_storage_account.func.name
  storage_uses_managed_identity = true
  tags                          = local.default_tags

  identity {
    type = "SystemAssigned"
  }

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

# ─── Role Assignments for Function App → Storage ─────────────────────────────

data "azurerm_client_config" "current" {}

resource "azurerm_role_assignment" "func_storage_blob_owner" {
  scope                = azurerm_storage_account.func.id
  role_definition_name = "Storage Blob Data Owner"
  principal_id         = azurerm_linux_function_app.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "func_storage_account_contributor" {
  scope                = azurerm_storage_account.func.id
  role_definition_name = "Storage Account Contributor"
  principal_id         = azurerm_linux_function_app.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "func_storage_queue_contributor" {
  scope                = azurerm_storage_account.func.id
  role_definition_name = "Storage Queue Data Contributor"
  principal_id         = azurerm_linux_function_app.main.identity[0].principal_id
}

resource "azurerm_role_assignment" "func_storage_table_contributor" {
  scope                = azurerm_storage_account.func.id
  role_definition_name = "Storage Table Data Contributor"
  principal_id         = azurerm_linux_function_app.main.identity[0].principal_id
}

# ─── Blob Container for Weather Data ─────────────────────────────────────────

resource "azurerm_storage_container" "weather_data" {
  name                  = "weather-data"
  storage_account_id    = azurerm_storage_account.func.id
  container_access_type = "private"
}

resource "azurerm_role_assignment" "user_storage_blob_contributor" {
  scope                = azurerm_storage_account.func.id
  role_definition_name = "Storage Blob Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}
