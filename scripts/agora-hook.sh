#!/bin/bash
# Agora Context Hook
# 
# This script fetches intelligent context from Agora and injects it into your AI assistant.
# Add to your shell profile (~/.zshrc or ~/.bashrc):
#   source /path/to/agora-hook.sh
#
# Usage:
#   agora-prime <project_id>

# Configuration
AGORA_API_ENDPOINT="${AGORA_API_ENDPOINT:-http://localhost:8000}"
AGORA_API_KEY="${AGORA_API_KEY}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

agora-prime() {
    local project_id="$1"
    
    if [ -z "$project_id" ]; then
        echo -e "${RED}❌ Error: project_id required${NC}"
        echo "Usage: agora-prime <project_id>"
        return 1
    fi
    
    if [ -z "$AGORA_API_KEY" ]; then
        echo -e "${RED}❌ Error: AGORA_API_KEY not set${NC}"
        echo "Set it in your environment: export AGORA_API_KEY=agora_xxx"
        return 1
    fi
    
    echo -e "${YELLOW}🧠 Fetching context from Agora...${NC}"
    
    # Call the context prime API
    local response=$(curl -s -X POST "${AGORA_API_ENDPOINT}/v1/context/prime" \
        -H "Authorization: Bearer ${AGORA_API_KEY}" \
        -H "Content-Type: application/json" \
        -d "{\"project_id\": \"${project_id}\"}")
    
    # Check if request was successful
    if [ $? -ne 0 ]; then
        echo -e "${RED}❌ Failed to fetch context${NC}"
        return 1
    fi
    
    # Extract context summary using jq (or python if jq not available)
    local summary=""
    if command -v jq &> /dev/null; then
        summary=$(echo "$response" | jq -r '.context_summary // empty')
    else
        # Fallback to python
        summary=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('context_summary', ''))" 2>/dev/null)
    fi
    
    if [ -z "$summary" ]; then
        echo -e "${RED}❌ No context summary returned${NC}"
        echo "Response: $response"
        return 1
    fi
    
    # Display the context
    echo -e "${GREEN}✅ Context Summary:${NC}"
    echo ""
    echo "$summary"
    echo ""
    
    # Copy to clipboard if available
    if command -v pbcopy &> /dev/null; then
        echo "$summary" | pbcopy
        echo -e "${GREEN}📋 Copied to clipboard${NC}"
    elif command -v xclip &> /dev/null; then
        echo "$summary" | xclip -selection clipboard
        echo -e "${GREEN}📋 Copied to clipboard${NC}"
    fi
    
    # Save to temp file for AI assistants to read
    local context_file="/tmp/agora_context_${project_id}.txt"
    echo "$summary" > "$context_file"
    echo -e "${GREEN}💾 Saved to: ${context_file}${NC}"
    
    return 0
}

# Auto-prime on directory change (optional)
# Uncomment to enable automatic context fetching when entering project directories
#
# agora-auto-prime() {
#     # Check if .agora-project file exists in current directory
#     if [ -f ".agora-project" ]; then
#         local project_id=$(cat .agora-project)
#         agora-prime "$project_id"
#     fi
# }
#
# # Hook into directory change
# if [ -n "$ZSH_VERSION" ]; then
#     # Zsh
#     autoload -U add-zsh-hook
#     add-zsh-hook chpwd agora-auto-prime
# elif [ -n "$BASH_VERSION" ]; then
#     # Bash
#     PROMPT_COMMAND="${PROMPT_COMMAND:+$PROMPT_COMMAND; }agora-auto-prime"
# fi

# Export function
export -f agora-prime

echo -e "${GREEN}✅ Agora context hook loaded${NC}"
echo "Usage: agora-prime <project_id>"
