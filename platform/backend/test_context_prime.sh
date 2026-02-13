#!/bin/bash

# Test Context Prime Endpoint with Golden Score
# Reads API key and project ID from .env file

echo "🧪 Testing Context Prime Endpoint"
echo "=================================="
echo ""

# Check if backend is running
if ! curl -s http://localhost:8000/ > /dev/null; then
    echo "❌ Backend not running on localhost:8000"
    echo "Start with: cd platform/backend && uvicorn main:app --reload"
    exit 1
fi

echo "✅ Backend is running"
echo ""

# Load environment variables from .env
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
    echo "✅ Loaded .env file"
else
    echo "⚠️  No .env file found"
fi

# Check for required variables
if [ -z "$AGORA_API_KEY" ]; then
    echo "❌ AGORA_API_KEY not set in .env"
    echo "   Add: AGORA_API_KEY=agora_xxx"
    exit 1
fi

if [ -z "$TEST_PROJECT_ID" ]; then
    echo "❌ TEST_PROJECT_ID not set in .env"
    echo "   Add: TEST_PROJECT_ID=your-project-uuid"
    exit 1
fi

echo "📡 Calling /v1/context/prime..."
echo "   Project ID: $TEST_PROJECT_ID"
echo ""

# Make the request
response=$(curl -X POST http://localhost:8000/v1/context/prime \
  -H "Authorization: Bearer $AGORA_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$TEST_PROJECT_ID\"}" \
  -w "\n%{http_code}" \
  -s)

# Split response and status code
http_code=$(echo "$response" | tail -n1)
body=$(echo "$response" | sed '$d')

# Pretty print JSON if jq is available
if command -v jq &> /dev/null; then
    echo "$body" | jq '.'
else
    echo "$body"
fi

echo ""
echo "HTTP Status: $http_code"
echo ""

if [ "$http_code" = "200" ]; then
    echo "✅ Test successful!"
else
    echo "❌ Test failed with status $http_code"
fi

echo ""
echo "📊 What to look for in backend logs:"
echo "  - First call: ❌ Cache miss → 🎯 Ranked N failures, M code changes"
echo "  - Second call (within 5 min): ✅ Cache hit"
echo "  - Embedding tokens: N for text length M"
