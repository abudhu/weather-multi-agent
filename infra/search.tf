# ─── Azure AI Search ─────────────────────────────────────────────────────────

resource "azurerm_search_service" "main" {
  name                          = "search-${local.name_suffix}"
  resource_group_name           = azurerm_resource_group.main.name
  location                      = azurerm_resource_group.main.location
  sku                           = "basic"
  replica_count                 = 1
  partition_count               = 1
  semantic_search_sku           = "standard"
  local_authentication_enabled  = true
  authentication_failure_mode   = "http401WithBearerChallenge"
  tags                          = local.default_tags

  identity {
    type = "SystemAssigned"
  }
}

# Grant Foundry project identity read access to search indexes
resource "azurerm_role_assignment" "project_search_index_reader" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azapi_resource.ai_foundry_project.output.identity.principalId
}

# Grant Foundry resource identity read access to search indexes
resource "azurerm_role_assignment" "foundry_search_index_reader" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Reader"
  principal_id         = azapi_resource.ai_foundry.output.identity.principalId
}

# Grant current user contributor access for knowledge base creation
resource "azurerm_role_assignment" "user_search_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Service Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

resource "azurerm_role_assignment" "user_search_index_contributor" {
  scope                = azurerm_search_service.main.id
  role_definition_name = "Search Index Data Contributor"
  principal_id         = data.azurerm_client_config.current.object_id
}

# Grant AI Search identity read access to blob storage (for indexing)
resource "azurerm_role_assignment" "search_storage_blob_reader" {
  scope                = azurerm_storage_account.func.id
  role_definition_name = "Storage Blob Data Reader"
  principal_id         = azurerm_search_service.main.identity[0].principal_id
}
