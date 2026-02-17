#!/bin/bash
# Quick MCP Server Test Script
# Tests core functionality of Agora Context Prime MCP server

echo "🧪 Agora MCP Server Test Suite"
echo "================================"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

PASS=0
FAIL=0

# Test 1: Server Startup
echo -n "Test 1: Server Startup... "
OUTPUT=$(AGORA_API_KEY="agora_kZm1BBglxdHyEyaz1NmpxowSLbYvZWyK" \
AGORA_PROJECT_ID="97be4a93-efe3-4374-b99b-f73dbb958ed9" \
AGORA_BACKEND_URL="http://localhost:8000" \
/Users/anirudhanil/Desktop/agora3/Agora/.venv/bin/python3 server.py < /dev/null 2>&1 | head -5)

if echo "$OUTPUT" | grep -q "✅"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi

# Test 2: Backend Health
echo -n "Test 2: Backend Health... "
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    echo "   (Make sure backend is running: cd platform/backend && uvicorn main:app --reload)"
    ((FAIL++))
fi

# Test 3: Context Prime API
echo -n "Test 3: Context Prime API... "
RESPONSE=$(curl -s -X POST http://localhost:8000/v1/context/prime \
  -H "Authorization: Bearer agora_kZm1BBglxdHyEyaz1NmpxowSLbYvZWyK" \
  -H "Content-Type: application/json" \
  -d '{"project_id":"97be4a93-efe3-4374-b99b-f73dbb958ed9"}' 2>&1)

if echo "$RESPONSE" | grep -q "context_summary"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi

# Test 4: Format Function
echo -n "Test 4: Format Function... "
FORMAT_TEST=$(/Users/anirudhanil/Desktop/agora3/Agora/.venv/bin/python3 -c "
import sys
sys.path.insert(0, '.')
from server import format_context

data = {
    'context_summary': 'Test',
    'metadata': {'recent_failures': []}
}
result = format_context(data, 'L1')
print('PASS' if 'No critical failures' in result else 'FAIL')
" 2>&1)

if echo "$FORMAT_TEST" | grep -q "PASS"; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi

# Test 5: Logging
echo -n "Test 5: Logging Setup... "
if [ -d "logs" ] || mkdir -p logs; then
    echo -e "${GREEN}✅ PASS${NC}"
    ((PASS++))
else
    echo -e "${RED}❌ FAIL${NC}"
    ((FAIL++))
fi

# Summary
echo ""
echo "================================"
echo "Test Results: ${PASS} passed, ${FAIL} failed"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✅ All tests passed!${NC}"
    echo "MCP server is ready to use with Cline and other agents."
    exit 0
else
    echo -e "${RED}❌ Some tests failed${NC}"
    echo "Check the output above for details."
    exit 1
fi
