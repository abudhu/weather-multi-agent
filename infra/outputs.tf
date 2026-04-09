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
