# Agora Context - Quick Start Guide

## 🚀 Use with Cline/Claude RIGHT NOW

### Step 1: Set Environment Variables
```bash
export AGORA_API_KEY="agora_kZm1BBglxdHyEyaz1NmpxowSLbYvZWyK"
export AGORA_PROJECT_ID="97be4a93-efe3-4374-b99b-f73dbb958ed9"
```

### Step 2: Run the Script
```bash
cd /Users/anirudhanil/Desktop/agora3/Agora
./scripts/agora-context.sh
```

### Step 3: Copy Output to Cline/Claude
The script will show:
- **AI Summary**: High-level overview of critical issues
- **Top 5 Failures**: Ranked by golden score (#1 is most important)

**Example Output**:
```
📊 AI SUMMARY
=============
The most critical issues are unknown errors in the Order Processing 
Workflow and Validate Order components.

🔥 TOP FAILURES (Ranked by Golden Score)
==========================================
#1 Order Processing Workflow.flow
   Error: Unknown error
   Time: 2026-01-30T09:22:11.440655Z

#2 Validate Order.exec
   Error: Unknown error
   Time: 2026-01-30T09:22:11.441845Z
   
...

💡 TIP: Focus on #1 first - it has the highest golden score!
```

---

## 🤖 How to Use with AI Coding Assistants

### With Cline
1. Run `./scripts/agora-context.sh`
2. Copy the output
3. In Cline chat: "Here's the AI context for my project: [paste output]. Please help me debug issue #1"

### With Claude Desktop
1. Same as above
2. Claude will understand the ranked failures and focus on the most critical ones

### With Cursor
1. Create `.cursorrules` file (see integration plan)
2. Run the script when debugging
3. Cursor will use the context automatically

---

## 📋 Example Workflow

```bash
# 1. Get AI context
./scripts/agora-context.sh

# Output shows:
# #1 Order Processing Workflow - Unknown error (MOST CRITICAL)
# #2 Validate Order - Unknown error
# #3 ContentPipeline - Unknown error

# 2. Tell Cline/Claude:
"I have 3 critical errors. The AI ranked 'Order Processing Workflow' 
as #1. Can you help me investigate this error first?"

# 3. Cline/Claude will:
# - Focus on the most important issue
# - Understand the context
# - Provide targeted debugging help
```

---

## 🎯 Why This Works

**Before**: You manually copy-paste random errors to Cline
**After**: AI pre-ranks errors by importance, you share the top ones

**Benefits**:
- ✅ Cline/Claude focuses on what matters
- ✅ Faster debugging (start with #1)
- ✅ Better context (AI summary included)
- ✅ No manual ranking needed

---

## 🔧 Advanced: MCP Server (Optional)

For automatic integration with Cline/Claude, see the full integration plan for setting up an MCP server. This allows Cline/Claude to call the Context Prime endpoint directly without you running scripts.

---

## ✅ You're Ready!

The golden score integration is now usable with your AI coding tools. Just run the script and share the output with Cline/Claude for smarter debugging! 🎉
