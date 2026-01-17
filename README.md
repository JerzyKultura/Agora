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
