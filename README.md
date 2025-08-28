# Inscribe Data Processing Service

A secure, scalable microservice architecture for customer data management, built with FastAPI, containerized with Docker, and deployed on AWS infrastructure using Terraform.

## Architecture Overview

This project demonstrates a complete microservice architecture with:

- **Infrastructure as Code**: Modular Terraform configuration for AWS resources
- **Secure Microservice**: FastAPI-based service with input validation and SQL injection prevention
- **Containerization**: Docker containers with ECR integration for consistent deployment
- **CI/CD Pipeline**: Separated CircleCI configurations for development and infrastructure
- **Code Quality**: Pre-commit hooks with automated formatting, linting, and testing
- **Observability**: Structured logging and comprehensive health monitoring

## Project Structure

```
├── .circleci/                 # CI/CD Configuration
│   ├── config.yml             # Development pipeline (tests, build)
│   └── infra-config.yml       # Infrastructure pipeline (deploy)
├── src/                       # Python Microservice
│   ├── main.py                # Application entry point
│   └── app/
│       ├── main.py            # FastAPI application
│       ├── api/v1/            # API endpoints
│       ├── core/              # Core configuration and security
│       ├── database/          # Database connection and management
│       ├── models/            # Data models
│       ├── schemas/           # Pydantic schemas
│       └── services/          # Business logic services
├── terraform/                 # Infrastructure as Code
│   ├── modules/
│   │   ├── ec2/               # EC2 instance with auto-deployment
│   │   ├── rds/               # RDS MySQL database
│   │   ├── ecr/               # ECR container registry
│   │   ├── secrets/           # AWS Secrets Manager
│   │   ├── security/          # Security groups
│   │   ├── iam/               # IAM roles and policies
│   │   └── keypair/           # SSH key management
│   ├── main.tf                # Main Terraform configuration
│   ├── variables.tf           # Input variables
│   └── outputs.tf             # Output values
├── scripts/                   # Utility Scripts
│   ├── secure_api_test.sh     # Secure API testing with AWS Secrets
│   └── setup-pre-commit.sh    # Pre-commit hooks setup
├── tests/                     # Unit Tests
│   ├── test_main.py           # Main application tests
│   ├── test_modular_app.py    # Modular application tests
│   └── conftest.py            # Test configuration
├── docs.bak/                  # Documentation Archive
├── .pre-commit-config.yaml    # Pre-commit hooks configuration
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Local development setup
├── docker-compose.test.yml    # Testing environment setup
├── requirements.txt           # Python dependencies
├── test-requirements.txt      # Testing dependencies
├── init.sql                   # Database initialization
└── deploy.sh                  # Interactive deployment script
```




## Architecture Overview

This project demonstrates a complete microservice architecture with:

- **Infrastructure as Code**: Modular Terraform configuration for AWS resources
- **Secure Microservice**: FastAPI-based service with input validation and SQL injection prevention
- **Containerization**: Docker containers for consistent deployment
- **CI/CD Pipeline**: CircleCI configuration for automated testing and deployment
- **Observability**: Structured logging and health monitoring

## Project Structure

```
├── terraform/                 # Infrastructure as Code
│   ├── modules/
│   │   ├── ec2/               # EC2 instance configuration
│   │   ├── rds/               # RDS database configuration
│   │   └── security/          # Security groups
│   ├── main.tf                # Main Terraform configuration
│   ├── variables.tf           # Input variables
│   └── outputs.tf             # Output values
├── src/                       # Python microservice
│   └── main.py                # FastAPI application
├── tests/                     # Unit tests
│   └── test_main.py           # Test suite
├── .circleci/                 # CI/CD configuration
│   └── config.yml             # CircleCI pipeline
├── Dockerfile                 # Container configuration
├── docker-compose.yml         # Local development setup
├── requirements.txt           # Python dependencies
└── init.sql                   # Database initialization
```

## Quick Start

### Prerequisites

- Docker and Docker Compose
- AWS CLI configured with appropriate permissions
- Terraform >= 1.0
- Python 3.13 (for local development)
- Git with pre-commit hooks support

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd inscribe-data-processing-service
   ```

2. **Set up development environment**:
   ```bash
   # Install pre-commit hooks for code quality
   ./scripts/setup-pre-commit.sh
   
   # Set up environment variables
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application locally**:
   ```bash
   docker-compose up -d
   ```

4. **Test the API**:
   ```bash
   ./scripts/secure_api_test.sh http://localhost:8080
   ```

5. **Access API documentation**:
   Open http://localhost:8080/docs in your browser

### Infrastructure Setup

1. **Configure AWS credentials**:
   ```bash
   aws configure
   ```

2. **Configure Terraform variables**:
   ```bash
   cd terraform
   cp terraform.tfvars.example terraform.tfvars
   # Edit terraform.tfvars with your AWS settings and desired configuration
   ```

3. **Deploy infrastructure and application**:
   ```bash
   cd ..
   ./deploy.sh
   ```

   This single command will:
   - Deploy AWS infrastructure (VPC, EC2, RDS, ECR, Security Groups)
   - Automatically build and push container images to ECR
   - Install and configure the application on EC2
   - Set up monitoring and management tools

4. **Access your deployed instance**:
   ```bash
   # Get all access information
   cd terraform && terraform output access_methods
   
   # SSM Session Manager Access (secure, no SSH keys needed)
   terraform output ssm_connect_command
   # Or use AWS Console: EC2 → Instance → Connect → Session Manager
   ```

5. **Monitor deployment progress**:
   ```bash
   # After connecting to EC2 (either SSH or SSM):
   sudo tail -f /var/log/user-data.log
   
   # Check if deployment completed
   grep "completed successfully" /var/log/user-data.log
   ```

6. **Test the deployment**:
   ```bash
   # Wait 5-10 minutes for complete deployment, then test
   ./scripts/secure_api_test.sh http://<EC2_PUBLIC_IP>:8080
   ```

## Security Features

### Credential Management
- **AWS Secrets Manager Integration**: All production credentials are automatically generated and stored securely
- **No Hardcoded Passwords**: Zero hardcoded credentials in source code or configuration files
- **Secure Credential Retrieval**: Uses boto3 and AWS SDK for runtime credential loading
- **Environment Separation**: Different credential sets for development, staging, and production

### Secure API Testing
While testing locally, you can use the provided secure testing script instead of manual curl commands:
```bash
# Health check
./scripts/secure_api_test.sh http://localhost:8080/health

# Get customers
./scripts/secure_api_test.sh http://localhost:8080/customers

# Create customer
./scripts/secure_api_test.sh http://localhost:8080/customers POST '{
  "first_name": "John",
  "last_name": "Doe", 
  "email": "john@example.com"
}'
```

**Important Security Notes:**
- Never hardcode credentials in source code, scripts, or documentation
- Always retrieve credentials from environment variables or AWS Secrets Manager
- Use the secure testing script for all API interactions
- The application automatically generates random credentials and stores them securely

### Authentication & Authorization
- **HTTP Basic Authentication** with secure credential retrieval
- **Secure credential comparison** using timing-safe functions  
- **Authentication required** for all API endpoints (except health check)
- **Ready for OAuth2/JWT upgrade** when needed

### Input Validation
- **Pydantic models** for comprehensive input validation
- **Email validation** using built-in validators
- **Name sanitization** to prevent malicious input
- **Length limits** on all text fields
- **Date format validation** for birth dates

### SQL Injection Prevention
- **Parameterized queries** using PyMySQL
- **No dynamic SQL construction** from user input
- **Prepared statements** for all database operations
- **Input sanitization** at the API layer

### Infrastructure Security
- **Security groups** with least privilege access
- **Database isolation** in private subnets
- **Encrypted storage** for RDS instances
- **Network-level access control**
- **IAM database authentication** enabled
- **Minimal AWS permissions** following principle of least privilege

## API Endpoints

### Health Check
```bash
GET /health
```

### Customer Management
```bash
# Create customer
POST /customers
Authorization: Basic <credentials>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe",
  "email": "john.doe@example.com",
  "phone": "+1-555-0123",
  "address": "123 Main St",
  "date_of_birth": "1990-01-01"
}

# Get all customers
GET /customers?skip=0&limit=100
Authorization: Basic <credentials>

# Get customer by ID
GET /customers/{id}
Authorization: Basic <credentials>

# Update customer
PUT /customers/{id}
Authorization: Basic <credentials>
Content-Type: application/json

{
  "first_name": "Jane",
  "email": "jane.doe@example.com"
}

# Delete customer
DELETE /customers/{id}
Authorization: Basic <credentials>
```

### Authentication
- **Credentials**: Retrieved securely from AWS Secrets Manager in production
- **Development**: Use `./scripts/secure_api_test.sh` for testing
- **Note**: Default credentials are auto-generated and stored securely

## Testing

### Unit Tests
```bash
# Install test dependencies
pip install -r test-requirements.txt

# Run tests with coverage
pytest tests/ -v --cov=src --cov-report=xml --cov-report=html

# Run specific test file
pytest tests/test_main.py -v
```

### Pre-commit Testing
```bash
# Run all pre-commit hooks
pre-commit run --all-files

# Run specific hooks
pre-commit run black
pre-commit run flake8
pre-commit run pytest
```

### Security Testing
```bash
# Install security tools
pip install bandit safety

# Run security scan
bandit -r src/
safety check
```

### API Testing
```bash
# Use the secure testing script for API calls
./scripts/secure_api_test.sh http://localhost:8080

# Test specific endpoints
./scripts/secure_api_test.sh http://localhost:8080/health
./scripts/secure_api_test.sh http://localhost:8080/customers
```

## CI/CD Pipeline

The project uses separated CircleCI configurations for different purposes:

### Development Pipeline (.circleci/config.yml)
- **Test Stage**: Unit test execution with coverage reporting
- **Code Quality**: Black formatting, isort import sorting, flake8 linting
- **Security Scanning**: Bandit security analysis, dependency vulnerability checks
- **Build Stage**: Docker image building and ECR integration
- **Container Security**: Trivy vulnerability scanning

### Infrastructure Pipeline (.circleci/infra-config.yml)
- **Infrastructure Stage**: Terraform plan and apply with latest orb
- **Deploy Stage**: Application deployment to EC2 via AWS SSM
- **Health Checks**: Automated validation and monitoring setup
- **ECR Integration**: Container registry with vulnerability scanning

### Pre-commit Hooks
Local development includes automated code quality checks:
- **Black**: Code formatting
- **isort**: Import organization (black profile)
- **flake8**: Code linting and style checking
- **pytest**: Unit test execution

Setup pre-commit hooks:
```bash
./scripts/setup-pre-commit.sh
```

### Environment Variables Required

Set these in CircleCI project settings:

```bash
# AWS
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION

# ECR
AWS_ACCOUNT_ID

# Deployment
AWS_EC2_INSTANCE_ID
```

## Infrastructure Components

### AWS Resources Created

1. **ECR Repository**:
   - Private container registry
   - Image vulnerability scanning enabled
   - Lifecycle policies for image management
   - Integration with CircleCI for automated pushes

2. **EC2 Instance**:
   - Amazon Linux 2
   - Docker and Docker Compose pre-installed
   - Security group with HTTP/HTTPS/SSH access
   - Elastic IP for stable public address
   - SSM Session Manager enabled

3. **RDS MySQL Instance**:
   - MySQL 8.0
   - Encrypted storage
   - Automated backups
   - Performance Insights enabled
   - Security group allowing access only from EC2

4. **AWS Secrets Manager**:
   - Secure credential storage
   - Automatic password generation
   - Runtime credential retrieval
   - Rotation policies configured

5. **Security Groups**:
   - EC2: HTTP (8080), HTTPS (443), SSH (22)
   - RDS: MySQL (3306) from EC2 only

6. **IAM Roles and Policies**:
   - EC2 instance role with minimal required permissions
   - Secrets Manager access
   - SSM Session Manager access
   - ECR image pull permissions

### Terraform Modules

- **`modules/ecr`**: ECR repository with scanning and lifecycle policies
- **`modules/ec2`**: EC2 instance with user data script for auto-deployment
- **`modules/rds`**: RDS instance with security configurations
- **`modules/secrets`**: AWS Secrets Manager for secure credential storage
- **`modules/security`**: Security groups with least privilege
- **`modules/iam`**: IAM roles and policies for secure access

## Monitoring & Observability

### Logging
- **Structured logging** with Python logging module
- **Request/response logging** for all API calls
- **Error tracking** with detailed stack traces
- **Security event logging** for authentication failures

### Health Monitoring
- **Health check endpoint** at `/health`
- **Database connectivity validation**
- **Container health checks** in Docker Compose
- **Ready for integration** with monitoring tools

### Optional: Datadog Integration
```python
# Add to requirements.txt
datadog==0.44.0

# Environment variables
DD_API_KEY=your-api-key
DD_SITE=datadoghq.com
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DB_HOST` | Database hostname | `localhost` |
| `DB_NAME` | Database name | `inscribe_customers` |
| `DB_USER` | Database username | `admin` |
| `DB_PASSWORD` | Database password | `password` |
| `DB_PORT` | Database port | `3306` |
| `ENVIRONMENT` | Environment name | `development` |

### Terraform Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `aws_region` | AWS region | `eu-west-1` |
| `environment` | Environment name | `dev` |
| `instance_type` | EC2 instance type | `t3.micro` |
| `db_instance_class` | RDS instance class | `db.t3.micro` |
| `allowed_cidr_blocks` | Allowed IP ranges | `["0.0.0.0/0"]` |

## Deployment

### Automated Deployment

1. **Development Changes**:
   Push to any branch to trigger the development pipeline:
   ```bash
   git push origin feature-branch
   ```

2. **Infrastructure Deployment**:
   Trigger infrastructure pipeline via CircleCI API or manual approval

3. **Production Deployment**:
   Merge to `main` branch triggers both pipelines

### Manual Deployment

1. **Build and push Docker image**:
   ```bash
   # Login to ECR
   aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account>.dkr.ecr.<region>.amazonaws.com
   
   # Build and tag image
   docker build -t inscribe-customer-service:latest .
   docker tag inscribe-customer-service:latest <account>.dkr.ecr.<region>.amazonaws.com/inscribe-customer-service:latest
   
   # Push to ECR
   docker push <account>.dkr.ecr.<region>.amazonaws.com/inscribe-customer-service:latest
   ```

2. **Deploy infrastructure**:
   ```bash
   cd terraform
   terraform init
   terraform plan
   terraform apply
   ```

3. **Connect to EC2 and manage application**:
   ```bash
   # Via SSM Session Manager
   aws ssm start-session --target <instance-id>
   
   # Check application status
   sudo docker ps
   sudo docker logs inscribe-app
   ```

## Security Considerations

### Production Recommendations

1. **Authentication**:
   - Replace Basic Auth with OAuth2/JWT
   - Implement API key management
   - Add rate limiting

2. **Database**:
   - Use AWS Secrets Manager for credentials
   - Enable encryption in transit
   - Implement connection pooling

3. **Network**:
   - Place RDS in private subnets
   - Use Application Load Balancer with SSL
   - Implement WAF rules

4. **Monitoring**:
   - Enable AWS CloudTrail
   - Set up CloudWatch alarms
   - Implement log aggregation

## Troubleshooting

### Common Issues

1. **Database Connection Failed**:
   ```bash
   # Check security groups
   aws ec2 describe-security-groups
   
   # Verify RDS endpoint
   aws rds describe-db-instances
   ```

2. **Docker Container Won't Start**:
   ```bash
   # Check logs
   docker logs <container-id>
   
   # Verify environment variables
   docker exec -it <container-id> env
   ```

3. **Terraform Apply Fails**:
   ```bash
   # Check AWS credentials
   aws sts get-caller-identity
   
   # Verify permissions
   aws iam get-user
   ```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Set up pre-commit hooks (`./scripts/setup-pre-commit.sh`)
4. Make your changes and ensure they pass all checks
5. Run the full test suite (`pytest tests/`)
6. Commit your changes (pre-commit hooks will run automatically)
7. Push to your fork (`git push origin feature/amazing-feature`)
8. Create a Pull Request

### Code Quality Standards

- **Black**: Code formatting (line length: 88)
- **isort**: Import sorting with black profile
- **flake8**: Linting and style checking
- **pytest**: Minimum 80% test coverage
- **Bandit**: Security scanning for vulnerabilities

### Documentation

Documentation is organized in the `docs.bak/` directory:
- API examples and guides
- Deployment and configuration instructions
- Security and compliance documentation
- Troubleshooting guides



#### Troubleshooting
1. **Review logs** for error details:
   ```bash
   # Application logs
   sudo docker logs inscribe-app
   
   # System logs
   sudo tail -f /var/log/user-data.log
   ```

   ```bash
   # Management commands (on EC2 instance):
   sudo systemctl status inscribe-app    # Check service status
   /opt/inscribe-app/manage.sh logs      # View application logs
   /opt/inscribe-app/manage.sh health    # Check application health
   ```

2. **Run diagnostics**:
   ```bash
   # Test API health
   ./scripts/secure_api_test.sh http://localhost:8080/health
   
   # Check database connectivity
   docker exec -it inscribe-app python -c "from src.app.database.connection import get_db_connection; print('DB OK' if get_db_connection() else 'DB FAIL')"
   ```
3. **Create an issue** in the repository with:
   - Clear description of the problem
   - Steps to reproduce
   - Relevant log excerpts
   - Environment details

---
