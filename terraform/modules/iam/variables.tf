variable "environment" {
  description = "Environment name for resource naming"
  type        = string
}

variable "enable_ssm_access" {
  description = "Whether to enable AWS Systems Manager Session Manager access"
  type        = bool
  default     = true
}

variable "enable_rds_iam_auth" {
  description = "Enable RDS IAM authentication"
  type        = bool
  default     = false
}

variable "secret_arns" {
  description = "List of Secrets Manager ARNs that the EC2 instance needs access to"
  type        = list(string)
  default     = []
}

variable "aws_region" {
  description = "AWS region"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account ID"
  type        = string
}

variable "db_instance_identifier" {
  description = "RDS instance identifier for IAM authentication"
  type        = string
  default     = ""
}

variable "db_username" {
  description = "Database username for IAM authentication"
  type        = string
  default     = ""
}
