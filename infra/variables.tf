variable "resource_prefix" {
  description = "Unique prefix for all globally-named resources (e.g. your initials or alias)"
  type        = string
  default     = ""
}

variable "project_name" {
  description = "Base name for all resources"
  type        = string
  default     = "weather-api"
}

variable "location" {
  description = "Azure region for all resources"
  type        = string
  default     = "eastus2"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "apim_publisher_name" {
  description = "APIM publisher name"
  type        = string
}

variable "apim_publisher_email" {
  description = "APIM publisher email"
  type        = string
}

variable "apim_sku_name" {
  description = "APIM SKU (Developer, Basic, Standard, Premium). Consumption does not support MCP servers."
  type        = string
  default     = "Developer_1"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
