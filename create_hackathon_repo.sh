#!/bin/bash
# =============================================================================
# CREATE NEW AGORA HACKATHON REPO AND PUSH TO GITHUB
# =============================================================================

echo "========================================================================"
echo "🚀 CREATING NEW AGORA HACKATHON REPO"
echo "========================================================================"
echo ""

# 1. Create new directory
echo "📁 Step 1: Creating new repo directory..."
cd ~
mkdir -p agora
cd agora

# 2. Transfer core files
echo "📦 Step 2: Transferring core Agora files..."
bash /home/user/Agora/transfer_to_hackathon.sh ~/agora

# 3. Initialize git
echo "🔧 Step 3: Initializing git repository..."
git init
git add .
git commit -m "Initial commit - Agora hackathon edition

Core workflow orchestration framework with local telemetry.

Features:
- Workflow orchestration with async nodes
- Conditional routing
- Retry logic and error handling
- Batch processing
- Wide events (business context)
- Local telemetry (console + file)
- LLM auto-tracing

No platform dependencies - fully offline capable."

# 4. Create GitHub repo and push
echo "🌐 Step 4: Creating GitHub repository..."
echo ""
echo "Creating repo 'agora' on GitHub..."

# Create GitHub repo using gh CLI
gh repo create agora --public --source=. --remote=origin --description="AI workflow orchestration with local telemetry - hackathon edition"

# Push to GitHub
echo ""
echo "📤 Step 5: Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "========================================================================"
echo "✅ SUCCESS!"
echo "========================================================================"
echo ""
echo "Your new repo is ready at:"
gh repo view --web --json url -q .url
echo ""
echo "Next steps:"
echo "  1. cd ~/agora"
echo "  2. pip install -r requirements.txt"
echo "  3. export OPENAI_API_KEY='sk-...'"
echo "  4. python hackathon_demo.py"
echo ""
echo "Happy hacking! 🚀"
echo "========================================================================"
