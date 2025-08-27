output "instance_profile_name" {
  description = "Name of the EC2 instance profile"
  value       = var.enable_ssm_access ? aws_iam_instance_profile.ec2_profile[0].name : null
}

output "role_arn" {
  description = "ARN of the EC2 IAM role"
  value       = var.enable_ssm_access ? aws_iam_role.ec2_role[0].arn : null
}

output "role_name" {
  description = "Name of the EC2 IAM role"
  value       = var.enable_ssm_access ? aws_iam_role.ec2_role[0].name : null
}
