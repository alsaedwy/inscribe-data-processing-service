variable "environment" {
  description = "Environment name"
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
}

variable "iam_instance_profile" {
  description = "IAM instance profile name for EC2"
  type        = string
  default     = null
}

variable "subnet_id" {
  description = "Subnet ID for EC2 instance"
  type        = string
}

variable "security_group_id" {
  description = "Security group ID for EC2 instance"
  type        = string
}

variable "db_endpoint" {
  description = "RDS endpoint"
  type        = string
}

variable "db_name" {
  description = "Database name"
  type        = string
}

variable "db_username" {
  description = "Database username"
  type        = string
}

variable "db_password" {
  description = "Database password"
  type        = string
  sensitive   = true
}

variable "application_secrets_name" {
  description = "Name of the application secrets in AWS Secrets Manager"
  type        = string
}

variable "rds_credentials_secret_name" {
  description = "Name of the RDS credentials secret in AWS Secrets Manager"
  type        = string
}

variable "datadog_api_key_secret_name" {
  description = "Name of the Datadog API key secret in AWS Secrets Manager"
  type        = string
}

variable "datadog_app_key_secret_name" {
  description = "Name of the Datadog application key secret in AWS Secrets Manager"
  type        = string
}
