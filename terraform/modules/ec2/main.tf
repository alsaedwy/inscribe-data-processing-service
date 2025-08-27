# Get the latest Amazon Linux 2 AMI
data "aws_ami" "amazon_linux" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["amzn2-ami-hvm-*-x86_64-gp2"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

# User data script to set up the EC2 instance with complete application deployment
locals {
  user_data = base64encode(<<-EOT
#!/bin/bash

# Comprehensive logging
exec > >(tee /var/log/user-data.log|logger -t user-data -s 2>/dev/console) 2>&1

echo "🚀 Starting Inscribe Customer Data Service deployment at $(date)"

# Update system packages
echo "📦 Updating system packages..."
yum update -y

# Install essential packages
echo "🛠️  Installing essential packages..."
yum install -y docker git curl wget

# Install and configure AWS SSM Agent
echo "📡 Installing AWS Systems Manager Agent..."
yum install -y amazon-ssm-agent
systemctl enable amazon-ssm-agent
systemctl start amazon-ssm-agent

# Configure Docker
echo "🐳 Configuring Docker..."
systemctl start docker
systemctl enable docker
usermod -a -G docker ec2-user

# Install Docker Compose
echo "🔧 Installing Docker Compose..."
curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
chmod +x /usr/local/bin/docker-compose

# Create application directory
echo "📁 Setting up application directory..."
mkdir -p /opt/inscribe-app
cd /opt/inscribe-app

# Clone the application repository
echo "⬇️  Cloning application repository..."
git clone https://github.com/alsaedwy/inscribe-data-processing-service.git .

# Create production environment file
echo "⚙️  Creating production environment..."

# Install jq if not present
if ! command -v jq &> /dev/null; then
    echo "📦 Installing jq..."
    yum install -y jq
fi

# Retrieve database password from Secrets Manager with error handling
echo "🔐 Retrieving database credentials from Secrets Manager..."
for i in {1..5}; do
    DB_PASSWORD=$(aws secretsmanager get-secret-value --secret-id "${var.rds_credentials_secret_name}" --region eu-west-1 --query SecretString --output text 2>/dev/null | jq -r '.password' 2>/dev/null)
    if [ ! -z "$DB_PASSWORD" ] && [ "$DB_PASSWORD" != "null" ]; then
        echo "✅ Successfully retrieved database password"
        break
    else
        echo "⚠️  Attempt $i: Failed to retrieve database password, retrying in 10 seconds..."
        sleep 10
    fi
done

if [ -z "$DB_PASSWORD" ] || [ "$DB_PASSWORD" = "null" ]; then
    echo "❌ Failed to retrieve database password from Secrets Manager"
    echo "🔄 Using placeholder - application will retrieve at runtime"
    DB_PASSWORD="RETRIEVE_FROM_SECRETS_MANAGER"
fi

cat > .env << ENV_EOF
DB_HOST=${var.db_endpoint}
DB_NAME=${var.db_name}
DB_USER=${var.db_username}
DB_PASSWORD=$DB_PASSWORD
DB_PORT=3306
ENVIRONMENT=development
API_CREDENTIALS_SECRET_NAME=${var.application_secrets_name}
RDS_CREDENTIALS_SECRET_NAME=${var.rds_credentials_secret_name}
DATADOG_API_KEY_SECRET_NAME=${var.datadog_api_key_secret_name}
DATADOG_APP_KEY_SECRET_NAME=${var.datadog_app_key_secret_name}
USE_SECRETS_MANAGER=true
ENV_EOF

# Create production Docker Compose file
echo "🐳 Creating production Docker Compose configuration..."
cat > docker-compose.prod.yml << 'COMPOSE_EOF'
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 120s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

COMPOSE_EOF

# Set proper ownership
chown -R ec2-user:ec2-user /opt/inscribe-app

# Wait for Docker to be fully ready
echo "⏳ Waiting for Docker to be ready..."
sleep 10

# Build the application
echo "🏗️  Building application..."
su - ec2-user -c "cd /opt/inscribe-app && docker-compose -f docker-compose.prod.yml build"

# Start the application
echo "🚀 Starting application..."
su - ec2-user -c "cd /opt/inscribe-app && docker-compose -f docker-compose.prod.yml up -d"

# Wait for application to start
echo "⏳ Waiting for application to start..."
sleep 60

# Test the application
echo "🧪 Testing application health..."
for i in {1..10}; do
    if curl -f http://localhost:8000/health; then
        echo "✅ Application is healthy!"
        break
    else
        echo "⏳ Waiting for application... (attempt $i/10)"
        sleep 15
    fi
done

# Create management script
echo "🔧 Creating management script..."
cat > /opt/inscribe-app/manage.sh << 'MANAGE_EOF'
#!/bin/bash
cd /opt/inscribe-app

case "$1" in
    start)
        docker-compose -f docker-compose.prod.yml up -d
        ;;
    stop)
        docker-compose -f docker-compose.prod.yml down
        ;;
    restart)
        docker-compose -f docker-compose.prod.yml restart
        ;;
    logs)
        docker-compose -f docker-compose.prod.yml logs -f
        ;;
    status)
        docker-compose -f docker-compose.prod.yml ps
        ;;
    health)
        curl -f http://localhost:8000/health || echo "Health check failed"
        ;;
    rebuild)
        docker-compose -f docker-compose.prod.yml down
        docker-compose -f docker-compose.prod.yml build --no-cache
        docker-compose -f docker-compose.prod.yml up -d
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|logs|status|health|rebuild}"
        exit 1
        ;;
esac
MANAGE_EOF

chmod +x /opt/inscribe-app/manage.sh
chown ec2-user:ec2-user /opt/inscribe-app/manage.sh

# Create systemd service for auto-start
echo "🔄 Creating systemd service..."
cat > /etc/systemd/system/inscribe-app.service << 'SERVICE_EOF'
[Unit]
Description=Inscribe Customer Data Service
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/inscribe-app
ExecStart=/usr/local/bin/docker-compose -f docker-compose.prod.yml up -d
ExecStop=/usr/local/bin/docker-compose -f docker-compose.prod.yml down
User=ec2-user
Group=ec2-user

[Install]
WantedBy=multi-user.target
SERVICE_EOF

systemctl daemon-reload
systemctl enable inscribe-app.service

# Final status
echo ""
echo "🎉 Deployment completed at $(date)"
echo ""
echo "📊 Service Information:"
echo "- Application URL: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000"
echo "- Health Check: http://$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4):8000/health"
echo "- Admin Credentials: Retrieved from AWS Secrets Manager"
echo ""
echo "🛠️  Management Commands:"
echo "- Status: sudo systemctl status inscribe-app"
echo "- Logs: /opt/inscribe-app/manage.sh logs"
echo "- Health: /opt/inscribe-app/manage.sh health"
echo ""
echo "📝 Log files:"
echo "- Deployment: /var/log/user-data.log"
echo "- Application: /opt/inscribe-app (docker-compose logs)"

# Log completion
echo "User data script completed successfully at $(date)" >> /var/log/user-data.log

EOT
  )
}

# EC2 Instance
resource "aws_instance" "main" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = var.instance_type
  
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = [var.security_group_id]
  associate_public_ip_address = true
  iam_instance_profile        = var.iam_instance_profile

  user_data = local.user_data

  tags = {
    Name = "${var.environment}-inscribe-app-server"
  }
}

# Elastic IP for stable public IP
resource "aws_eip" "main" {
  instance = aws_instance.main.id
  domain   = "vpc"

  tags = {
    Name = "${var.environment}-inscribe-app-eip"
  }
}
