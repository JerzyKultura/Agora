# Agora Examples

Simple, working examples to get you started with Agora.

## Running Examples

All examples must be run with `PYTHONPATH=.` from the Agora root directory:

```bash
cd /path/to/Agora
PYTHONPATH=. python3 examples/simple_example.py
```

## Available Examples

### 1. `simple_example.py` - Hello World
The absolute simplest Agora example. Single node that greets a user.

**Run:**
```bash
PYTHONPATH=. python3 examples/simple_example.py
```

**What it shows:**
- Creating a basic `AsyncNode`
- Running a single node
- Passing data to nodes

---

### 2. `basic_workflow.py` - 3-Node Pipeline
Simple ETL workflow: Fetch → Transform → Save

**Run:**
```bash
PYTHONPATH=. python3 examples/basic_workflow.py
```

**What it shows:**
- Chaining multiple nodes
- Using `AsyncFlow` for orchestration
- Passing data between nodes via `shared` state
- Using `post_async` to update shared state

---

### 3. `conditional_routing.py` - Dynamic Routing
Routes requests to different handlers based on amount.

**Run:**
```bash
PYTHONPATH=. python3 examples/conditional_routing.py
```

**What it shows:**
- Conditional routing with `successors`
- Multiple execution paths
- Returning actions from `exec_async`
- Business logic-based routing

---

### 4. `error_handling.py` - Retries & Fallbacks
Demonstrates retry logic and fallback mechanisms.

**Run:**
```bash
PYTHONPATH=. python3 examples/error_handling.py
```

**What it shows:**
- Automatic retries with `max_retries`
- Wait time between retries with `wait`
- Fallback logic with `exec_fallback_async`
- Graceful error handling

---

### 5. `openai_example.py` - LLM Integration
Uses OpenAI API to generate and summarize stories.

**Setup:**
```bash
pip install openai
export OPENAI_API_KEY=sk-your-key-here
```

**Run:**
```bash
PYTHONPATH=. python3 examples/openai_example.py
```

**What it shows:**
- OpenAI API integration
- Async API calls
- Token usage tracking
- Error handling for API failures
- Mock responses when API unavailable

---

### 6. `comprehensive_workflow_demo.py` - Full E-commerce Flow
Complete order processing system with 7 nodes.

**Run:**
```bash
PYTHONPATH=. python3 comprehensive_workflow_demo.py
```

**What it shows:**
- Complex multi-node workflows
- Multiple routing paths
- Inventory checks
- Payment processing
- Error handling and retries
- Real-world business logic

---

## Key Patterns

### Pattern 1: Single Node
```python
class MyNode(AsyncNode):
    async def prep_async(self, shared):
        return shared  # Pass shared data to exec
    
    async def exec_async(self, prep_res):
        # Your logic here
        return result
```

### Pattern 2: Chained Nodes
```python
node1.successors = {"default": node2}
node2.successors = {"default": node3}

flow = AsyncFlow("My Flow", start=node1)
await flow.run_async({})
```

### Pattern 3: Conditional Routing
```python
class Router(AsyncNode):
    async def exec_async(self, prep_res):
        if condition:
            return "route_a"
        else:
            return "route_b"

router.successors = {
    "route_a": node_a,
    "route_b": node_b
}
```

### Pattern 4: Sharing Data Between Nodes
```python
class Node1(AsyncNode):
    async def exec_async(self, prep_res):
        return {"data": "value"}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared.update(exec_res)  # Store for next node
        return "default"

class Node2(AsyncNode):
    async def prep_async(self, shared):
        return shared  # Get data from Node1
    
    async def exec_async(self, prep_res):
        data = prep_res.get("data")  # Use it!
        return f"Got: {data}"
```

## Telemetry

All examples automatically track:
- Node execution times
- Success/failure rates
- Retry attempts
- Token usage (for LLM calls)
- Business context

View at: `http://localhost:5173/monitoring`

## Troubleshooting

**Import Error: No module named 'agora'**
- Make sure to run with `PYTHONPATH=.` from the Agora root directory

**OpenAI API Error**
- Install: `pip install openai`
- Set key: `export OPENAI_API_KEY=sk-...`

**AttributeError: 'NoneType' object has no attribute 'get'**
- Add `prep_async` method that returns `shared`
- Or handle None in `exec_async`

## Next Steps

1. Start with `simple_example.py`
2. Try `basic_workflow.py` to see chaining
3. Explore `conditional_routing.py` for routing
4. Check `comprehensive_workflow_demo.py` for a real-world example
5. Build your own workflow!

For full documentation, see the main [README.md](../README.md)
