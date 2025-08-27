variable "vpc_id" {
  description = "VPC ID for security groups"
  type        = string
}

variable "environment" {
  description = "Environment name"
  type        = string
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access the services"
  type        = list(string)
}
