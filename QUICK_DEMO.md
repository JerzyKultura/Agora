# Quick Demo: Agora with API Key

Get started with Agora workflows and cloud telemetry in 2 minutes.

---

## Step 1: Deploy Your Platform

```bash
# Build the project
npm run build

# Click "Publish" in your deployment tool
```

Your platform is live at: `https://your-url.com`

---

## Step 2: Get Your API Key

1. **Open your deployed platform** (https://your-url.com)
2. **Sign up** with an email and password
3. **Go to Settings** (click Settings in the sidebar)
4. **Click "New API Key"**
   - Enter a name like "Demo Workflow"
   - Click "Generate"
5. **Copy the key** (starts with `agora_`)
   - ⚠️ Save it now! You won't see it again

---

## Step 3: Run the Demo Script

### Install Agora

```bash
pip install git+https://github.com/yourusername/Agora.git
```

### Set Your API Key

```bash
export AGORA_API_KEY="agora_your_key_here"
```

### Run the Demo

```bash
python demo_workflow.py
```

**What You'll See:**
```
============================================================
AGORA WORKFLOW DEMO
============================================================

🚀 Starting demo workflow...
  ✓ Processed item #1
  ✓ Processed item #2
  ✓ Processed item #3
  ✓ Processed item #4
  ✓ Processed item #5

📊 Analyzing results...
  Total items processed: 5
  Results: 5 items

✅ Workflow completed successfully!
  Final count: 5
  Analysis: {'total': 5, 'status': 'success'}

============================================================
✓ Telemetry sent to Agora Cloud!
View your workflow execution at:
https://your-platform.com/monitoring
============================================================
```

---

## Step 4: View Telemetry in Platform

1. Go back to your platform: `https://your-url.com`
2. Click **"Monitoring"** in the sidebar (or create a project first)
3. You should see:
   - Execution traces
   - Node timing
   - Success/error status
   - Full workflow timeline

---

## What the Demo Does

The `demo_workflow.py` script:

✅ **Initializes tracing** with your API key
✅ **Creates 5 nodes** using `@agora_node` decorator:
   - Start → ProcessData → AnalyzeResults → Finish
✅ **Loops through ProcessData** 5 times
✅ **Sends telemetry** to your platform
✅ **Saves local backup** to `demo_traces.jsonl`

---

## Testing Without API Key

Want to test locally first?

```bash
# Don't set AGORA_API_KEY
python demo_workflow.py
```

**Output:**
```
⚠️  No AGORA_API_KEY found!
Set it with: export AGORA_API_KEY='agora_xxxxx'

Running in local mode (no cloud sync)...
```

Telemetry saves to `demo_traces.jsonl` instead of the cloud.

---

## Next Steps

### Customize the Demo

Edit `demo_workflow.py` to:
- Add more nodes
- Change the loop count
- Add error handling
- Process real data

### Integrate with Your Code

Copy the pattern into your own scripts:

```python
import os
from agora.agora_tracer import init_traceloop, agora_node

# Initialize with your API key
init_traceloop(
    app_name="my_app",
    api_key=os.environ["AGORA_API_KEY"]
)

# Create nodes
@agora_node(name="MyNode")
async def my_node(shared):
    # Your logic here
    return "next"

# Build and run flow
# ...
```

### Add OpenAI Integration

Want to track LLM calls? Add OpenAI:

```python
from openai import OpenAI

client = OpenAI()

@agora_node(name="LLMCall")
async def llm_call(shared):
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    shared["response"] = response.choices[0].message.content
    return "done"
```

Traceloop will automatically instrument OpenAI calls!

---

## Troubleshooting

### "Module not found: agora"
```bash
pip install --force-reinstall git+https://github.com/yourusername/Agora.git
```

### "API key invalid"
- Check you copied the full key (starts with `agora_`)
- Make sure it's set: `echo $AGORA_API_KEY`
- Generate a new key in Settings if needed

### "No executions showing in platform"
- Check the Monitoring page (might need to create a project first)
- Check browser console for errors
- Verify API key is not deleted/expired

### "Workflow loops forever"
- Make sure your nodes return the correct action strings
- Check that routing matches: `node - "action" >> next_node`

---

## Platform Features

Once your workflows are running:

### Dashboard
- Total projects
- Active workflows
- Success rate stats

### Projects
- Create projects to organize workflows
- Track multiple applications

### Monitoring
- Real-time execution traces
- Node-level timing
- Error tracking
- Full execution history

### Settings
- Generate multiple API keys
- Track key usage
- Revoke keys
- View last used date

---

## Questions?

Check these files:
- `TEST_AGORA_DECORATORS.md` - Full testing guide
- `README.md` - Framework documentation
- `examples/` - More workflow examples
