#!/bin/bash

# Terraform deployment script for Inscribe Data Processing Service

set -e

echo "🏗️  Deploying Inscribe Data Processing Service Infrastructure..."

# Check if AWS CLI is configured
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS CLI is not configured or credentials are invalid."
    echo "Please run 'aws configure' first."
    exit 1
fi

# Check if Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform is not installed. Please install Terraform first."
    exit 1
fi

# Change to terraform directory
cd terraform

# Initialize Terraform
echo "🔧 Initializing Terraform..."
terraform init

# Validate configuration
echo "✅ Validating Terraform configuration..."
terraform validate

# Plan deployment
echo "📋 Creating deployment plan..."
terraform plan -out=tfplan

# Ask for confirmation
read -p "Do you want to apply this plan? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Applying Terraform configuration..."
    terraform apply tfplan
    
    echo ""
    echo "Infrastructure deployment complete!"
    echo ""
    echo "Outputs:"
    terraform output
    
    # Get the EC2 public IP
    EC2_IP=$(terraform output -raw ec2_public_ip 2>/dev/null || echo "")
    
    echo ""
    echo "Next steps:"
    echo "1. Wait 5-10 minutes for complete application deployment"
    echo "2. Monitor deployment progress:"
    echo "   ssh ec2-user@$EC2_IP 'sudo tail -f /var/log/user-data.log'"
    echo ""
    echo "3. Test the deployed application:"
    echo "   cd /Users/alaa/Documents/code/inscribe-data-processing-service"
    echo "   ./scripts/secure_api_test.sh http://$EC2_IP:8000"
    echo ""
    echo "4. Access the application:"
    echo "   Application URL: http://$EC2_IP:8000"
    echo "   API Documentation: http://$EC2_IP:8000/docs"
    echo ""
    echo "Management commands (on EC2 instance):"
    echo "   sudo systemctl status inscribe-app    # Check service status"
    echo "   /opt/inscribe-app/manage.sh logs      # View application logs"
    echo "   /opt/inscribe-app/manage.sh health    # Check application health"
else
    echo "Deployment cancelled."
    rm -f tfplan
fi
