# Agora Hackathon - Files to Copy

## Quick Transfer (Automated)

```bash
# 1. Create your hackathon repo
mkdir ~/my-hackathon-project

# 2. Run the transfer script
bash transfer_to_hackathon.sh ~/my-hackathon-project

# 3. Done!
```

## Manual Transfer (File-by-File)

If you prefer to copy files manually:

### Core Files (Required)

```
agora/
├── __init__.py              # Core framework
├── engine.py                # Event-driven execution engine
├── builder.py               # Workflow builder
├── registry.py              # Node registry
├── inspector.py             # Flow inspection
├── telemetry.py             # Audit logging
├── agora_tracer.py          # OpenTelemetry integration
├── wide_events.py           # Business context enrichment
└── logging_config.py        # Logging configuration
```

### Demo & Examples

```
hackathon_demo.py                              # Main demo (MUST HAVE!)
examples/minimal_local_example.py              # Minimal example
examples/local_usage_without_platform.py       # All usage options
```

### Configuration Files to Create

**requirements.txt:**
```
openai>=1.0.0
traceloop-sdk>=0.24.0
opentelemetry-api>=1.20.0
opentelemetry-sdk>=1.20.0
opentelemetry-instrumentation-openai>=0.24.0
```

**.gitignore:**
```
__pycache__/
*.py[cod]
venv/
env/
*.jsonl
.env
*_credentials*
```

## What NOT to Copy

❌ **platform/** - Monitoring platform (web UI, backend)
❌ **test_*.py** - Test files
❌ **colab_*.py** - Google Colab examples
❌ **.git/** - Git history
❌ **examples/Milvus/** - Specific integrations

## Minimal Installation

If you just want the absolute minimum:

```
your-hackathon-repo/
├── agora/
│   ├── __init__.py
│   ├── engine.py
│   ├── builder.py
│   └── registry.py
├── hackathon_demo.py
└── requirements.txt (just: openai)
```

This gives you pure workflow orchestration without any telemetry.

## Full Installation (Recommended)

Copy all files listed in "Core Files" section above. This gives you:
- ✅ Full workflow orchestration
- ✅ Local telemetry (console + file)
- ✅ LLM auto-tracing
- ✅ Wide events / business context
- ✅ Comprehensive logging

## Quick Setup Commands

```bash
# In your new repo
pip install -r requirements.txt
export OPENAI_API_KEY='sk-...'
python hackathon_demo.py
```

## File Sizes (Reference)

```
Total size of core files: ~150KB
hackathon_demo.py: ~15KB
Full agora/ directory: ~200KB
```

Very lightweight! Perfect for hackathons. 🚀
