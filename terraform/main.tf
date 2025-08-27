# Main Terraform configuration for Inscribe Data Processing Service
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "inscribe-data-processing-service"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# Data sources for existing resources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

data "aws_caller_identity" "current" {}

# Secrets Manager Module
module "secrets" {
  source = "./modules/secrets"

  environment             = var.environment
  datadog_api_key         = var.datadog_api_key
  datadog_app_key         = var.datadog_app_key
  circleci_ssh_private_key = var.circleci_ssh_private_key
}

# ECR Repository Module
module "ecr" {
  source = "./modules/ecr"

  repository_name           = var.ecr_repository_name
  environment              = var.environment
  image_tag_mutability     = var.ecr_image_tag_mutability
  scan_on_push             = var.ecr_scan_on_push
  encryption_type          = var.ecr_encryption_type
  kms_key_id               = var.ecr_kms_key_id
  enable_enhanced_scanning = var.ecr_enable_enhanced_scanning
  scan_frequency           = var.ecr_scan_frequency
  enable_scan_logging      = var.ecr_enable_scan_logging
  log_retention_days       = var.ecr_log_retention_days
  max_image_count          = var.ecr_max_image_count
  untagged_image_days      = var.ecr_untagged_image_days
  dev_image_count          = var.ecr_dev_image_count
}

# Security Groups Module
module "security_groups" {
  source = "./modules/security"

  vpc_id      = data.aws_vpc.default.id
  environment = var.environment

  allowed_cidr_blocks = var.allowed_cidr_blocks
}

# IAM Module (for SSM access and secrets management)
module "iam" {
  source = "./modules/iam"

  environment              = var.environment
  enable_ssm_access        = var.enable_ssm_access
  enable_rds_iam_auth      = var.enable_rds_iam_auth
  secret_arns              = concat(
    module.secrets.secret_arns,
    [module.rds.rds_credentials_secret_arn]
  )
  aws_region               = var.aws_region
  aws_account_id           = data.aws_caller_identity.current.account_id
  db_instance_identifier   = module.rds.db_instance_identifier
  db_username              = var.db_username
  ecr_repository_arn       = module.ecr.repository_arn
}

# RDS Module
module "rds" {
  source = "./modules/rds"

  environment          = var.environment
  db_instance_class    = var.db_instance_class
  db_allocated_storage = var.db_allocated_storage
  db_name              = var.db_name
  db_username          = var.db_username
  enable_iam_auth      = var.enable_iam_auth
  iam_db_username      = var.iam_db_username

  vpc_id            = data.aws_vpc.default.id
  subnet_ids        = data.aws_subnets.default.ids
  security_group_id = module.security_groups.rds_security_group_id

  backup_retention_period = var.backup_retention_period
  backup_window           = var.backup_window
  maintenance_window      = var.maintenance_window
}

# EC2 Module
module "ec2" {
  source = "./modules/ec2"

  environment       = var.environment
  instance_type     = var.instance_type
  subnet_id         = data.aws_subnets.default.ids[0]
  security_group_id = module.security_groups.ec2_security_group_id

  # IAM instance profile for SSM access and secrets
  iam_instance_profile = var.enable_ssm_access ? module.iam.instance_profile_name : null

  # Pass RDS connection details (will be retrieved from secrets manager in production)
  db_endpoint = module.rds.db_endpoint
  db_name     = var.db_name
  db_username = var.db_username
  db_password = "will-be-retrieved-from-secrets"  # Placeholder, actual password retrieved from secrets

  # Pass secret names for application configuration
  application_secrets_name = module.secrets.application_secrets_secret_name
  rds_credentials_secret_name = module.rds.rds_credentials_secret_name
  datadog_api_key_secret_name = module.secrets.datadog_api_key_secret_name
  datadog_app_key_secret_name = module.secrets.datadog_app_key_secret_name

  # Ensure RDS is fully available before creating EC2
  depends_on = [module.rds]
}
