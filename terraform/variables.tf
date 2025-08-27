# Variables for Terraform configuration
variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-west-1"
}

variable "environment" {
  description = "Environment name (e.g., dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "instance_type" {
  description = "EC2 instance type for the microservice - t3.micro for free tier"
  type        = string
  default     = "t3.micro" # Free tier eligible
}

variable "enable_ssm_access" {
  description = "Whether to enable AWS Systems Manager Session Manager for EC2 access"
  type        = bool
  default     = true
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the services"
  type        = list(string)
  default     = ["0.0.0.0/0"] # Restrict this in production
}

variable "db_instance_class" {
  description = "RDS instance class - db.t3.micro for free tier"
  type        = string
  default     = "db.t3.micro" # Free tier eligible
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance (GB) - 20GB max for free tier"
  type        = number
  default     = 20 # Free tier limit
}

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "inscribe_customers"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "admin"
}

variable "db_port" {
  description = "Database port"
  type        = number
  default     = 3306
}

variable "enable_rds_iam_auth" {
  description = "Enable RDS IAM authentication"
  type        = bool
  default     = false
}

variable "backup_retention_period" {
  description = "Backup retention period for RDS - 7 days max for free tier"
  type        = number
  default     = 7 # Free tier limit
}

variable "backup_window" {
  description = "Backup window for RDS"
  type        = string
  default     = "03:00-04:00"
}

variable "maintenance_window" {
  description = "Maintenance window for RDS"
  type        = string
  default     = "sun:04:00-sun:05:00"
}

# Observability Configuration
variable "datadog_api_key" {
  description = "Datadog API key for monitoring and logging"
  type        = string
  sensitive   = true
  default     = null
}

variable "datadog_app_key" {
  description = "Datadog application key for monitoring"
  type        = string
  sensitive   = true
  default     = null
}

# Authentication Configuration (will be auto-generated and stored in Secrets Manager)
# No hardcoded credentials needed - all generated randomly

# CI/CD Configuration
variable "circleci_ssh_private_key" {
  description = "CircleCI SSH private key for deployment"
  type        = string
  sensitive   = true
  default     = null
}

# IAM Database Authentication Configuration
variable "enable_iam_auth" {
  description = "Enable IAM database authentication (recommended for production)"
  type        = bool
  default     = true
}

variable "iam_db_username" {
  description = "IAM database username for application connections"
  type        = string
  default     = "iam_app_user"
}
