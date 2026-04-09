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
  description = "APIM SKU (Consumption, Developer, Basic, Standard, Premium)"
  type        = string
  default     = "Consumption_0"
}

variable "tags" {
  description = "Tags to apply to all resources"
  type        = map(string)
  default     = {}
}
