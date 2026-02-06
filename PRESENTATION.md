# Agora: Build AI Workflows in Minutes

## What is Agora?

**Agora** makes building AI workflows ridiculously simple with just one decorator: `@agora_node`

---

## The Magic: @agora_node Decorator

### Before Agora (Traditional Approach)
```python
# Lots of boilerplate code
class MyNode(BaseNode):
    def __init__(self):
        super().__init__()
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        result = do_something()
        return result
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['result'] = exec_res
        return "default"

# More code to chain nodes...
```

### With Agora (Simple!)
```python
@agora_node(name="MyNode")
async def my_node(shared):
    result = do_something()
    shared['result'] = result
    return "default"
```

**That's it! One decorator, one function.** ✨

---

## Quick Start: 3-Node Workflow

```python
from agora.agora_tracer import agora_node, TracedAsyncFlow, init_agora
import asyncio

init_agora(app_name="My App")

# Step 1: Fetch data
@agora_node(name="Fetch")
async def fetch(shared):
    shared['data'] = [1, 2, 3, 4, 5]
    return "default"

# Step 2: Transform data
@agora_node(name="Transform")
async def transform(shared):
    data = shared['data']
    shared['result'] = [x * 2 for x in data]
    return "default"

# Step 3: Save results
@agora_node(name="Save")
async def save(shared):
    print(f"Saved: {shared['result']}")
    return "default"

# Chain them together
async def main():
    flow = TracedAsyncFlow("ETL Pipeline")
    
    # Define flow: Fetch → Transform → Save
    fetch.successors = {"default": transform}
    transform.successors = {"default": save}
    flow.start_node = fetch
    
    # Run!
    await flow.run_async({})

asyncio.run(main())
```

**Output:**
```
Saved: [2, 4, 6, 8, 10]
```

**Dashboard:** See full visualization at `http://localhost:5173/monitoring`

---

## Real Example: AI Chatbot

```python
from agora.agora_tracer import agora_node, TracedAsyncFlow, init_agora
from openai import AsyncOpenAI
import asyncio

init_agora(app_name="Chatbot")
client = AsyncOpenAI()

# Node 1: Get AI response
@agora_node(name="GetAIResponse")
async def get_ai_response(shared):
    user_msg = shared.get("user_message", "")
    history = shared.get("history", [])
    
    # Build messages
    messages = [{"role": "system", "content": "You are helpful."}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_msg})
    
    # Call OpenAI (tokens tracked automatically!)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=150
    )
    
    shared["ai_response"] = response.choices[0].message.content
    return "default"

# Node 2: Update conversation history
@agora_node(name="UpdateHistory")
async def update_history(shared):
    user_msg = shared.get("user_message", "")
    ai_response = shared.get("ai_response", "")
    history = shared.get("history", [])
    
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": ai_response})
    shared["history"] = history
    shared["response"] = ai_response
    
    return "default"

# Run chatbot
async def main():
    shared = {"history": []}
    
    while True:
        user_input = input("You: ").strip()
        if user_input.lower() in ['quit', 'exit']:
            break
        
        # Create flow
        flow = TracedAsyncFlow("Chat")
        get_ai_response.successors = {"default": update_history}
        flow.start_node = get_ai_response
        
        # Run
        shared["user_message"] = user_input
        await flow.run_async(shared)
        
        # Show response
        print(f"AI:  {shared.get('response', '')}\n")

asyncio.run(main())
```

---

## Key Concepts

### 1. Shared State
A dictionary that passes data between nodes:

```python
@agora_node(name="Step1")
async def step1(shared):
    shared['data'] = "hello"  # Store data
    return "default"

@agora_node(name="Step2")
async def step2(shared):
    data = shared.get('data')  # Retrieve data
    print(data)  # "hello"
    return "default"
```

### 2. Routing
Return different strings to route to different nodes:

```python
@agora_node(name="Router")
async def router(shared):
    amount = shared.get('amount', 0)
    
    if amount > 1000:
        return "vip"  # Go to VIP handler
    else:
        return "standard"  # Go to standard handler

# Set up routes
router.successors = {
    "vip": vip_handler,
    "standard": standard_handler
}
```

### 3. Chaining Nodes
Connect nodes with `successors`:

```python
# Linear chain: A → B → C
node_a.successors = {"default": node_b}
node_b.successors = {"default": node_c}

# Conditional routing: A → [B or C]
node_a.successors = {
    "route1": node_b,
    "route2": node_c
}
```

---

## What You Get Automatically

✅ **Telemetry Tracking** - Every execution logged  
✅ **Performance Metrics** - Duration, success/failure  
✅ **Token Counting** - For LLM calls (OpenAI, Anthropic, etc.)  
✅ **Error Handling** - Built-in retries and fallbacks  
✅ **Workflow Visualization** - Interactive dashboard  
✅ **Debugging Tools** - View input/output, error messages  

---

## Dashboard Features

Access: `http://localhost:5173/monitoring`

### What You See:

📊 **Executions**
- All workflow runs
- Status, duration, timestamp

🔍 **Execution Details**
- Node-by-node breakdown
- Input/output data
- Error messages

📈 **Workflow Graph**
- Visual flow diagram
- Node execution order

⏱️ **Timeline**
- When each node ran
- Performance bottlenecks

💰 **Token Usage**
- LLM token counts
- Cost estimation

---

## Advanced: Error Handling

Add retries and fallbacks:

```python
from agora import AsyncNode

class RobustNode(AsyncNode):
    def __init__(self):
        super().__init__(
            "RobustNode",
            max_retries=3,  # Retry 3 times
            wait=2          # Wait 2 seconds between retries
        )
    
    async def exec_async(self, prep_res):
        # This will retry automatically on failure
        return await risky_operation()
    
    async def exec_fallback_async(self, prep_res, exc):
        # Called after all retries fail
        return "fallback_result"
```

Or with decorator:

```python
@agora_node(name="RobustNode", max_retries=3, wait=2)
async def robust_node(shared):
    # Will retry 3 times with 2 second wait
    result = await risky_operation()
    shared['result'] = result
    return "default"
```

---

## Installation & Setup

### Install
```bash
pip install agora supabase-py opentelemetry-api opentelemetry-sdk
pip install openai  # For LLM support
```

### Configure
```bash
export VITE_SUPABASE_URL=your-url
export VITE_SUPABASE_ANON_KEY=your-key
export OPENAI_API_KEY=sk-...
```

### Initialize
```python
from agora.agora_tracer import init_agora

init_agora(app_name="My Application")
```

---

## Running Examples

All examples in `/examples` directory:

```bash
cd /path/to/Agora

# Simple 3-node workflow
PYTHONPATH=. python3 examples/decorator_example.py

# Interactive chatbot (2 nodes)
PYTHONPATH=. python3 examples/chatbot_2nodes.py

# Single-node chatbot
PYTHONPATH=. python3 examples/chatbot_decorator.py
```

---

## Best Practices

### ✅ DO:
- Use `@agora_node` for simplicity
- Return strings for routing (e.g., `"default"`, `"vip"`, `"error"`)
- Keep nodes focused on one task
- Use descriptive node names
- Store results in `shared` state

### ❌ DON'T:
- Return dictionaries (return strings!)
- Create circular dependencies
- Put too much logic in one node
- Forget to initialize with `init_agora()`

---

## Common Patterns

### ETL Pipeline
```
Fetch → Transform → Validate → Save
```

### Conditional Processing
```
Input → Router → [VIP | Standard] → Output
```

### LLM Chain
```
Prompt → LLM → Parse → Store
```

### Error Recovery
```
Try → [Success → Continue | Fail → Retry → Fallback]
```

---

## Why Agora?

### Before Agora:
- ❌ Complex boilerplate code
- ❌ Manual telemetry setup
- ❌ No built-in monitoring
- ❌ Hard to debug workflows
- ❌ Token tracking requires custom code

### With Agora:
- ✅ One decorator, one function
- ✅ Automatic telemetry
- ✅ Beautiful dashboard included
- ✅ Full debugging tools
- ✅ Token tracking out-of-the-box

---

## Live Demo

**Run this now:**
```bash
cd /Users/anirudhanil/Desktop/agora3/Agora
PYTHONPATH=. python3 examples/chatbot_2nodes.py
```

**Then open:** `http://localhost:5173/monitoring`

**You'll see:**
- Real-time execution tracking
- 2-node workflow visualization
- Token usage (if using OpenAI)
- Complete execution history

---

## Summary

**Agora makes AI workflows simple:**

1. Add `@agora_node` decorator to your functions
2. Chain them with `successors`
3. Run with `TracedAsyncFlow`
4. Monitor everything in the dashboard

**That's it!** 🚀

---

**Questions?**

Check out:
- Full examples in `/examples`
- Complete README.md
- Live dashboard at `localhost:5173/monitoring`
