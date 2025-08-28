# ECR Module Variables

variable "repository_name" {
  description = "Name of the ECR repository"
  type        = string
  default     = "inscribe-customer-data-service"
}

variable "environment" {
  description = "Environment name (e.g., development, staging, production)"
  type        = string
}

variable "image_tag_mutability" {
  description = "The tag mutability setting for the repository. Must be one of: MUTABLE or IMMUTABLE"
  type        = string
  default     = "MUTABLE"

  validation {
    condition     = contains(["MUTABLE", "IMMUTABLE"], var.image_tag_mutability)
    error_message = "Image tag mutability must be either MUTABLE or IMMUTABLE."
  }
}

variable "scan_on_push" {
  description = "Indicates whether images are scanned after being pushed to the repository"
  type        = bool
  default     = true
}

variable "encryption_type" {
  description = "The encryption type for the repository. Must be one of: AES256 or KMS"
  type        = string
  default     = "AES256"

  validation {
    condition     = contains(["AES256", "KMS"], var.encryption_type)
    error_message = "Encryption type must be either AES256 or KMS."
  }
}

variable "kms_key_id" {
  description = "The KMS key to use when encryption_type is KMS. If not specified, uses the default AWS managed key for ECR"
  type        = string
  default     = null
}

variable "enable_cross_account_access" {
  description = "Enable cross-account access to the ECR repository"
  type        = bool
  default     = false
}

variable "cross_account_arns" {
  description = "List of AWS account ARNs that can access this ECR repository"
  type        = list(string)
  default     = []
}

variable "max_image_count" {
  description = "Maximum number of tagged images to retain"
  type        = number
  default     = 10
}

variable "untagged_image_days" {
  description = "Number of days to retain untagged images"
  type        = number
  default     = 1
}

variable "dev_image_count" {
  description = "Maximum number of development images to retain"
  type        = number
  default     = 5
}

variable "enable_enhanced_scanning" {
  description = "Enable enhanced scanning for the ECR repository"
  type        = bool
  default     = true
}

variable "scan_frequency" {
  description = "Frequency of enhanced scanning. Valid values: SCAN_ON_PUSH, CONTINUOUS_SCAN, MANUAL"
  type        = string
  default     = "SCAN_ON_PUSH"

  validation {
    condition     = contains(["SCAN_ON_PUSH", "CONTINUOUS_SCAN", "MANUAL"], var.scan_frequency)
    error_message = "Scan frequency must be one of: SCAN_ON_PUSH, CONTINUOUS_SCAN, MANUAL."
  }
}

variable "enable_scan_logging" {
  description = "Enable CloudWatch logging for ECR scan results"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "Number of days to retain ECR scan logs in CloudWatch"
  type        = number
  default     = 14
}

variable "enable_scan_notifications" {
  description = "Enable notifications for ECR scan completion"
  type        = bool
  default     = false
}

variable "notification_target_arn" {
  description = "ARN of the notification target (SNS topic, SQS queue, Lambda function, etc.)"
  type        = string
  default     = null
}

variable "notification_type" {
  description = "Type of notification target (sns, sqs, lambda)"
  type        = string
  default     = "sns"

  validation {
    condition     = contains(["sns", "sqs", "lambda"], var.notification_type)
    error_message = "Notification type must be one of: sns, sqs, lambda."
  }
}

variable "allow_scan_results_access" {
  description = "Allow IAM policy to include access to scan results"
  type        = bool
  default     = true
}
