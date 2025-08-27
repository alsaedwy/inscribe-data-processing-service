#!/bin/bash

# Test individual endpoints to isolate the issue

BASE_URL="http://176.34.251.95:8000/api/v1"
USERNAME="qzrb4r0rhgx1272r"
PASSWORD='jXDiGD>@YhsCteU!3s+pNoe3GR1)uu+4'

echo "Testing individual endpoints for detailed debugging..."

echo "1. Health check (working):"
curl -s "$BASE_URL/health" | jq .

echo -e "\n2. Testing customers list with verbose output:"
curl -v -X GET "$BASE_URL/customers/" \
  --user "$USERNAME:$PASSWORD" \
  2>&1 | head -20

echo -e "\n3. Testing a simpler endpoint - getting customer by ID 1:"
curl -v -X GET "$BASE_URL/customers/1" \
  --user "$USERNAME:$PASSWORD" \
  2>&1 | head -20

echo -e "\nDebugging tests completed!"
