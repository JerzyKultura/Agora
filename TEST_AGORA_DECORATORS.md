# Testing Agora Decorators & API

Complete guide to test your Agora workflow framework with the decorator API.

---

## Quick Start: Simple Test Script

Create a test file to verify the decorator API works:

```python
# test_agora_simple.py
import asyncio
import os
from agora.agora_tracer import (
    TracedAsyncNode,
    TracedAsyncFlow,
    init_traceloop,
    agora_node,
)

# Initialize tracing
init_traceloop(
    app_name="test_decorators",
    export_to_console=True,
    export_to_file="test_traces.jsonl"
)

# Define nodes using @agora_node decorator
@agora_node(name="StartNode")
async def start_node(shared):
    """First node in the flow"""
    print("Starting workflow...")
    shared["counter"] = 0
    return "process"

@agora_node(name="ProcessNode")
async def process_node(shared):
    """Process some data"""
    shared["counter"] += 1
    print(f"Processing step {shared['counter']}")

    if shared["counter"] < 3:
        return "process"  # Loop back
    return "finish"

@agora_node(name="FinishNode")
async def finish_node(shared):
    """Complete the workflow"""
    print(f"Finished after {shared['counter']} steps")
    return None  # End the flow

# Build and run the flow
async def test_decorator_flow():
    """Test the decorator-based workflow"""

    # Create flow
    flow = TracedAsyncFlow("TestDecoratorFlow")
    flow.start(start_node)

    # Define routing
    start_node - "process" >> process_node
    process_node - "process" >> process_node  # Loop
    process_node - "finish" >> finish_node

    # Run
    shared = {}
    await flow.run_async(shared)

    # Print results
    print("\n" + "="*50)
    print("RESULTS:")
    print(f"Counter: {shared['counter']}")
    print("="*50)
    print("\nFlow diagram:")
    print(flow.to_mermaid())

# Run the test
if __name__ == "__main__":
    asyncio.run(test_decorator_flow())
```

Run it:
```bash
cd /tmp/cc-agent/60723596/project
python test_agora_simple.py
```

**Expected Output:**
- Console shows node executions
- Trace file `test_traces.jsonl` is created
- Flow diagram is printed
- Counter reaches 3

---

## Test the Chat Example

The chat example demonstrates both decorator and class-based approaches:

### 1. Setup Environment

```bash
# Install dependencies if needed
pip install openai traceloop-sdk nest_asyncio

# Set your OpenAI API key
export OPENAI_API_KEY="your-key-here"
```

### 2. Run the Chat Example

```bash
cd examples/simple_chat_app
python simple_chat_app.py
```

Or use the notebook version in Google Colab:
- Open `examples/Decorator_chat_example.ipynb`
- Add your OpenAI API key
- Run all cells

### 3. What to Test

**Basic Chat Flow:**
1. Script starts and shows "Chat ready"
2. Type a message
3. Bot responds using GPT-4
4. Type "exit" to quit
5. Summary shows turn count

**Verify Telemetry:**
- Check console output for trace logs
- Look for JSONL file in `/content/chat_telemetry/` (Colab) or local directory
- Each interaction should create traces

**Check Decorator Functionality:**
- `@agora_node` decorated functions work as nodes
- Routing works: "respond" → response_node, "exit" → exit_node
- Shared state persists across nodes (messages array)

---

## Test API Key Integration (Future)

When your platform is deployed, test the API key workflow:

### 1. Generate API Key (via Web UI)

```
1. Login to deployed platform
2. Go to Settings or API Keys page
3. Click "Generate New Key"
4. Copy the key (starts with "agora_")
```

### 2. Use Key in Python Script

```python
import os
os.environ["AGORA_API_KEY"] = "agora_xxxxxxxxxxxxx"

from agora.agora_tracer import init_traceloop, agora_node

# Initialize with API key
init_traceloop(
    app_name="my_app",
    export_to_console=True,
    api_key=os.environ["AGORA_API_KEY"]  # Send traces to platform
)

@agora_node(name="TestNode")
async def test_node(shared):
    print("Testing API key integration")
    return None

# Run and check platform dashboard
```

### 3. Verify in Platform Dashboard

```
1. Go to platform /monitoring page
2. Check for new traces from "my_app"
3. Click on a trace to see node details
4. Verify timing, status, and attributes
```

---

## Testing Checklist

### Core Functionality
- [ ] `@agora_node` decorator creates valid nodes
- [ ] Decorated nodes work with `TracedAsyncFlow`
- [ ] Routing works (action strings)
- [ ] Shared state persists across nodes
- [ ] Loops work (node → same node)
- [ ] Flow ends when node returns None

### Telemetry
- [ ] `init_traceloop()` initializes tracing
- [ ] Console output shows traces
- [ ] JSONL file is created
- [ ] Traces include node names, timing, status
- [ ] OpenAI calls are instrumented (if using)

### Flow Building
- [ ] `flow.start(node)` works
- [ ] `node - "action" >> next_node` syntax works
- [ ] `flow.to_mermaid()` generates diagram
- [ ] Flow executes in correct order

### Async Support
- [ ] `await flow.run_async(shared)` works
- [ ] Async node functions execute properly
- [ ] Shared dict updates are visible to all nodes

### Error Handling
- [ ] Exceptions in nodes are caught and traced
- [ ] Error status appears in traces
- [ ] Flow stops gracefully on error

---

## Common Issues & Solutions

### Issue: "Module not found: agora"
**Solution:**
```bash
pip install --force-reinstall git+https://github.com/yourusername/Agora.git
```

### Issue: "Traceloop already initialized"
**Solution:** This is just a warning, safe to ignore. It means `init_traceloop()` was called twice.

### Issue: OpenAI calls not traced
**Solution:** Make sure you installed `traceloop-sdk`:
```bash
pip install traceloop-sdk
```

### Issue: No JSONL file created
**Solution:** Check the `export_to_file` path exists:
```python
import os
os.makedirs("./traces", exist_ok=True)
init_traceloop(..., export_to_file="./traces/trace.jsonl")
```

### Issue: Decorator node doesn't route
**Solution:** Make sure your function returns a string that matches a routing action:
```python
@agora_node(name="Router")
async def router(shared):
    return "next"  # Must match: node - "next" >> next_node
```

---

## Advanced Testing

### Test with OpenTelemetry Backend

Send traces to Jaeger or another OTLP backend:

```python
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import BatchSpanProcessor

exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
processor = BatchSpanProcessor(exporter)
trace.get_tracer_provider().add_span_processor(processor)
```

### Test Parallel Node Execution

```python
from agora import BatchNode

@agora_node(name="ParallelTask")
async def parallel_task(shared):
    await asyncio.sleep(1)
    return "done"

# Run multiple instances in parallel
batch = BatchNode([parallel_task, parallel_task, parallel_task])
```

### Test Complex Routing

```python
@agora_node(name="Conditional")
async def conditional(shared):
    if shared["value"] > 10:
        return "high"
    elif shared["value"] > 5:
        return "medium"
    else:
        return "low"

# Setup multiple branches
conditional - "high" >> high_handler
conditional - "medium" >> medium_handler
conditional - "low" >> low_handler
```

---

## Next Steps

Once basic tests pass:

1. **Integrate with Platform**
   - Generate API key from deployed web app
   - Configure `init_traceloop()` to send traces to platform
   - Verify traces appear in monitoring dashboard

2. **Test Real Workflows**
   - Replace test nodes with actual business logic
   - Test with real OpenAI API calls
   - Monitor performance and errors

3. **Production Testing**
   - Test with multiple concurrent flows
   - Verify trace storage in Supabase
   - Check dashboard performance with many traces

---

## Questions?

Check these resources:
- `README.md` - Full documentation
- `examples/` - Working examples
- `agora/tracer.py` - Tracer implementation
- `agora/agora_tracer.py` - Decorator implementation
