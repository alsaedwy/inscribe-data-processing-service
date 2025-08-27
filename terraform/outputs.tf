# Outputs for Terraform configuration
output "ec2_public_ip" {
  description = "Public IP address of the EC2 instance"
  value       = module.ec2.public_ip
}

output "ec2_instance_id" {
  description = "Instance ID of the EC2 instance"
  value       = module.ec2.instance_id
}

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.db_endpoint
  sensitive   = true
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.db_port
}

output "application_url" {
  description = "URL to access the microservice"
  value       = "http://${module.ec2.public_ip}:8000"
}

# Secret names for application configuration
output "application_secrets_name" {
  description = "Name of the application secrets in AWS Secrets Manager"
  value       = module.secrets.application_secrets_secret_name
}

output "rds_credentials_secret_name" {
  description = "Name of the RDS credentials secret in AWS Secrets Manager"
  value       = module.rds.rds_credentials_secret_name
}

output "datadog_api_key_secret_name" {
  description = "Name of the Datadog API key secret in AWS Secrets Manager"
  value       = module.secrets.datadog_api_key_secret_name
}

output "datadog_app_key_secret_name" {
  description = "Name of the Datadog application key secret in AWS Secrets Manager"
  value       = module.secrets.datadog_app_key_secret_name
}

# SSM Access Information
output "ssm_connect_command" {
  description = "AWS SSM Session Manager command to connect to EC2 instance"
  value       = var.enable_ssm_access ? "aws ssm start-session --target ${module.ec2.instance_id}" : "SSM access not enabled"
}

output "access_methods" {
  description = "Available methods to access the EC2 instance"
  value = {
    ssm_available = var.enable_ssm_access
    public_ip     = module.ec2.public_ip
    instance_id   = module.ec2.instance_id
  }
}
