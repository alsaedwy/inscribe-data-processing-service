#!/bin/bash

BASE_URL="http://176.34.251.95:8000/api/v1"
USERNAME="qzrb4r0rhgx1272r"
PASSWORD='jXDiGD>@YhsCteU!3s+pNoe3GR1)uu+4'

echo "Testing API endpoints..."

echo "1. Testing health endpoint:"
curl -s "$BASE_URL/health" | jq .

echo -e "\n2. Testing customers list (should be empty initially):"
curl -s -X GET "$BASE_URL/customers/" \
  --user "$USERNAME:$PASSWORD" \
  | jq .

echo -e "\n3. Creating a test customer:"
curl -s -X POST "$BASE_URL/customers/" \
  --user "$USERNAME:$PASSWORD" \
  -H "Content-Type: application/json" \
  -d '{
    "first_name": "John",
    "last_name": "Doe",
    "email": "john.doe@example.com", 
    "phone": "+1-555-0123",
    "address": "123 Main St, City, State 12345"
  }' | jq .

echo -e "\n4. Getting customers list again:"
curl -s -X GET "$BASE_URL/customers/" \
  --user "$USERNAME:$PASSWORD" \
  | jq .

echo -e "\nAPI tests completed!"
