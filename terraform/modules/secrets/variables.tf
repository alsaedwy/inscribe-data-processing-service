variable "environment" {
  description = "Environment name (development, staging, production)"
  type        = string
}

variable "datadog_api_key" {
  description = "Datadog API key"
  type        = string
  sensitive   = true
  default     = null
}

variable "datadog_app_key" {
  description = "Datadog application key"
  type        = string
  sensitive   = true
  default     = null
}

variable "circleci_ssh_private_key" {
  description = "CircleCI SSH private key for deployment"
  type        = string
  sensitive   = true
  default     = null
}

# Note: API credentials (username, password, JWT secret) are now auto-generated
# No variables needed as they're created with random_password and random_string resources
