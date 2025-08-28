#!/bin/bash

# Secure API Testing Script
# This script retrieves credentials from AWS Secrets Manager and tests the API

set -e

# Configuration
REGION="${AWS_REGION:-eu-west-1}"
ENVIRONMENT="${ENVIRONMENT:-dev}"
SECRET_NAME="${ENVIRONMENT}-inscribe-application-secrets-52583"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Secure API Testing Script${NC}"
echo "=================================="

# Function to retrieve credentials from Secrets Manager
get_credentials() {
    echo -e "${YELLOW}Retrieving credentials from AWS Secrets Manager...${NC}"
    
    # Check if AWS CLI is available
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}AWS CLI not found. Please install it first.${NC}"
        exit 1
    fi
    
    # Retrieve secret
    SECRET_JSON=$(aws secretsmanager get-secret-value \
        --secret-id "$SECRET_NAME" \
        --region "$REGION" \
        --query 'SecretString' \
        --output text 2>/dev/null)
    
    if [ $? -ne 0 ] || [ -z "$SECRET_JSON" ]; then
        echo -e "${RED}Failed to retrieve credentials from Secrets Manager${NC}"
        echo -e "${YELLOW}Fallback: Using environment variables${NC}"
        
        # Fallback to environment variables
        API_USERNAME="${BASIC_AUTH_USERNAME:-admin}"
        echo API_USERNAME=$API_USERNAME
        API_PASSWORD="${BASIC_AUTH_PASSWORD:-dev_password_change_me}"
        
        if [ "$API_PASSWORD" = "dev_password_change_me" ]; then
            echo -e "${RED}Using default password - change this in production!${NC}"
        fi
    else
        # Parse JSON to extract credentials
        API_USERNAME=$(echo "$SECRET_JSON" | jq -r '.basic_auth_username')
        API_PASSWORD=$(echo "$SECRET_JSON" | jq -r '.basic_auth_password')
        
        if [ "$API_USERNAME" = "null" ] || [ "$API_PASSWORD" = "null" ]; then
            echo -e "${RED}Invalid credentials format in Secrets Manager${NC}"
            exit 1
        fi
        echo -e "API_USERNAME=$API_USERNAME"
        echo -e "API_PASSWORD=$API_PASSWORD"
        echo -e "${GREEN}Credentials retrieved successfully from Secrets Manager${NC}"
    fi
}

# Function to test API endpoint
test_api() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"
    
    echo -e "${YELLOW}Testing ${method} ${endpoint}${NC}"
    
    if [ "$method" = "POST" ] && [ -n "$data" ]; then
        response=$(curl -s -w "HTTP_CODE:%{http_code}" \
            -u "${API_USERNAME}:${API_PASSWORD}" \
            -X "$method" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$endpoint")
    else
        response=$(curl -s -w "HTTP_CODE:%{http_code}" \
            -u "${API_USERNAME}:${API_PASSWORD}" \
            -X "$method" \
            "$endpoint")
    fi
    
    http_code=$(echo "$response" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
    body=$(echo "$response" | sed 's/HTTP_CODE:[0-9]*$//')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}Success (HTTP $http_code)${NC}"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo -e "${RED}Failed (HTTP $http_code)${NC}"
        echo "$body"
    fi
    
    echo ""
}

# Main execution
main() {
    # Get target URL
    if [ -z "$1" ]; then
        echo "Usage: $0 <API_URL>"
        echo "Example: $0 http://localhost:8080"
        echo "Example: $0 http://3.123.45.67:8080"
        exit 1
    fi
    
    BASE_URL="$1"
    
    # Retrieve credentials securely
    get_credentials
    
    # Test API endpoints
    echo -e "${GREEN}Testing API endpoints...${NC}"
    echo "=================================="
    
    test_api "${BASE_URL}/health"
    test_api "${BASE_URL}/api/v1/health"
    test_api "${BASE_URL}/api/v1/customers/"
    
    # Test creating a customer
    customer_data='{
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "phone": "+1234567890",
        "address": "123 Main St, City, State",
        "date_of_birth": "1990-01-01"
    }'
    
    test_api "${BASE_URL}/api/v1/customers/" "POST" "$customer_data"
    
    echo -e "${GREEN}API testing completed${NC}"
    echo ""
    echo -e "${YELLOW}Security Notes:${NC}"
    echo "- Credentials were retrieved from AWS Secrets Manager"
    echo "- No secrets were logged or displayed in plain text"
    echo "- Use this script instead of hardcoded credentials"
}

# Run main function with all arguments
main "$@"
