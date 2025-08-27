#!/bin/bash
set -e

echo "Starting deployment..."

# Get environment variables passed from CircleCI
CIRCLE_SHA1="${CIRCLE_SHA1}"
DB_HOST="${DB_HOST}"
DB_NAME="${DB_NAME}"
DB_USER="${DB_USER}"
DB_PASSWORD="${DB_PASSWORD}"
DATADOG_API_KEY="${DATADOG_API_KEY}"
DATADOG_APP_KEY="${DATADOG_APP_KEY}"

# Update system
sudo yum update -y

# Install Docker if not present
if ! command -v docker &> /dev/null; then
    sudo yum install -y docker
    sudo systemctl start docker
    sudo systemctl enable docker
    sudo usermod -a -G docker ssm-user
fi

# Pull latest image
echo "Pulling Docker image: inscribe/customer-data-service:${CIRCLE_SHA1}"
sudo docker pull inscribe/customer-data-service:${CIRCLE_SHA1}

# Stop existing container if running
sudo docker stop inscribe-app || true
sudo docker rm inscribe-app || true

# Start new container
echo "Starting new container..."
sudo docker run -d --name inscribe-app \
  --restart unless-stopped \
  -p 8000:8000 \
  -e DB_HOST="${DB_HOST}" \
  -e DB_NAME="${DB_NAME}" \
  -e DB_USER="${DB_USER}" \
  -e DB_PASSWORD="${DB_PASSWORD}" \
  -e DATADOG_API_KEY="${DATADOG_API_KEY}" \
  -e DATADOG_APP_KEY="${DATADOG_APP_KEY}" \
  -e ENVIRONMENT=development \
  inscribe/customer-data-service:${CIRCLE_SHA1}

# Wait for application to start
echo "Waiting for application to start..."
sleep 30

# Health check
echo "Running health check..."
for i in {1..10}; do
  if curl -f http://localhost:8000/health; then
    echo "Health check passed!"
    break
  else
    echo "Health check failed, retrying in 10 seconds..."
    sleep 10
  fi
  
  if [ $i -eq 10 ]; then
    echo "Health check failed after 10 attempts"
    sudo docker logs inscribe-app
    exit 1
  fi
done

echo "Deployment completed successfully!"
