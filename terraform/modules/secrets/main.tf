# AWS Secrets Manager for sensitive configuration

# Generate random credentials for API authentication
resource "random_password" "api_password" {
  length  = 32
  special = true
  upper   = true
  lower   = true
  numeric = true
}

resource "random_string" "api_username" {
  length  = 16
  special = false
  upper   = false
  lower   = true
  numeric = true
}

resource "random_password" "jwt_secret" {
  length  = 64
  special = true
  upper   = true
  lower   = true
  numeric = true
}

# Generate random suffixes for secret names to avoid conflicts
resource "random_string" "secret_suffix" {
  length  = 5
  special = false
  upper   = false
  lower   = false
  numeric = true
}

# Datadog API Key Secret
resource "aws_secretsmanager_secret" "datadog_api_key" {
  name        = "${var.environment}-inscribe-datadog-api-key-${random_string.secret_suffix.result}"
  description = "Datadog API key for ${var.environment} environment"
  
  tags = {
    Name        = "${var.environment}-inscribe-datadog-api-key-${random_string.secret_suffix.result}"
    Environment = var.environment
    Service     = "inscribe-customer-service"
  }
}

resource "aws_secretsmanager_secret_version" "datadog_api_key" {
  secret_id = aws_secretsmanager_secret.datadog_api_key.id
  secret_string = jsonencode({
    api_key = var.datadog_api_key
  })
}

# Datadog Application Key Secret
resource "aws_secretsmanager_secret" "datadog_app_key" {
  name        = "${var.environment}-inscribe-datadog-app-key-${random_string.secret_suffix.result}"
  description = "Datadog application key for ${var.environment} environment"
  
  tags = {
    Name        = "${var.environment}-inscribe-datadog-app-key-${random_string.secret_suffix.result}"
    Environment = var.environment
    Service     = "inscribe-customer-service"
  }
}

resource "aws_secretsmanager_secret_version" "datadog_app_key" {
  secret_id = aws_secretsmanager_secret.datadog_app_key.id
  secret_string = jsonencode({
    app_key = var.datadog_app_key
  })
}

# CircleCI SSH Key for deployment (if needed)
resource "aws_secretsmanager_secret" "circleci_ssh_key" {
  name        = "${var.environment}-inscribe-circleci-ssh-key-${random_string.secret_suffix.result}"
  description = "CircleCI SSH private key for deployment"
  
  tags = {
    Name        = "${var.environment}-inscribe-circleci-ssh-key-${random_string.secret_suffix.result}"
    Environment = var.environment
    Service     = "inscribe-customer-service"
  }
}

resource "aws_secretsmanager_secret_version" "circleci_ssh_key" {
  count     = var.circleci_ssh_private_key != null ? 1 : 0
  secret_id = aws_secretsmanager_secret.circleci_ssh_key.id
  secret_string = jsonencode({
    private_key = var.circleci_ssh_private_key
  })
}

# Application secrets (API keys, JWT secrets, etc.)
resource "aws_secretsmanager_secret" "application_secrets" {
  name        = "${var.environment}-inscribe-application-secrets-${random_string.secret_suffix.result}"
  description = "Application-level secrets and configuration"
  
  tags = {
    Name        = "${var.environment}-inscribe-application-secrets-${random_string.secret_suffix.result}"
    Environment = var.environment
    Service     = "inscribe-customer-service"
  }
}

resource "aws_secretsmanager_secret_version" "application_secrets" {
  secret_id = aws_secretsmanager_secret.application_secrets.id
  secret_string = jsonencode({
    basic_auth_username = random_string.api_username.result
    basic_auth_password = random_password.api_password.result
    jwt_secret_key     = random_password.jwt_secret.result
  })
}
