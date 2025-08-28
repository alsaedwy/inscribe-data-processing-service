# Inscribe Data Processing Service

A secure, s**Free Tier Note**: This project is configured to use only AWS Free Tier resources. See `FREE_TIER_COMPLIANCE.md` for details on staying within free limits.alable microservice architecture for customer data management, built with FastAPI, containerized with Docker, and deployed on AWS infrastructure using Terraform.

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
- Python 3.11+ (for local development)
- **AWS Free Tier eligible account** (for cost-free deployment)

> 💰 **Free Tier Note**: This project is configured to use only AWS Free Tier resources. See `FREE_TIER_COMPLIANCE.md` for details on staying within free limits.

### Local Development

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd inscribe-data-processing-service
   ```

2. **Set up environment variables**:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

3. **Start the application locally**:
   ```bash
   docker-compose up -d
   ```

4. **Test the API**:
   ```bash
   ./scripts/secure_api_test.sh http://localhost:8000
   ```

5. **Access API documentation**:
   Open http://localhost:8000/docs in your browser

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
   - Deploy AWS infrastructure (VPC, EC2, RDS, Security Groups)
   - Automatically install and configure the application on EC2
   - Set up monitoring and management tools

4. **Access your deployed instance**:
   ```bash
   # Get all access information
   cd terraform && terraform output access_methods
   
   # SSM Session Manager Access (secure, no SSH keys needed)
   terraform output ssm_connect_command
   # Or use AWS Console: EC2 → Instance → Connect → Session Manager
   ```

   **For detailed access instructions, see [EC2_ACCESS_GUIDE.md](./EC2_ACCESS_GUIDE.md)**

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
   ./scripts/secure_api_test.sh http://<EC2_PUBLIC_IP>:8000
   ```

**For complete setup instructions, see [DEPLOYMENT_GUIDE.md](./DEPLOYMENT_GUIDE.md)**

## Security Features

### Credential Management
- **AWS Secrets Manager Integration**: All production credentials are automatically generated and stored securely
- **No Hardcoded Passwords**: Zero hardcoded credentials in source code or configuration files
- **Secure Credential Retrieval**: Uses boto3 and AWS SDK for runtime credential loading
- **Environment Separation**: Different credential sets for development, staging, and production

### Secure API Testing
Always use the provided secure testing script instead of manual curl commands:
```bash
# Health check
./scripts/secure_api_test.sh http://localhost:8000/health

# Get customers
./scripts/secure_api_test.sh http://localhost:8000/customers

# Create customer
./scripts/secure_api_test.sh http://localhost:8000/customers POST '{
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

### Run Unit Tests
```bash
# Install test dependencies
pip install -r test-requirements.txt

# Run tests
pytest tests/ -v
```

### Security Testing
```bash
# Install security tools
pip install bandit safety

# Run security scan
bandit -r src/
safety check
```

### Load Testing
```bash
# Use the secure testing script for API calls
./scripts/secure_api_test.sh http://localhost:8000

# Or test specific endpoints (after retrieving credentials securely)
# Example: Create a customer
echo '{"first_name":"Test","last_name":"User","email":"test@example.com"}' | \
./scripts/secure_api_test.sh http://localhost:8000
```

## CI/CD Pipeline

The CircleCI pipeline includes:

1. **Test Stage**:
   - Unit test execution
   - Security scanning with Bandit and Safety
   - Code quality checks

2. **Build Stage**:
   - Docker image building
   - Container security scanning with Trivy
   - Image pushing to Docker Hub

3. **Infrastructure Stage**:
   - Terraform plan and apply
   - Infrastructure validation

4. **Deploy Stage**:
   - Application deployment to EC2
   - Health checks and validation

### Environment Variables Required

Set these in CircleCI project settings:

```bash
# Docker Hub
DOCKERHUB_USERNAME
DOCKERHUB_PASSWORD

# AWS
AWS_ACCESS_KEY_ID
AWS_SECRET_ACCESS_KEY
AWS_DEFAULT_REGION

# Deployment
EC2_HOST
AWS_EC2_INSTANCE_ID
```

## Infrastructure Components

### AWS Resources Created

1. **EC2 Instance**:
   - Amazon Linux 2
   - Docker and Docker Compose pre-installed
   - Security group with HTTP/HTTPS/SSH access
   - Elastic IP for stable public address

2. **RDS MySQL Instance**:
   - MySQL 8.0
   - Encrypted storage
   - Automated backups
   - Performance Insights enabled
   - Security group allowing access only from EC2

3. **Security Groups**:
   - EC2: HTTP (8000), HTTPS (443), SSH (22)
   - RDS: MySQL (3306) from EC2 only

4. **Networking**:
   - Default VPC usage
   - Multi-AZ subnet group for RDS
   - Internet Gateway access for EC2

### Terraform Modules

- **`modules/ec2`**: EC2 instance with user data script
- **`modules/rds`**: RDS instance with security configurations
- **`modules/security`**: Security groups with least privilege

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

### Manual Deployment

1. **Build and push Docker image**:
   ```bash
   docker build -t inscribe/customer-data-service:latest .
   docker push inscribe/customer-data-service:latest
   ```

2. **Deploy infrastructure**:
   ```bash
   cd terraform
   terraform apply
   ```

3. **SSH to EC2 and start application**:
   ```bash
   ssh ec2-user@<ec2-public-ip>
   cd /opt/inscribe-app
   ./start_app.sh
   ```

### Automated Deployment

Push to the `main` branch to trigger the CI/CD pipeline.

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
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## License

This project is licensed under the MIT License.

## Support

For questions or issues, please:
1. Check the troubleshooting section
2. Review the logs for error details
3. Create an issue in the repository

---

**Built with dedication for Inscribe's mission of creating fair and efficient financial services.**
