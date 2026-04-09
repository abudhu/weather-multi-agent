output "resource_group_name" {
  value = azurerm_resource_group.main.name
}

output "function_app_name" {
  value = azurerm_linux_function_app.main.name
}

output "function_app_url" {
  value = "https://${azurerm_linux_function_app.main.default_hostname}"
}

output "apim_gateway_url" {
  value = azurerm_api_management.main.gateway_url
}

output "apim_weather_api_url" {
  value = "${azurerm_api_management.main.gateway_url}/weather"
}

output "application_insights_name" {
  value = azurerm_application_insights.main.name
}

output "deploy_command" {
  value       = "cd ${path.root}/.. && func azure functionapp publish ${azurerm_linux_function_app.main.name}"
  description = "Run this command to deploy your function code after terraform apply"
}

output "foundry_resource_name" {
  value = azapi_resource.ai_foundry.name
}

output "foundry_project_name" {
  value = azapi_resource.ai_foundry_project.name
}

output "foundry_endpoint" {
  value = "https://${azapi_resource.ai_foundry.name}.services.ai.azure.com"
}

output "foundry_project_endpoint" {
  value = "https://${azapi_resource.ai_foundry.name}.services.ai.azure.com/api/projects/${azapi_resource.ai_foundry_project.name}"
}

output "container_registry_name" {
  value = azurerm_container_registry.main.name
}

output "container_registry_login_server" {
  value = azurerm_container_registry.main.login_server
}

output "weather_mcp_url" {
  value       = "${azurerm_api_management.main.gateway_url}/weather-mcp/mcp"
  description = "MCP endpoint URL for the Weather API in APIM"
}

output "storage_account_name" {
  value = azurerm_storage_account.func.name
}
