# Security Groups for EC2 and RDS instances
resource "aws_security_group" "ec2_sg" {
  name_prefix = "${var.environment}-inscribe-ec2-"
  description = "Security group for EC2 instance hosting the microservice"
  vpc_id      = var.vpc_id

  # HTTP access for the microservice
  ingress {
    description = "HTTP"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  # HTTPS access
  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_cidr_blocks
  }

  # All outbound traffic
  egress {
    description = "All outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.environment}-inscribe-ec2-sg"
  }
}

resource "aws_security_group" "rds_sg" {
  name_prefix = "${var.environment}-inscribe-rds-"
  description = "Security group for RDS instance"
  vpc_id      = var.vpc_id

  # MySQL/Aurora access from EC2 security group only
  ingress {
    description     = "MySQL/Aurora"
    from_port       = 3306
    to_port         = 3306
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2_sg.id]
  }

  # No outbound rules needed for RDS
  tags = {
    Name = "${var.environment}-inscribe-rds-sg"
  }
}
