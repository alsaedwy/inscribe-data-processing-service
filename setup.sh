#!/bin/bash

# Inscribe Data Processing Service - Setup Script
# This script helps set up the development environment

set -e

echo "🚀 Setting up Inscribe Data Processing Service..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "✅ Created .env file. Please review and update the values."
fi

# Build and start the services
echo "🔨 Building and starting services..."
docker-compose up -d --build

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if the application is running
echo "🔍 Checking application health..."
if ./scripts/secure_api_test.sh http://localhost:8000 > /dev/null 2>&1; then
    echo "✅ Application is running successfully!"
    echo ""
    echo "🌐 API Documentation: http://localhost:8000/docs"
    echo "🔍 Health Check: http://localhost:8000/health"
    echo "📊 API Base URL: http://localhost:8000"
    echo ""
    echo "🔐 Authentication:"
    echo "   Credentials are retrieved securely from AWS Secrets Manager"
    echo "   For testing, use: ./scripts/secure_api_test.sh http://localhost:8000"
    echo ""
    echo "📝 Example API testing:"
    echo "   ./scripts/secure_api_test.sh http://localhost:8000"
else
    echo "❌ Application is not responding. Check the logs:"
    echo "   docker-compose logs"
fi

echo ""
echo "🎉 Setup complete!"
