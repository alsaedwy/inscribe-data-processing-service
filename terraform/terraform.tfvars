# Copy this file to terraform.tfvars and fill in your values

# AWS Configuration
aws_region  = "eu-west-1"
environment = "dev"

# EC2 Configuration
instance_type = "t3.micro"

# Access Configuration
enable_ssm_access = true # Enable AWS Systems Manager Session Manager access

# Database Configuration
db_instance_class    = "db.t3.micro"
db_allocated_storage = 20
db_name              = "inscribe_db"
db_username          = "admin"

# Network Configuration (optional - will create VPC if not specified)
# vpc_id = ""
# subnet_ids = ["subnet-xxxxx", "subnet-yyyyy"]
