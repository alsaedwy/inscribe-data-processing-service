output "datadog_api_key_secret_arn" {
  description = "ARN of the Datadog API key secret"
  value       = aws_secretsmanager_secret.datadog_api_key.arn
}

output "datadog_app_key_secret_arn" {
  description = "ARN of the Datadog application key secret"
  value       = aws_secretsmanager_secret.datadog_app_key.arn
}

output "circleci_ssh_key_secret_arn" {
  description = "ARN of the CircleCI SSH key secret"
  value       = aws_secretsmanager_secret.circleci_ssh_key.arn
}

output "application_secrets_secret_arn" {
  description = "ARN of the application secrets"
  value       = aws_secretsmanager_secret.application_secrets.arn
}

# Secret names for application configuration
output "datadog_api_key_secret_name" {
  description = "Name of the Datadog API key secret"
  value       = aws_secretsmanager_secret.datadog_api_key.name
}

output "datadog_app_key_secret_name" {
  description = "Name of the Datadog application key secret"
  value       = aws_secretsmanager_secret.datadog_app_key.name
}

output "application_secrets_secret_name" {
  description = "Name of the application secrets"
  value       = aws_secretsmanager_secret.application_secrets.name
}

output "secret_arns" {
  description = "List of all secret ARNs for IAM policy creation"
  value = [
    aws_secretsmanager_secret.datadog_api_key.arn,
    aws_secretsmanager_secret.datadog_app_key.arn,
    aws_secretsmanager_secret.circleci_ssh_key.arn,
    aws_secretsmanager_secret.application_secrets.arn
  ]
}

# Generated credentials outputs (sensitive) - for emergency access only
output "generated_api_username" {
  description = "Generated API username (for emergency reference only - retrieve via AWS CLI)"
  value       = random_string.api_username.result
  sensitive   = true
}

output "generated_api_password" {
  description = "Generated API password (for emergency reference only - retrieve via AWS CLI)"
  value       = random_password.api_password.result
  sensitive   = true
}

output "generated_jwt_secret" {
  description = "Generated JWT secret (for emergency reference only - retrieve via AWS CLI)"
  value       = random_password.jwt_secret.result
  sensitive   = true
}
