# CircleCI Integration Guide

This guide explains how to integrate your Inscribe Data Processing Service with CircleCI for automated CI/CD.

## Prerequisites

1. **GitHub Repository**: Your code must be in a GitHub repository
2. **CircleCI Account**: Sign up at [circleci.com](https://circleci.com)
3. **Docker Hub Account**: For container registry (optional, can use other registries)
4. **AWS Account**: For deployment to EC2

## Setup Steps

### 1. Connect Repository to CircleCI

1. Go to [CircleCI](https://circleci.com) and sign in with your GitHub account
2. Click "Set Up Project" next to your `inscribe-data-processing-service` repository
3. Choose "Fast" setup to use the existing `.circleci/config.yml` file

### 2. Configure Environment Variables

In your CircleCI project settings, add these environment variables:

#### AWS Credentials (for ECR and deployment)
```
AWS_ACCESS_KEY_ID=<your-aws-access-key>
AWS_SECRET_ACCESS_KEY=<your-aws-secret-key>
AWS_DEFAULT_REGION=<your-aws-region>
```

**Note**: Docker Hub credentials are no longer needed as we now use Amazon ECR.

#### Database Configuration
```
DB_HOST=<your-rds-endpoint>
DB_NAME=<your-database-name>
DB_USER=<your-database-username>
DB_PASSWORD=<your-database-password>
```

#### Datadog (optional, for monitoring)
```
DATADOG_API_KEY=<your-datadog-api-key>
DATADOG_APP_KEY=<your-datadog-app-key>
```

#### SSH Key (for EC2 access)
```
SSH_KEY_FINGERPRINT=<your-ssh-key-fingerprint>
```

### 3. Create Contexts (Required)

For better organization, create contexts in CircleCI:

1. **aws-deployment**: Contains AWS credentials and all deployment variables (ECR, EC2, RDS, etc.)

**Note**: The `docker-hub` context is no longer needed as we now use Amazon ECR.

### 4. Upload SSH Key

1. In CircleCI project settings, go to "SSH Keys"
2. Add your private key that corresponds to the EC2 key pair
3. Note the fingerprint and update the `SSH_KEY_FINGERPRINT` environment variable

## Pipeline Overview

The CircleCI pipeline consists of four main jobs:

### 1. Test Job
- **Python Version**: 3.13
- **Dependencies**: Installs from `requirements.txt` and `test-requirements.txt`
- **Linting**: Runs Black, isort, flake8, and mypy
- **Testing**: Runs pytest with coverage reporting
- **Security**: Runs Bandit, Safety, and pip-audit scans
- **Artifacts**: Stores test results and security reports

### 2. Infrastructure Job
- **Terraform**: Plans and applies infrastructure changes
- **Runs only on**: `main` branch
- **Dependencies**: Requires test job to pass

### 3. Build and Push Job
- **Amazon ECR**: Builds and pushes container images to AWS ECR
- **Dual Security Scanning**: Runs both Trivy and ECR vulnerability scans
- **ECR Authentication**: Uses AWS CLI for ECR login
- **Enhanced Scanning**: Triggers ECR enhanced scanning with detailed vulnerability reports
- **Runs only on**: `main` branch

### 4. Deploy Job
- **AWS SSM**: Uses custom SSM document for deployment
- **Modular Approach**: Broken into smaller steps to avoid CircleCI expression limits
- **Health Check**: Verifies deployment success
- **Runs only on**: `main` branch after build completes

## Recent Major Updates

### ECR Integration (Latest Update):

Replaced Docker Hub with Amazon ECR for enhanced security and vulnerability scanning:

1. **Container Registry Migration**: 
   - Moved from Docker Hub to Amazon ECR
   - No more Docker Hub subscription fees
   - Enhanced security with AWS encryption and IAM access control

2. **Enhanced Vulnerability Scanning**:
   - **Trivy Scanning**: Local vulnerability scanning during build
   - **ECR Basic Scanning**: Automatic scanning on image push (free)
   - **ECR Enhanced Scanning**: Continuous vulnerability monitoring with Amazon Inspector
   - **Dual Scan Reports**: Both Trivy and ECR scan results stored as artifacts

3. **Pipeline Dependencies**:
   - Infrastructure job must complete before build-and-push
   - ECR repository created by Terraform before images can be pushed
   - Enhanced error handling and scan result retrieval

4. **Cost Optimization**:
   - Pay-per-GB storage model vs fixed subscription fees
   - Automatic image lifecycle management
   - Regional storage reduces data transfer costs

### Fixed CircleCI Expression Limit Issue (Previous Update):

The deployment job was experiencing "Expressions must be less than 2048 characters" error. This was resolved by:

1. **Breaking deployment into multiple steps**:
   - Install Session Manager plugin
   - Get EC2 instance information  
   - Create/update SSM document
   - Execute deployment via SSM document
   - Wait for deployment completion
   - Check deployment results

2. **Using AWS SSM Documents**: Created a custom SSM document (`scripts/deploy-document.json`) that contains the deployment logic, eliminating the need for long inline scripts.

3. **Environment variable management**: Using `$BASH_ENV` to pass variables between steps.

### Configuration Updates Made:

1. **Python Version**: Updated from 3.11 to 3.13
2. **Package Versions**: Pinned all dependency versions for reproducibility
3. **Test Dependencies**: Updated pytest and related packages to latest versions
4. **Security Tools**: Updated Bandit, Safety, and pip-audit versions
5. **Workflow Version**: Removed deprecated `version: 2` from workflows

### Updated `test-requirements.txt`:

Added comprehensive development dependencies:
- Updated pytest ecosystem packages
- Added linting tools (Black, isort, flake8, mypy)
- Added security scanning tools
- Pinned all versions for consistency

## Deployment Architecture

The new deployment approach uses:

1. **SSM Document**: Contains the deployment script logic
2. **Parameter Passing**: Environment variables passed as SSM parameters
3. **Modular Steps**: Each deployment phase is a separate CircleCI step
4. **Error Handling**: Comprehensive error checking and logging

## Branch Strategy

- **All branches**: Run tests, linting, and security scans
- **Main branch only**: Run infrastructure, build, and deployment jobs

## Monitoring and Artifacts

The pipeline stores the following artifacts:
- Test results and coverage reports
- **Dual security scan reports**: Trivy and ECR scan results
- **ECR vulnerability reports**: Detailed findings from AWS ECR scanning
- HTML test reports

## Troubleshooting

### Common Issues:

1. **ECR Authentication Failures**: Ensure AWS credentials have ECR permissions
2. **Image Repository Not Found**: Verify Terraform has created the ECR repository
3. **Scan Results Unavailable**: ECR scans may take several minutes to complete
4. **Expression Limit Errors**: Resolved by using SSM documents instead of inline scripts
5. **AWS Permissions**: Verify IAM user has SSM, ECR, and EC2 permissions
6. **SSH Key**: Make sure the key pair exists in AWS and is uploaded to CircleCI
7. **SSM Document**: The deployment document is created/updated automatically

### Health Check Endpoints:

The application provides multiple health check endpoints:
- `/health` - Main health check (legacy)
- `/api/health` - Simple API health check
- `/api/v1/health` - Versioned health check

## Security Best Practices

1. **Environment Variables**: Use CircleCI contexts for sensitive data
2. **SSH Keys**: Rotate keys regularly
3. **Container Scanning**: Review Trivy reports for vulnerabilities
4. **Dependency Scanning**: Monitor Safety and pip-audit reports
5. **Code Security**: Review Bandit reports for security issues
6. **SSM Documents**: Use parameterized documents instead of inline scripts

## Next Steps

1. Set up the environment variables in CircleCI (remove Docker Hub variables, ensure AWS credentials are set)
2. Create the required AWS deployment context
3. Upload your SSH key
4. Deploy infrastructure first to create ECR repository
5. Push a commit to trigger the first build
6. Monitor the pipeline execution and ECR scan results

For detailed ECR configuration and vulnerability scanning information, see `ECR_INTEGRATION_GUIDE.md`.
For more detailed AWS infrastructure setup, see `DEPLOYMENT_GUIDE.md`.
