#!/bin/bash
# Agora Context - Get AI-ranked debugging context with actionable file locations
# Usage: ./agora-context.sh [project-id]

set -e

# Configuration
BACKEND_URL="${AGORA_BACKEND_URL:-http://localhost:8000}"
PROJECT_ID="${1:-$AGORA_PROJECT_ID}"

# Validation
if [ -z "$AGORA_API_KEY" ]; then
    echo "❌ AGORA_API_KEY not set"
    echo "   Export it: export AGORA_API_KEY=agora_xxx"
    exit 1
fi

if [ -z "$PROJECT_ID" ]; then
    echo "Usage: $0 <project-id>"
    echo "   Or set: export AGORA_PROJECT_ID=your-uuid"
    exit 1
fi

echo "🔍 Fetching AI context for project: $PROJECT_ID"
echo ""

# Call Context Prime endpoint
response=$(curl -s -X POST "$BACKEND_URL/v1/context/prime" \
  -H "Authorization: Bearer $AGORA_API_KEY" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\": \"$PROJECT_ID\"}")

# Parse and display with Python
echo "$response" | python3 -c "
import sys, json

data = json.load(sys.stdin)

print('📊 AI SUMMARY')
print('=' * 60)
print(data['context_summary'])
print()

print('🔥 TOP FAILURES (Ranked by Golden Score)')
print('=' * 60)

for i, failure in enumerate(data['metadata']['recent_failures'][:5], 1):
    print(f'\n#{i} {failure[\"name\"]}')
    print(f'   Error: {failure[\"error_message\"]}')
    print(f'   Time: {failure[\"timestamp\"]}')
    
    attrs = failure.get('attributes', {})
    
    # Show workflow/node info with file search hints
    if 'agora.flow' in attrs:
        workflow = attrs['agora.flow']
        print(f'   📁 Workflow: {workflow}')
        # Suggest file search
        workflow_file = workflow.lower().replace(' ', '_')
        print(f'   💡 Search for: {workflow_file}.py or similar')
    
    if 'agora.node' in attrs:
        node = attrs['agora.node']
        print(f'   🔧 Node: {node}')
        # Suggest function search
        node_func = node.lower().replace(' ', '_')
        print(f'   💡 Search for: def {node_func}( or @agora_node')
    
    # Show trace/execution IDs for debugging
    print(f'   🔍 Trace ID: {failure[\"trace_id\"]}')
    if 'execution_id' in attrs:
        print(f'   🔍 Execution: {attrs[\"execution_id\"]}')
    
    # Add actionable debugging steps
    print(f'   📝 Debug steps:')
    if 'agora.flow' in attrs:
        print(f'      1. Search codebase for \"{attrs[\"agora.flow\"]}\"')
    if 'agora.node' in attrs:
        print(f'      2. Find @agora_node decorator for \"{attrs[\"agora.node\"]}\"')
    print(f'      3. Check telemetry for trace_id: {failure[\"trace_id\"]}')

print('\n' + '=' * 60)
print('💡 TIPS FOR CLINE/CLAUDE:')
print('=' * 60)
print('1. Focus on #1 first (highest golden score)')
print('2. Search your codebase for the workflow/node names above')
print('3. Use trace IDs to find related failures in telemetry')
print('4. Check execution IDs to see full workflow timeline')
print()
print('📋 COPY THIS TO CLINE/CLAUDE:')
print('-' * 60)
print(f'I have {len(data[\"metadata\"][\"recent_failures\"])} AI-ranked failures.')
print(f'Top issue: {data[\"metadata\"][\"recent_failures\"][0][\"name\"]}')
if 'agora.flow' in data['metadata']['recent_failures'][0].get('attributes', {}):
    print(f'Workflow: {data[\"metadata\"][\"recent_failures\"][0][\"attributes\"][\"agora.flow\"]}')
print(f'Error: {data[\"metadata\"][\"recent_failures\"][0][\"error_message\"]}')
print()
print('Can you help me find and fix this in my codebase?')
print('Search for the workflow/node names listed above.')
"
