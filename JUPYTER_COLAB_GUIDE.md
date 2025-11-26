# Jupyter/Colab Guide for Agora Workflows

## The Event Loop Error Explained

### ❌ Error You're Seeing
```
RuntimeError: asyncio.run() cannot be called from a running event loop
```

### 🤔 What This Means
- **Jupyter/Colab notebooks** already have an asyncio event loop running
- `asyncio.run()` tries to create a **new** event loop
- Python doesn't allow nested/overlapping event loops
- Result: RuntimeError

### ✅ The Fix

**In Jupyter/Colab notebooks, use `await` directly:**

```python
# ❌ WRONG - Don't use this in notebooks
asyncio.run(my_async_function())

# ✅ CORRECT - Use this in notebooks
await my_async_function()
```

## Quick Start for Colab

### Cell 1: Install Packages
```python
!pip install openai traceloop-sdk supabase
```

### Cell 2: Import and Configure
```python
import os
from openai import OpenAI
from agora.agora_tracer import init_traceloop, TracedAsyncFlow, agora_node

# Set your API keys
os.environ["OPENAI_API_KEY"] = "sk-..."
os.environ["VITE_SUPABASE_URL"] = "https://xxxxx.supabase.co"
os.environ["VITE_SUPABASE_ANON_KEY"] = "eyJhbGci..."

# Initialize tracing
init_traceloop(
    app_name="my_notebook",
    export_to_console=True,
    enable_cloud_upload=True,
    project_name="Colab Demo"
)
```

### Cell 3: Define Your Workflow
```python
@agora_node(name="ProcessData")
async def process_data(shared):
    print("Processing...")
    shared["result"] = "done"
    return None
```

### Cell 4: Run Your Workflow
```python
# Create and configure flow
flow = TracedAsyncFlow("MyWorkflow")
flow.start(process_data)

# ✅ Use await in notebooks (not asyncio.run!)
await flow.run_async({})
```

## Complete Working Example

```python
# Cell 1: Setup
!pip install openai traceloop-sdk supabase

# Cell 2: Configure
import os
from agora.agora_tracer import init_traceloop, TracedAsyncFlow, agora_node

os.environ["VITE_SUPABASE_URL"] = "https://your-project.supabase.co"
os.environ["VITE_SUPABASE_ANON_KEY"] = "your-anon-key"

init_traceloop(
    app_name="demo",
    enable_cloud_upload=True,
    project_name="Demo"
)

# Cell 3: Define nodes
@agora_node(name="Start")
async def start_node(shared):
    print("Starting...")
    shared["count"] = 0
    return "process"

@agora_node(name="Process")
async def process_node(shared):
    shared["count"] += 1
    print(f"Count: {shared['count']}")
    if shared["count"] >= 3:
        return "finish"
    return "process"

@agora_node(name="Finish")
async def finish_node(shared):
    print("Done!")
    return None

# Cell 4: Run workflow
flow = TracedAsyncFlow("CounterWorkflow")
flow.start(start_node)

start_node - "process" >> process_node
process_node - "process" >> process_node
process_node - "finish" >> finish_node

# ✅ IMPORTANT: Use 'await' in notebooks!
await flow.run_async({})

print("\n✅ Check your monitoring page for telemetry!")
```

## Regular Python Scripts vs Notebooks

### Python Script (.py file)
```python
# demo.py
import asyncio

async def main():
    # your async code
    pass

# ✅ Use asyncio.run() in scripts
if __name__ == "__main__":
    asyncio.run(main())
```

### Jupyter/Colab Notebook
```python
# In a notebook cell

async def main():
    # your async code
    pass

# ✅ Use await in notebooks
await main()
```

## Common Mistakes

### ❌ Mistake 1: Using asyncio.run() in Notebooks
```python
# DON'T DO THIS in Colab/Jupyter
asyncio.run(my_function())  # ❌ RuntimeError!
```

### ✅ Fix: Use await
```python
# DO THIS instead
await my_function()  # ✅ Works!
```

### ❌ Mistake 2: Forgetting async
```python
# If you see "object is not awaitable"
def my_function():  # ❌ Missing 'async'
    pass

await my_function()  # Error: not awaitable
```

### ✅ Fix: Add async
```python
async def my_function():  # ✅ Now it's async
    pass

await my_function()  # ✅ Works!
```

## Testing Your Setup

Run this in a Colab cell to verify everything works:

```python
# Test cell - should complete without errors

import asyncio
from agora.agora_tracer import init_traceloop, TracedAsyncFlow, agora_node

init_traceloop(app_name="test", enable_cloud_upload=False)

@agora_node(name="TestNode")
async def test_node(shared):
    print("✅ Test successful!")
    return None

flow = TracedAsyncFlow("TestFlow")
flow.start(test_node)

# Use await in notebooks!
await flow.run_async({})

print("✅ If you see this, everything is working!")
```

## Updated colab_demo.py

The `colab_demo.py` file has been fixed to use `await` instead of `asyncio.run()`:

```python
# ✅ Fixed - now works in Colab
await run_chatbot()
```

Just copy the cells from `colab_demo.py` into your Colab notebook and run them!

## Summary

| Environment | Use This |
|-------------|----------|
| **Jupyter/Colab** | `await function()` |
| **Python Script** | `asyncio.run(function())` |
| **Already in async function** | `await function()` |

The key rule: **Never use `asyncio.run()` inside an existing event loop!**
