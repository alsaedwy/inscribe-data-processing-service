# IAM Role for EC2 with minimal required permissions

# IAM role for EC2 instance
resource "aws_iam_role" "ec2_role" {
  count = var.enable_ssm_access ? 1 : 0
  name  = "${var.environment}-inscribe-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "${var.environment}-inscribe-ec2-role"
  }
}

# Attach AWS managed policy for SSM
resource "aws_iam_role_policy_attachment" "ssm_managed_instance_core" {
  count      = var.enable_ssm_access ? 1 : 0
  role       = aws_iam_role.ec2_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

# Attach AWS managed policy for CloudWatch (for SSM Session Manager logging)
resource "aws_iam_role_policy_attachment" "cloudwatch_agent_server_policy" {
  count      = var.enable_ssm_access ? 1 : 0
  role       = aws_iam_role.ec2_role[0].name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

# Custom policy for Secrets Manager access
resource "aws_iam_policy" "secrets_manager_policy" {
  count       = var.enable_ssm_access ? 1 : 0
  name        = "${var.environment}-inscribe-secrets-manager-policy"
  description = "Policy for accessing Secrets Manager secrets"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = var.secret_arns
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "secrets_manager_policy" {
  count      = var.enable_ssm_access ? 1 : 0
  role       = aws_iam_role.ec2_role[0].name
  policy_arn = aws_iam_policy.secrets_manager_policy[0].arn
}

# Custom policy for RDS connection (minimal permissions)
resource "aws_iam_policy" "rds_connect_policy" {
  count       = var.enable_ssm_access && var.enable_rds_iam_auth ? 1 : 0
  name        = "${var.environment}-inscribe-rds-connect-policy"
  description = "Minimal policy for RDS connection using IAM authentication"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds-db:connect"
        ]
        Resource = [
          "arn:aws:rds-db:${var.aws_region}:${var.aws_account_id}:dbuser:${var.db_instance_identifier}/${var.db_username}"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_connect_policy" {
  count      = var.enable_ssm_access && var.enable_rds_iam_auth ? 1 : 0
  role       = aws_iam_role.ec2_role[0].name
  policy_arn = aws_iam_policy.rds_connect_policy[0].arn
}

# Custom policy for CloudWatch logs
resource "aws_iam_policy" "cloudwatch_logs_policy" {
  count       = var.enable_ssm_access ? 1 : 0
  name        = "${var.environment}-inscribe-cloudwatch-logs-policy"
  description = "Policy for writing CloudWatch logs"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents",
          "logs:DescribeLogGroups",
          "logs:DescribeLogStreams"
        ]
        Resource = [
          "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/aws/inscribe/*",
          "arn:aws:logs:${var.aws_region}:${var.aws_account_id}:log-group:/aws/inscribe/*:*"
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "cloudwatch_logs_policy" {
  count      = var.enable_ssm_access ? 1 : 0
  role       = aws_iam_role.ec2_role[0].name
  policy_arn = aws_iam_policy.cloudwatch_logs_policy[0].arn
}

# Custom policy for EC2 metadata access (required for some operations)
resource "aws_iam_policy" "ec2_metadata_policy" {
  count       = var.enable_ssm_access ? 1 : 0
  name        = "${var.environment}-inscribe-ec2-metadata-policy"
  description = "Policy for accessing EC2 instance metadata"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ec2:DescribeInstances",
          "ec2:DescribeTags"
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "ec2:Region" = var.aws_region
          }
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ec2_metadata_policy" {
  count      = var.enable_ssm_access ? 1 : 0
  role       = aws_iam_role.ec2_role[0].name
  policy_arn = aws_iam_policy.ec2_metadata_policy[0].arn
}

# Instance profile for EC2
resource "aws_iam_instance_profile" "ec2_profile" {
  count = var.enable_ssm_access ? 1 : 0
  name  = "${var.environment}-inscribe-ec2-profile"
  role  = aws_iam_role.ec2_role[0].name

  tags = {
    Name = "${var.environment}-inscribe-ec2-profile"
  }
}
