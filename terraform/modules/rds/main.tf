# DB Subnet Group
resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-inscribe-db-subnet-group"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.environment}-inscribe-db-subnet-group"
  }
}

# Generate random password for initial RDS setup (only used during creation)
resource "random_password" "db_password" {
  length  = 16
  special = true
}

# Generate random suffix for secret name to avoid conflicts
resource "random_string" "secret_suffix" {
  length  = 5
  special = false
  upper   = false
  lower   = false
  numeric = true
}

# Store RDS credentials in Secrets Manager
resource "aws_secretsmanager_secret" "rds_credentials" {
  name        = "${var.environment}-inscribe-rds-credentials-${random_string.secret_suffix.result}"
  description = "RDS database credentials for ${var.environment} environment"
  
  tags = {
    Name        = "${var.environment}-inscribe-rds-credentials-${random_string.secret_suffix.result}"
    Environment = var.environment
    Service     = "inscribe-customer-service"
  }
}

resource "aws_secretsmanager_secret_version" "rds_credentials" {
  secret_id = aws_secretsmanager_secret.rds_credentials.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    host     = aws_db_instance.main.address
    port     = aws_db_instance.main.port
    database = var.db_name
  })
  
  depends_on = [aws_db_instance.main]
}

# RDS Instance with IAM Authentication
resource "aws_db_instance" "main" {
  identifier = "${var.environment}-inscribe-db"

  # Engine configuration - Free tier: MySQL 8.0
  engine         = "mysql"
  engine_version = "8.0"
  instance_class = var.db_instance_class

  # Storage configuration - Free tier: 20GB General Purpose SSD
  allocated_storage     = var.db_allocated_storage
  max_allocated_storage = 0  # Disable auto-scaling for free tier
  storage_type          = "gp2"
  storage_encrypted     = false  # Encryption not available in free tier

  # Database configuration - IAM authentication enabled
  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result
  port     = 3306

  # Enable IAM database authentication
  iam_database_authentication_enabled = var.enable_iam_auth

  # Network configuration
  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [var.security_group_id]
  publicly_accessible    = false

  # Backup configuration - Free tier: 1-7 days retention
  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window

  # Deletion protection and other settings
  deletion_protection = false  # Set to true in production
  skip_final_snapshot = true   # Set to false in production
  
  # Performance insights - Not available in free tier
  performance_insights_enabled = false

  # Ignore password changes after creation (not used with IAM auth)
  lifecycle {
    ignore_changes = [password]
  }

  tags = {
    Name = "${var.environment}-inscribe-db"
  }
}

# Note: IAM database user creation is handled by the application on first startup
# This avoids requiring MySQL client on the Terraform execution environment
