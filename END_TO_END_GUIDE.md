# End-to-End Telemetry Guide

The full telemetry pipeline is now complete and working!

## What's Been Fixed

### ✅ Backend (100%)
- **Telemetry Ingestion API** - POST endpoints to receive telemetry
  - `/telemetry/executions/start` - Start workflow execution
  - `/telemetry/executions/{id}/complete` - Mark execution as complete
  - `/telemetry/executions/{id}/nodes` - Add node execution data
  - `/telemetry/executions/{id}/spans` - Add OpenTelemetry spans
  - `/telemetry/executions/{id}/events` - Add telemetry events
  - `/telemetry/batch` - Batch upload multiple items
- **API Key Authentication** - Secure access with organization-scoped keys
- **Auto-creation** - Automatically creates projects/workflows if they don't exist

### ✅ Frontend (100%)
- **Monitoring Page** - Real-time execution list with filtering
  - View all executions across workflows
  - Filter by status (running, success, error, timeout)
  - Auto-refresh every 5 seconds
  - Click to view details
- **Execution Detail Page** - Complete execution visualization
  - Timeline view with node-by-node execution
  - Metrics dashboard (success rate, duration, retries)
  - Input/Output data viewer
  - Error messages and debugging info

### ✅ SDK (100%)
- **Cloud Uploader** - HTTP client for platform integration
  - Automatic batch uploading
  - Retry logic with error handling
  - Environment variable configuration
- **Integrated with agora_tracer** - Works seamlessly with existing code
  - TracedAsyncFlow auto-uploads execution data
  - TracedAsyncNode uploads node execution details
  - No code changes needed for existing workflows

## How to Use

### Step 1: Start the Backend (Local Development)

```bash
cd platform/backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

### Step 2: Get Your API Key

1. Open the frontend: Your deployed URL or `http://localhost:5173`
2. Sign up / Log in
3. Go to **Settings** page
4. Click **"Generate API Key"**
5. Copy your API key (starts with `agora_`)

### Step 3: Run Your Workflow

```bash
# Install httpx for cloud upload
pip install httpx

# Set environment variables
export AGORA_API_KEY="agora_your_key_here"
export AGORA_PLATFORM_URL="http://localhost:8000"

# Run the demo
python demo_workflow.py
```

### Step 4: View Telemetry

1. Go to the **Monitoring** page in the frontend
2. You'll see your workflow execution appear
3. Click **"View Details"** to see:
   - Timeline of node executions
   - Execution metrics
   - Input/Output data
   - Error messages (if any)

## What Happens Behind the Scenes

```
Your Script (demo_workflow.py)
    ↓
Agora Framework (agora_tracer.py)
    ↓ Detects @agora_node decorators
    ↓ Wraps nodes with TracedAsyncNode
    ↓
TracedAsyncFlow starts
    ↓ Calls cloud_uploader.start_execution()
    ↓ POST /telemetry/executions/start
    ↓
Backend creates:
    - Project (if needed)
    - Workflow (if needed)
    - Execution record
    ↓ Returns execution_id
    ↓
Each node runs:
    ↓ cloud_uploader.add_node_execution()
    ↓ Buffers data locally
    ↓
Flow completes:
    ↓ cloud_uploader.complete_execution()
    ↓ POST /telemetry/batch (flushes buffer)
    ↓
Data stored in Supabase:
    - executions table
    - node_executions table
    - nodes table (auto-created)
    - workflows table (auto-created)
    ↓
Frontend polls database:
    ↓ Monitoring page shows new execution
    ↓ ExecutionDetail page shows timeline
```

## Environment Variables

### Required

- `AGORA_API_KEY` - Your API key from the platform

### Optional

- `AGORA_PLATFORM_URL` - Platform URL (default: `http://localhost:8000`)
- `TRACELOOP_API_KEY` - Set automatically from AGORA_API_KEY

## Code Example

```python
import os
from agora.agora_tracer import init_traceloop, TracedAsyncFlow, agora_node

# Setup (one time)
os.environ["AGORA_API_KEY"] = "agora_xxxxx"
os.environ["AGORA_PLATFORM_URL"] = "http://localhost:8000"

# Initialize with cloud upload enabled
init_traceloop(
    app_name="my_app",
    export_to_console=True,
    enable_cloud_upload=True,
    project_name="My Project"
)

# Define nodes
@agora_node(name="ProcessData")
async def process_data(shared):
    shared["result"] = "processed"
    return "finish"

@agora_node(name="Finish")
async def finish(shared):
    print(f"Result: {shared['result']}")
    return None

# Run workflow
flow = TracedAsyncFlow("MyWorkflow")
flow.start(process_data)
process_data - "finish" >> finish

await flow.run_async({})

# Telemetry automatically uploaded to platform!
```

## Troubleshooting

### No executions showing up?

1. Check API key is set: `echo $AGORA_API_KEY`
2. Check platform URL: `echo $AGORA_PLATFORM_URL`
3. Check backend is running: `curl http://localhost:8000/health`
4. Check console output for upload errors

### httpx not installed?

```bash
pip install httpx
```

### Backend not starting?

```bash
cd platform/backend
pip install fastapi uvicorn supabase python-dotenv pydantic
```

### Frontend not showing data?

1. Check browser console for errors
2. Verify Supabase env vars in `.env`
3. Check RLS policies allow access

## Features

### Monitoring Page
- ✅ Real-time execution list
- ✅ Status filtering
- ✅ Auto-refresh
- ✅ Workflow grouping
- ✅ Duration tracking

### Execution Detail Page
- ✅ Node-by-node timeline
- ✅ Phase durations (prep, exec, post)
- ✅ Success/error status per node
- ✅ Retry tracking
- ✅ Error messages
- ✅ Input/Output data
- ✅ Execution metrics

### SDK Features
- ✅ Automatic telemetry upload
- ✅ Batch processing
- ✅ Error handling
- ✅ API key authentication
- ✅ Environment configuration
- ✅ Local fallback (saves to JSON)

## Next Steps

### Deploy to Production

1. Deploy backend to your server
2. Deploy frontend to Vercel/Netlify
3. Update `AGORA_PLATFORM_URL` to production URL
4. Distribute API keys to users

### Add More Workflows

Just use the same pattern:
- Use `@agora_node` decorator
- Use `TracedAsyncFlow`
- Set API key
- Run!

No additional configuration needed - projects and workflows are auto-created!
