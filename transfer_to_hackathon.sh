#!/bin/bash
# =============================================================================
# AGORA HACKATHON TRANSFER SCRIPT
# =============================================================================
# This script copies the core Agora files needed for local/offline use
# (no platform components)
#
# Usage:
#   1. Create your new hackathon repo directory
#   2. Run: bash transfer_to_hackathon.sh /path/to/your/new/repo
# =============================================================================

if [ -z "$1" ]; then
    echo "Usage: bash transfer_to_hackathon.sh /path/to/your/hackathon/repo"
    exit 1
fi

DEST_DIR="$1"
SOURCE_DIR="/home/user/Agora"

echo "========================================================================"
echo "TRANSFERRING AGORA CORE FILES TO: $DEST_DIR"
echo "========================================================================"
echo ""

# Create destination directory
mkdir -p "$DEST_DIR"

# =============================================================================
# 1. COPY CORE AGORA LIBRARY
# =============================================================================

echo "📦 Copying core Agora library..."
mkdir -p "$DEST_DIR/agora"

# Core framework files (required)
cp "$SOURCE_DIR/agora/__init__.py" "$DEST_DIR/agora/"
cp "$SOURCE_DIR/agora/engine.py" "$DEST_DIR/agora/"
cp "$SOURCE_DIR/agora/builder.py" "$DEST_DIR/agora/"
cp "$SOURCE_DIR/agora/registry.py" "$DEST_DIR/agora/"
cp "$SOURCE_DIR/agora/inspector.py" "$DEST_DIR/agora/"

# Telemetry files (for local logging)
cp "$SOURCE_DIR/agora/telemetry.py" "$DEST_DIR/agora/"
cp "$SOURCE_DIR/agora/agora_tracer.py" "$DEST_DIR/agora/"
cp "$SOURCE_DIR/agora/wide_events.py" "$DEST_DIR/agora/"
cp "$SOURCE_DIR/agora/logging_config.py" "$DEST_DIR/agora/"

# Optional: Supabase uploader (only if you want cloud upload capability)
# Uncomment if needed:
# cp "$SOURCE_DIR/agora/supabase_uploader.py" "$DEST_DIR/agora/"

echo "   ✅ Core Agora library copied"

# =============================================================================
# 2. COPY HACKATHON DEMO
# =============================================================================

echo "📦 Copying hackathon demo..."
cp "$SOURCE_DIR/hackathon_demo.py" "$DEST_DIR/"
echo "   ✅ Hackathon demo copied"

# =============================================================================
# 3. COPY USEFUL EXAMPLES (Optional)
# =============================================================================

echo "📦 Copying examples..."
mkdir -p "$DEST_DIR/examples"

cp "$SOURCE_DIR/examples/minimal_local_example.py" "$DEST_DIR/examples/" 2>/dev/null || echo "   ⚠️  minimal_local_example.py not found"
cp "$SOURCE_DIR/examples/local_usage_without_platform.py" "$DEST_DIR/examples/" 2>/dev/null || echo "   ⚠️  local_usage_without_platform.py not found"

echo "   ✅ Examples copied"

# =============================================================================
# 4. CREATE REQUIREMENTS.TXT
# =============================================================================

echo "📦 Creating requirements.txt..."

cat > "$DEST_DIR/requirements.txt" << 'EOF'
# Core dependencies for Agora (local/offline use)
openai>=1.0.0
traceloop-sdk>=0.24.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-openai>=0.24.0

# Optional: For Supabase upload (if you want cloud features)
# supabase>=2.0.0
# python-dotenv>=1.0.0
EOF

echo "   ✅ requirements.txt created"

# =============================================================================
# 5. CREATE README FOR HACKATHON
# =============================================================================

echo "📦 Creating README.md..."

cat > "$DEST_DIR/README.md" << 'EOF'
# Agora - Hackathon Edition

Lightweight AI workflow orchestration with local telemetry (no platform needed).

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set your OpenAI API key
export OPENAI_API_KEY='sk-...'

# 3. Run the demo
python hackathon_demo.py
```

## What's Included

- **agora/** - Core workflow orchestration engine
- **hackathon_demo.py** - Full-featured demo showcasing all capabilities
- **examples/** - Additional usage examples

## Features

✅ Workflow orchestration with async nodes
✅ Conditional routing
✅ Retry logic and error handling
✅ Batch processing
✅ Wide events (business context)
✅ Local telemetry (console + file)
✅ LLM auto-tracing

## Usage

### Basic Workflow

```python
from agora import AsyncNode, AsyncFlow
from agora.agora_tracer import init_agora
import asyncio

# Initialize with local telemetry
init_agora(
    app_name="my-app",
    export_to_console=True,
    export_to_file="traces.jsonl",
    enable_cloud_upload=False
)

# Define your node
class MyNode(AsyncNode):
    async def exec_async(self, prep_res):
        # Your logic here
        return "result"

# Build workflow
flow = AsyncFlow()
flow.start(MyNode())

# Run
result = asyncio.run(flow.run({}))
```

### Add Business Context

```python
from agora.wide_events import set_business_context

set_business_context(
    user_id="user_123",
    custom={"project": "hackathon"}
)
```

## Telemetry Options

**Console only:**
```python
init_agora(app_name="my-app", export_to_console=True, enable_cloud_upload=False)
```

**File only:**
```python
init_agora(app_name="my-app", export_to_file="traces.jsonl", enable_cloud_upload=False)
```

**Both:**
```python
init_agora(app_name="my-app", export_to_console=True, export_to_file="traces.jsonl", enable_cloud_upload=False)
```

**None (pure workflows):**
```python
from agora import AsyncNode, AsyncFlow
# Just use the workflow engine, no init_agora() needed
```

## Querying Telemetry

```bash
# View all traces
cat traces.jsonl | jq

# Get token usage
cat traces.jsonl | jq '.attributes."llm.usage.total_tokens"' | grep -v null

# Get costs
cat traces.jsonl | jq '.attributes."traceloop.cost.usd"' | grep -v null
```

## Source

This is a lightweight distribution of [Agora](https://github.com/JerzyKultura/Agora) for hackathon use.
EOF

echo "   ✅ README.md created"

# =============================================================================
# 6. CREATE .gitignore
# =============================================================================

echo "📦 Creating .gitignore..."

cat > "$DEST_DIR/.gitignore" << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
*.egg-info/
dist/
build/

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# Telemetry files
*.jsonl
traces.json
audit_trail.json

# Credentials
.env
.env.local
*_credentials*
EOF

echo "   ✅ .gitignore created"

# =============================================================================
# 7. SUMMARY
# =============================================================================

echo ""
echo "========================================================================"
echo "✅ TRANSFER COMPLETE"
echo "========================================================================"
echo ""
echo "Files copied to: $DEST_DIR"
echo ""
echo "Structure:"
echo "  $DEST_DIR/"
echo "  ├── agora/                    # Core library"
echo "  │   ├── __init__.py"
echo "  │   ├── engine.py"
echo "  │   ├── agora_tracer.py"
echo "  │   ├── wide_events.py"
echo "  │   └── ..."
echo "  ├── hackathon_demo.py         # Ready-to-run demo"
echo "  ├── examples/                 # Additional examples"
echo "  ├── requirements.txt          # Dependencies"
echo "  ├── README.md                 # Documentation"
echo "  └── .gitignore"
echo ""
echo "Next steps:"
echo "  1. cd $DEST_DIR"
echo "  2. pip install -r requirements.txt"
echo "  3. export OPENAI_API_KEY='sk-...'"
echo "  4. python hackathon_demo.py"
echo ""
echo "Happy hacking! 🚀"
echo "========================================================================"
