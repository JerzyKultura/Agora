# How Agora Telemetry Works Across Different Environments

## The Short Answer

**YES!** You can use your Agora SDK from **anywhere** (your PC, Colab, a different computer, a server) and see all the chat messages and telemetry data on your localhost dashboard.

## How It Works

Your Agora setup uses a **centralized remote database** (Supabase Cloud), which means:

```
Any Computer → Agora SDK → Supabase Cloud (remote DB)
                                ↓
                    Your Localhost Dashboard reads from Supabase Cloud
```

## Concrete Scenarios

### Scenario 1: Running LLM Calls from Google Colab

```python
# On Google Colab (running in Google's cloud)
from agora.agora_tracer import init_agora
from traceloop.sdk import Traceloop
from openai import OpenAI

# Initialize telemetry - points to YOUR Supabase cloud
Traceloop.init(app_name="my-colab-app", disable_batch=True)
init_agora(
    app_name="my-colab-app",
    enable_cloud_upload=True  # Sends to Supabase!
)

# Make LLM calls
client = OpenAI(api_key="sk-...")
response = client.chat.completions.create(
    model="gpt-4",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is the capital of France?"}
    ]
)
```

**What happens:**
1. Colab runs the LLM call
2. Traceloop SDK captures the chat messages (system, user, assistant)
3. Agora SDK sends the telemetry to **Supabase Cloud** (https://tfueafatqxspitjcbukq.supabase.co)
4. You open **http://localhost:5173/monitoring** on your laptop
5. The dashboard reads from the **same Supabase Cloud**
6. **You see the Colab chat messages instantly!** 🎉

### Scenario 2: Running from a Different PC

```python
# On your friend's computer / work laptop / any other machine
from agora.agora_tracer import init_agora

# Same Supabase credentials
init_agora(
    app_name="remote-pc-app",
    enable_cloud_upload=True
)

# Run LLM calls...
```

**What happens:**
- Remote PC → Supabase Cloud → Your localhost dashboard
- All chat messages, tokens, costs appear in your dashboard

### Scenario 3: Multiple Environments Simultaneously

```
Your Laptop (running workflow) → Supabase Cloud ↘
Colab (running chatbot)        → Supabase Cloud → Your localhost:5173/monitoring
Friend's PC (testing)          → Supabase Cloud ↗
```

**All three environments write to the same database, and you see everything in one dashboard!**

## Why This Works: Supabase is Remote

The key difference from a purely local setup:

### ❌ Local Setup (NOT your case)
```
Your PC: SQLite DB → localhost dashboard
Colab: ⚠️ Can't reach your SQLite! Needs ngrok/tunnel
```

### ✅ Your Agora Setup (Remote Supabase)
```
Your PC   → Supabase Cloud ↘
Colab     → Supabase Cloud → localhost dashboard
Other PC  → Supabase Cloud ↗
```

Supabase is **hosted in the cloud** with a public URL, so:
- ✅ Any machine can reach it (no tunnels needed)
- ✅ All data is centralized
- ✅ Your localhost dashboard just reads from the cloud
- ✅ Historical data is permanent

## What You'll See in the Monitoring Dashboard

When you open **http://localhost:5173/monitoring**:

### Traces Tab (shows chat messages!)
Click any trace → Select the "openai.chat" span → See tabs:

**Prompt Tab:**
```
SYSTEM
You are a helpful assistant.

USER
What is the capital of France?
```

**Completions Tab:**
```
ASSISTANT
The capital of France is Paris.
```

**LLM Data Tab:**
```
Model: gpt-4
Provider: openai
Temperature: 0.7
Token Usage: 25 input + 8 output = 33 total
Estimated Cost: $0.000825
```

### Executions Tab (shows metrics!)
- 5 colorful cards: Total Executions, Success, Errors, Tokens, Cost
- Table with all workflow executions
- Filter by status

## The Magic: Environment Variables

All machines need the **same Supabase credentials**:

**.env file (on ANY machine):**
```bash
# Supabase (the remote cloud database)
VITE_SUPABASE_URL=https://tfueafatqxspitjcbukq.supabase.co
VITE_SUPABASE_ANON_KEY=your-supabase-anon-key-here

# OpenAI (for making LLM calls)
OPENAI_API_KEY=sk-proj-your-key-here
```

When you call `init_agora(enable_cloud_upload=True)`:
- The SDK reads these environment variables
- Connects to Supabase Cloud
- Sends all telemetry there

## Testing It Right Now

**Step 1: Run from Colab**
```python
# In a Colab notebook
!pip install traceloop-sdk openai supabase

import os
os.environ["VITE_SUPABASE_URL"] = "https://tfueafatqxspitjcbukq.supabase.co"
os.environ["VITE_SUPABASE_ANON_KEY"] = "your-key"
os.environ["OPENAI_API_KEY"] = "sk-..."

from agora.agora_tracer import init_agora
from traceloop.sdk import Traceloop
from openai import OpenAI

Traceloop.init(app_name="colab-test", disable_batch=True)
init_agora(app_name="colab-test", enable_cloud_upload=True)

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello from Colab!"}]
)
print(response.choices[0].message.content)
```

**Step 2: Open your localhost**
```bash
# On your laptop
cd ~/Agora/platform/frontend
npm run dev
# Open http://localhost:5173/monitoring
```

**Step 3: Check the Traces tab**
- You'll see the trace from Colab!
- Click it → See "Hello from Colab!" in the Prompt tab
- See the AI response in the Completions tab

## Summary Table

| Where Code Runs | Where Data Goes | Where You View It |
|-----------------|----------------|-------------------|
| Your Laptop | Supabase Cloud | localhost:5173 |
| Google Colab | Supabase Cloud | localhost:5173 |
| Friend's PC | Supabase Cloud | localhost:5173 |
| Remote Server | Supabase Cloud | localhost:5173 |

**The pattern:** All code → Same cloud DB → One dashboard

## Important Notes

1. **No tunnels needed** - Supabase is public, so Colab can reach it directly
2. **Historical data** - All telemetry is stored permanently in Supabase
3. **Real-time updates** - The dashboard uses Supabase subscriptions for live updates
4. **Multiple dashboards** - You can open the dashboard from multiple browsers/machines simultaneously (all connected to the same Supabase)

## What If You Want to Share the Dashboard?

Since Supabase is remote, you can:

1. **Deploy the frontend** to Vercel/Netlify
2. **Access from anywhere** with a URL like https://agora-dashboard.vercel.app
3. **See the same data** from any device

But even without deploying, you can:
- Run the frontend on your laptop
- Have friends run LLM code on their machines
- All their telemetry appears in your localhost dashboard!

## The Bottom Line

**Your Agora setup is already configured perfectly for multi-environment use:**

✅ Centralized remote database (Supabase Cloud)
✅ No network configuration needed
✅ Works from anywhere (PC, Colab, servers)
✅ All chat messages captured and visible
✅ Historical data stored permanently
✅ Real-time dashboard updates

Just make sure every environment has the same `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in their `.env` file or environment variables!
