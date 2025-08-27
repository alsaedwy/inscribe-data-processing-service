# ECR Integration and Vulnerability Scanning Guide

This guide explains the ECR (Elastic Container Registry) integration that replaces Docker Hub and provides comprehensive vulnerability scanning capabilities.

## Overview

The project now uses Amazon ECR instead of Docker Hub for container image storage, providing:

- **Enhanced Security**: Images are stored in AWS with encryption at rest
- **Vulnerability Scanning**: Automatic scanning on push with detailed reports
- **Enhanced Scanning**: Continuous vulnerability detection with Inspector
- **Lifecycle Management**: Automatic cleanup of old images
- **Access Control**: Fine-grained IAM permissions
- **Cost Optimization**: Pay only for storage used, no registry fees

## ECR Module Features

### 🔒 Security Features

1. **Image Scanning**: 
   - Basic scanning on push (free)
   - Enhanced scanning with Amazon Inspector (additional cost)
   - Continuous vulnerability monitoring

2. **Encryption**:
   - AES256 encryption by default
   - Optional KMS encryption for enhanced security

3. **Access Control**:
   - IAM-based access control
   - Repository policies for cross-account access
   - Least privilege permissions for EC2 instances

### 📊 Vulnerability Scanning

#### Basic Scanning (Free)
- Scans for known vulnerabilities in OS packages
- Results available immediately after push
- CVE database updated regularly

#### Enhanced Scanning (Additional Cost)
- Powered by Amazon Inspector
- Scans application dependencies
- Continuous monitoring for new vulnerabilities
- More comprehensive vulnerability database

### 🧹 Lifecycle Management

The ECR module includes automatic lifecycle policies:

1. **Production Images**: Keep last 10 tagged images (v*, release*)
2. **Development Images**: Keep last 5 development images (dev*, feature*, main*)
3. **Untagged Images**: Delete after 1 day

### 📈 Monitoring and Alerting

- **CloudWatch Logs**: Scan results logging
- **EventBridge Rules**: Notifications on scan completion
- **Custom Metrics**: Track vulnerability counts over time

## Terraform Configuration

### ECR Module Structure
```
terraform/modules/ecr/
├── main.tf          # ECR repository and scanning configuration
├── variables.tf     # Input variables with defaults
└── outputs.tf       # Repository URL, ARN, and scan configuration
```

### Key Variables

```hcl
# Repository Configuration
ecr_repository_name = "inscribe/customer-data-service"
ecr_image_tag_mutability = "MUTABLE"

# Security Configuration
ecr_scan_on_push = true
ecr_enable_enhanced_scanning = true
ecr_scan_frequency = "SCAN_ON_PUSH"

# Lifecycle Configuration
ecr_max_image_count = 10
ecr_dev_image_count = 5
ecr_untagged_image_days = 1
```

## CircleCI Integration Changes

### Environment Variables (Updated)

Remove Docker Hub variables and ensure these AWS variables are set:

```bash
# AWS Credentials (required for ECR)
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_DEFAULT_REGION=<your-aws-region>

# Remove these Docker Hub variables
# DOCKERHUB_USERNAME (no longer needed)
# DOCKERHUB_PASSWORD (no longer needed)
```

### Pipeline Changes

1. **Infrastructure First**: ECR repository must be created before building images
2. **ECR Login**: Uses AWS CLI to authenticate with ECR
3. **Image Scanning**: Both Trivy and ECR scanning for comprehensive coverage
4. **Deployment**: EC2 instances authenticate with ECR using IAM roles

### Build Process

```yaml
# Old (Docker Hub)
docker build -t inscribe/customer-data-service:${CIRCLE_SHA1} .
docker push inscribe/customer-data-service:${CIRCLE_SHA1}

# New (ECR)
ECR_REPOSITORY_URL=$(terraform output -raw ecr_repository_url)
docker build -t ${ECR_REPOSITORY_URL}:${CIRCLE_SHA1} .
aws ecr get-login-password | docker login --username AWS --password-stdin
docker push ${ECR_REPOSITORY_URL}:${CIRCLE_SHA1}
```

## Security Scanning Workflow

### 1. Build-Time Scanning
- **Trivy**: Local vulnerability scanning during build
- **ECR Basic Scan**: Triggered automatically on image push
- **ECR Enhanced Scan**: Continuous monitoring after push

### 2. Scan Results
- **Trivy Results**: Stored as CircleCI artifacts
- **ECR Results**: Available in AWS Console and via CLI
- **Continuous Monitoring**: Ongoing vulnerability detection

### 3. Scan Artifacts
```
security/
├── trivy-report.json          # Trivy scan results
└── ecr-scan-results.json      # ECR scan findings
```

## Deployment Changes

### EC2 IAM Permissions
The EC2 instance now has ECR access permissions:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["ecr:GetAuthorizationToken"],
      "Resource": "*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "ecr:BatchCheckLayerAvailability",
        "ecr:GetDownloadUrlForLayer",
        "ecr:BatchGetImage"
      ],
      "Resource": "arn:aws:ecr:region:account:repository/inscribe/customer-data-service"
    }
  ]
}
```

### Deployment Script Updates
- **ECR Authentication**: EC2 instances authenticate with ECR using IAM
- **Image URLs**: Updated to use ECR repository URLs
- **AWS CLI**: Installed on EC2 for ECR authentication

## Cost Considerations

### ECR Pricing
- **Storage**: $0.10 per GB per month
- **Data Transfer**: Standard AWS data transfer rates
- **Enhanced Scanning**: $0.09 per image scan

### Cost Optimization
- **Lifecycle Policies**: Automatic cleanup of old images
- **Regional Storage**: Images stored in same region as deployment
- **Compression**: Docker layer deduplication reduces storage

### Comparison with Docker Hub
- **No Registry Fees**: Unlike Docker Hub's per-repository pricing
- **Pay-as-you-go**: Only pay for storage actually used
- **Enhanced Features**: Vulnerability scanning included

## Migration Checklist

### ✅ Pre-Migration
1. Update CircleCI environment variables
2. Remove Docker Hub context from workflows
3. Ensure AWS credentials have ECR permissions

### ✅ During Migration
1. Deploy Terraform changes to create ECR repository
2. Update CircleCI configuration
3. Trigger first build to test ECR integration

### ✅ Post-Migration
1. Verify image scanning results
2. Monitor ECR costs in AWS Cost Explorer
3. Configure scan result notifications (optional)

## Troubleshooting

### Common Issues

1. **ECR Login Failures**
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Manual ECR login test
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account>.dkr.ecr.us-east-1.amazonaws.com
   ```

2. **Image Push Failures**
   ```bash
   # Verify repository exists
   aws ecr describe-repositories --repository-names inscribe/customer-data-service
   
   # Check image tags
   aws ecr list-images --repository-name inscribe/customer-data-service
   ```

3. **Scan Results Not Available**
   ```bash
   # Check scan status
   aws ecr describe-image-scan-findings --repository-name inscribe/customer-data-service --image-id imageTag=latest
   ```

### Monitoring Commands

```bash
# View scan results
aws ecr describe-image-scan-findings \
  --repository-name inscribe/customer-data-service \
  --image-id imageTag=latest

# List images with scan status
aws ecr describe-images \
  --repository-name inscribe/customer-data-service \
  --query 'imageDetails[*].[imageTags[0],imageScanFindingsSummary.findingCounts]'

# View repository policy
aws ecr get-repository-policy \
  --repository-name inscribe/customer-data-service
```

## Benefits Summary

### 🔒 Security Improvements
- Vulnerability scanning on every image push
- Enhanced scanning with continuous monitoring
- Encrypted storage with AWS security standards
- IAM-based access control

### 💰 Cost Benefits
- No Docker Hub subscription fees
- Pay only for storage used
- Automatic image cleanup reduces costs
- Regional deployment reduces data transfer costs

### 🚀 Operational Benefits
- Integrated with AWS ecosystem
- Automated vulnerability scanning
- CloudWatch integration for monitoring
- EventBridge integration for notifications

### 📊 Compliance Benefits
- Audit trail of all image activities
- Vulnerability scan history
- Compliance reporting capabilities
- Security posture monitoring

This ECR integration provides enterprise-grade container image management with comprehensive vulnerability scanning while optimizing costs and enhancing security posture.
