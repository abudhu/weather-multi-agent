# ─── Microsoft Foundry (AI Services) ─────────────────────────────────────────

provider "azapi" {
  subscription_id = data.azurerm_client_config.current.subscription_id
}

resource "azapi_resource" "ai_foundry" {
  type                      = "Microsoft.CognitiveServices/accounts@2025-06-01"
  name                      = "foundry-${local.name_suffix}"
  parent_id                 = azurerm_resource_group.main.id
  location                  = azurerm_resource_group.main.location
  schema_validation_enabled = false

  body = {
    kind = "AIServices"
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      disableLocalAuth        = true
      allowProjectManagement  = true
      customSubDomainName     = "foundry-${local.name_suffix}"
    }
  }

  response_export_values = ["identity.principalId"]

  tags = local.default_tags
}

# ─── Model Deployment (GPT-4o-mini) ─────────────────────────────────────────

resource "azapi_resource" "gpt_5_4_mini" {
  type      = "Microsoft.CognitiveServices/accounts/deployments@2023-05-01"
  name      = "gpt-5-4-mini"
  parent_id = azapi_resource.ai_foundry.id

  body = {
    sku = {
      name     = "GlobalStandard"
      capacity = 50
    }
    properties = {
      model = {
        format  = "OpenAI"
        name    = "gpt-5.4-mini"
        version = "2026-03-17"
      }
    }
  }

  depends_on = [azapi_resource.ai_foundry]
}

# ─── Foundry Project ────────────────────────────────────────────────────────

resource "azapi_resource" "ai_foundry_project" {
  type                      = "Microsoft.CognitiveServices/accounts/projects@2025-06-01"
  name                      = "weather-agent-project"
  parent_id                 = azapi_resource.ai_foundry.id
  location                  = azurerm_resource_group.main.location
  schema_validation_enabled = false

  body = {
    sku = {
      name = "S0"
    }
    identity = {
      type = "SystemAssigned"
    }
    properties = {
      displayName = "Weather Agent Project"
      description = "Foundry project for the weather multi-agent system"
    }
  }

  response_export_values = ["identity.principalId"]

  tags = local.default_tags
}

# ─── Capability Host (required for hosted agents) ───────────────────────────

resource "azapi_resource" "capability_host" {
  type                      = "Microsoft.CognitiveServices/accounts/capabilityHosts@2025-10-01-preview"
  name                      = "accountcaphost"
  parent_id                 = azapi_resource.ai_foundry.id
  schema_validation_enabled = false

  body = {
    properties = {
      capabilityHostKind             = "Agents"
      enablePublicHostingEnvironment = true
    }
  }

  depends_on = [azapi_resource.ai_foundry_project]
}

# ─── Azure Container Registry (for hosted agent images) ─────────────────────

resource "azurerm_container_registry" "main" {
  name                = replace("acr${local.storage_prefix}${var.project_name}${var.environment}", "-", "")
  resource_group_name = azurerm_resource_group.main.name
  location            = azurerm_resource_group.main.location
  sku                 = "Basic"
  admin_enabled       = false
  tags                = local.default_tags
}

# Grant the Foundry resource identity pull access to ACR
resource "azurerm_role_assignment" "foundry_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azapi_resource.ai_foundry.output.identity.principalId
}

# Grant the Foundry project identity pull access to ACR (hosted agents use project identity)
resource "azurerm_role_assignment" "project_acr_pull" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPull"
  principal_id         = azapi_resource.ai_foundry_project.output.identity.principalId
}

# Grant current user push access to ACR
resource "azurerm_role_assignment" "user_acr_push" {
  scope                = azurerm_container_registry.main.id
  role_definition_name = "AcrPush"
  principal_id         = data.azurerm_client_config.current.object_id
}
