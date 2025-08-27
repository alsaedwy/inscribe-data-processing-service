# ECR Module Outputs

output "repository_url" {
  description = "The URL of the repository (in the form aws_account_id.dkr.ecr.region.amazonaws.com/repositoryName)"
  value       = aws_ecr_repository.inscribe_customer_data_service.repository_url
}

output "repository_arn" {
  description = "Full ARN of the repository"
  value       = aws_ecr_repository.inscribe_customer_data_service.arn
}

output "repository_name" {
  description = "Name of the repository"
  value       = aws_ecr_repository.inscribe_customer_data_service.name
}

output "registry_id" {
  description = "The registry ID where the repository was created"
  value       = aws_ecr_repository.inscribe_customer_data_service.registry_id
}

output "ecr_access_policy_arn" {
  description = "ARN of the IAM policy for ECR access"
  value       = aws_iam_policy.ecr_access_policy.arn
}

output "ecr_access_policy_name" {
  description = "Name of the IAM policy for ECR access"
  value       = aws_iam_policy.ecr_access_policy.name
}

output "lifecycle_policy_text" {
  description = "The text of the lifecycle policy"
  value       = aws_ecr_lifecycle_policy.inscribe_customer_data_service_lifecycle.policy
}

output "scan_configuration" {
  description = "ECR repository scanning configuration"
  value = {
    scan_on_push         = var.scan_on_push
    enhanced_scanning    = var.enable_enhanced_scanning
    scan_frequency       = var.scan_frequency
  }
}

output "cloudwatch_log_group_name" {
  description = "Name of the CloudWatch log group for ECR scan results"
  value       = var.enable_scan_logging ? aws_cloudwatch_log_group.ecr_scan_results[0].name : null
}

output "cloudwatch_log_group_arn" {
  description = "ARN of the CloudWatch log group for ECR scan results"
  value       = var.enable_scan_logging ? aws_cloudwatch_log_group.ecr_scan_results[0].arn : null
}

output "scan_event_rule_name" {
  description = "Name of the EventBridge rule for ECR scan completion"
  value       = var.enable_scan_notifications ? aws_cloudwatch_event_rule.ecr_scan_complete[0].name : null
}

output "scan_event_rule_arn" {
  description = "ARN of the EventBridge rule for ECR scan completion"
  value       = var.enable_scan_notifications ? aws_cloudwatch_event_rule.ecr_scan_complete[0].arn : null
}
