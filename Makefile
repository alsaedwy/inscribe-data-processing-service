# Makefile for Inscribe Data Processing Service

.PHONY: help setup test build run deploy clean

# Default target
help:
	@echo "Inscribe Data Processing Service - Available Commands:"
	@echo ""
	@echo "  setup    - Set up local development environment"
	@echo "  test     - Run unit tests"
	@echo "  build    - Build Docker image"
	@echo "  run      - Run application locally"
	@echo "  deploy   - Deploy infrastructure to AWS"
	@echo "  clean    - Clean up Docker containers and images"
	@echo "  lint     - Run code linting and security checks"
	@echo ""

# Set up local development environment
setup:
	@./setup.sh

# Run unit tests
test:
	@echo "🧪 Running unit tests..."
	@docker-compose -f docker-compose.test.yml up --build --abort-on-container-exit
	@docker-compose -f docker-compose.test.yml down

# Build Docker image
build:
	@echo "🔨 Building Docker image..."
	@docker build -t inscribe/customer-data-service:latest .

# Run application locally
run:
	@echo "🚀 Starting application..."
	@docker-compose up -d
	@echo "Application running at http://localhost:8000"
	@echo "API Documentation: http://localhost:8000/docs"

# Deploy infrastructure
deploy:
	@./deploy.sh

# Clean up Docker containers and images
clean:
	@echo "🧹 Cleaning up Docker resources..."
	@docker-compose down -v
	@docker system prune -f
	@docker volume prune -f

# Run linting and security checks
lint:
	@echo "🔍 Running code quality checks..."
	@docker run --rm -v $(PWD)/src:/app -w /app python:3.11-slim sh -c \
		"pip install bandit safety flake8 && \
		 flake8 . --max-line-length=100 --exclude=__pycache__ && \
		 bandit -r . && \
		 echo 'Code quality checks passed!'"

# Run security scan on Docker image
security-scan: build
	@echo "🔒 Running security scan on Docker image..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy:latest image inscribe/customer-data-service:latest

# Show logs
logs:
	@docker-compose logs -f

# Show application status
status:
	@docker-compose ps
	@echo ""
	@./scripts/secure_api_test.sh http://localhost:8000 || echo "Application not responding"
