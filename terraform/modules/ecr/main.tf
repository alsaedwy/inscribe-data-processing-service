# ECR Repository Module for Inscribe Customer Data Service

resource "aws_ecr_repository" "inscribe_customer_data_service" {
  name                 = var.repository_name
  image_tag_mutability = var.image_tag_mutability

  image_scanning_configuration {
    scan_on_push = var.scan_on_push
  }

  encryption_configuration {
    encryption_type = var.encryption_type
    kms_key         = var.kms_key_id
  }

  tags = {
    Name        = var.repository_name
    Environment = var.environment
    Project     = "inscribe-data-processing-service"
    ManagedBy   = "terraform"
  }
}

# ECR Repository Policy for allowing cross-account access if needed
resource "aws_ecr_repository_policy" "inscribe_customer_data_service_policy" {
  count      = var.enable_cross_account_access ? 1 : 0
  repository = aws_ecr_repository.inscribe_customer_data_service.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowCrossAccountAccess"
        Effect = "Allow"
        Principal = {
          AWS = var.cross_account_arns
        }
        Action = [
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:BatchCheckLayerAvailability"
        ]
      }
    ]
  })
}

# ECR Lifecycle Policy to manage image retention
resource "aws_ecr_lifecycle_policy" "inscribe_customer_data_service_lifecycle" {
  repository = aws_ecr_repository.inscribe_customer_data_service.name

  policy = jsonencode({
    rules = [
      {
        rulePriority = 1
        description  = "Keep last ${var.max_image_count} images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["v", "release"]
          countType     = "imageCountMoreThan"
          countNumber   = var.max_image_count
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 2
        description  = "Delete untagged images older than ${var.untagged_image_days} days"
        selection = {
          tagStatus   = "untagged"
          countType   = "sinceImagePushed"
          countUnit   = "days"
          countNumber = var.untagged_image_days
        }
        action = {
          type = "expire"
        }
      },
      {
        rulePriority = 3
        description  = "Keep only last ${var.dev_image_count} development images"
        selection = {
          tagStatus     = "tagged"
          tagPrefixList = ["dev", "feature", "main"]
          countType     = "imageCountMoreThan"
          countNumber   = var.dev_image_count
        }
        action = {
          type = "expire"
        }
      }
    ]
  })
}

# ECR Repository Scanner Configuration for Enhanced Scanning
resource "aws_ecr_registry_scanning_configuration" "inscribe_scanning" {
  count       = var.enable_enhanced_scanning ? 1 : 0
  scan_type   = "ENHANCED"

  rule {
    scan_frequency = var.scan_frequency
    repository_filter {
      filter      = var.repository_name
      filter_type = "WILDCARD"
    }
  }
}

# CloudWatch Log Group for ECR scanning results
resource "aws_cloudwatch_log_group" "ecr_scan_results" {
  count             = var.enable_scan_logging ? 1 : 0
  name              = "/aws/ecr/scan-results/${var.repository_name}"
  retention_in_days = var.log_retention_days

  tags = {
    Name        = "ecr-scan-results-${var.repository_name}"
    Environment = var.environment
    Project     = "inscribe-data-processing-service"
    ManagedBy   = "terraform"
  }
}

# EventBridge Rule for ECR scan completion notifications
resource "aws_cloudwatch_event_rule" "ecr_scan_complete" {
  count       = var.enable_scan_notifications ? 1 : 0
  name        = "ecr-scan-complete-${var.repository_name}"
  description = "Capture ECR scan completion events for ${var.repository_name}"

  event_pattern = jsonencode({
    source        = ["aws.ecr"]
    detail-type   = ["ECR Image Scan"]
    detail = {
      repository-name = [var.repository_name]
      scan-status     = ["COMPLETE"]
    }
  })

  tags = {
    Name        = "ecr-scan-complete-${var.repository_name}"
    Environment = var.environment
    Project     = "inscribe-data-processing-service"
    ManagedBy   = "terraform"
  }
}

# EventBridge Target for scan notifications (can be SNS, SQS, Lambda, etc.)
resource "aws_cloudwatch_event_target" "ecr_scan_complete_target" {
  count     = var.enable_scan_notifications && var.notification_target_arn != null ? 1 : 0
  rule      = aws_cloudwatch_event_rule.ecr_scan_complete[0].name
  target_id = "ECRScanCompleteTarget"
  arn       = var.notification_target_arn

  # If the target is SNS, we need to format the input
  dynamic "input_transformer" {
    for_each = var.notification_type == "sns" ? [1] : []
    content {
      input_paths = {
        repository = "$.detail.repository-name"
        tag        = "$.detail.image-tags[0]"
        status     = "$.detail.scan-status"
        findings   = "$.detail.finding-counts"
      }
      input_template = jsonencode({
        "repository" : "<repository>",
        "tag" : "<tag>",
        "scan_status" : "<status>",
        "vulnerability_counts" : "<findings>",
        "message" : "ECR scan completed for repository <repository> with tag <tag>. Status: <status>. Findings: <findings>"
      })
    }
  }
}

# IAM Policy for ECR access (to be attached to EC2 instance role)
data "aws_iam_policy_document" "ecr_access_policy" {
  statement {
    effect = "Allow"
    actions = [
      "ecr:GetAuthorizationToken"
    ]
    resources = ["*"]
  }

  statement {
    effect = "Allow"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage"
    ]
    resources = [aws_ecr_repository.inscribe_customer_data_service.arn]
  }

  # Optional: Allow image scanning results access
  dynamic "statement" {
    for_each = var.allow_scan_results_access ? [1] : []
    content {
      effect = "Allow"
      actions = [
        "ecr:DescribeImageScanFindings",
        "ecr:DescribeImages"
      ]
      resources = [aws_ecr_repository.inscribe_customer_data_service.arn]
    }
  }
}

resource "aws_iam_policy" "ecr_access_policy" {
  name_prefix = "ecr-access-"
  description = "IAM policy for ECR access to ${var.repository_name}"
  policy      = data.aws_iam_policy_document.ecr_access_policy.json

  tags = {
    Name        = "ecr-access-${var.repository_name}"
    Environment = var.environment
    Project     = "inscribe-data-processing-service"
    ManagedBy   = "terraform"
  }
}
