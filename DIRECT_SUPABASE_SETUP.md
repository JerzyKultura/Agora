# Direct Supabase Telemetry Setup

## ✅ Fixed Issues

1. **`init_traceloop()` now accepts `enable_cloud_upload` parameter** - The function signature has been updated
2. **Telemetry goes directly to Supabase** - No intermediate backend API needed!
3. **Uses the deployed website's database** - Same Supabase instance as your frontend

## How It Works

```
Your Python Script
    ↓
agora_tracer.py (with enable_cloud_upload=True)
    ↓
SupabaseUploader (supabase_uploader.py)
    ↓
Direct INSERT to Supabase database
    ↓
Frontend reads from same database
    ↓
You see telemetry in Monitoring page!
```

## Setup Steps

### 1. Install Required Package

```bash
pip install supabase
```

### 2. Get Your Supabase Credentials

From your `.env` file in the project root:

```bash
cat .env
```

You'll see:
```
VITE_SUPABASE_URL=https://your-project.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

### 3. Set Environment Variables

```bash
export VITE_SUPABASE_URL="https://your-project.supabase.co"
export VITE_SUPABASE_ANON_KEY="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

### 4. Run Your Workflow

```python
import os
from agora.agora_tracer import init_traceloop, TracedAsyncFlow, agora_node

# Credentials from environment
# VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY

# Initialize with cloud upload
init_traceloop(
    app_name="my_workflow",
    export_to_console=True,
    enable_cloud_upload=True,  # ✅ Now supported!
    project_name="My Project"
)

# Define your workflow
@agora_node(name="ProcessData")
async def process_data(shared):
    shared["result"] = "done"
    return None

# Run it
flow = TracedAsyncFlow("MyWorkflow")
flow.start(process_data)
await flow.run_async({})

# Telemetry automatically uploaded to Supabase!
```

### 5. View Telemetry

1. Open your deployed frontend
2. Go to **Monitoring** page
3. See your execution appear!
4. Click **View Details** for timeline and metrics

## What Gets Created Automatically

When you run a workflow, the system auto-creates:

1. **Organization** (if none exists)
2. **Project** (with the name you specified)
3. **Workflow** (with the flow name)
4. **Execution** record
5. **Nodes** (one for each @agora_node)
6. **Node Executions** (timing and status for each node run)

## For Colab/Jupyter

In your notebook:

```python
# Cell 1: Install
!pip install supabase

# Cell 2: Set credentials
import os
os.environ["VITE_SUPABASE_URL"] = "https://your-project.supabase.co"
os.environ["VITE_SUPABASE_ANON_KEY"] = "your-anon-key"

# Cell 3: Run your code
# (rest of your workflow code)
```

## Troubleshooting

### Error: "init_traceloop() got an unexpected keyword argument 'enable_cloud_upload'"

**Cause**: Old version of agora_tracer.py

**Fix**: Make sure you're using the updated version:
```bash
# Check the file has been updated
grep "enable_cloud_upload" agora/agora_tracer.py
```

You should see the parameter in the function signature.

### No telemetry showing up

**Check 1**: Verify supabase package is installed
```bash
pip list | grep supabase
```

**Check 2**: Verify environment variables
```bash
echo $VITE_SUPABASE_URL
echo $VITE_SUPABASE_ANON_KEY
```

**Check 3**: Look for success message when running script
```
✅ Supabase uploader enabled for project: My Project
✅ Started execution: <execution-id>
✅ Completed execution: <execution-id> (success)
```

### Database connection errors

**Check**: Make sure Supabase credentials are correct
- Copy them directly from your `.env` file
- Don't use the service role key (use anon key)

### RLS Policy Errors

**Issue**: Supabase RLS might block anonymous inserts

**Solution**: The uploader creates records properly. If you see RLS errors, it means:
1. You're using the wrong key (use ANON key, not service role)
2. RLS policies need adjustment (already set up correctly in migrations)

## What's Different From Before

### ❌ Old Way (Had Issues)
- Required backend API running
- Needed API key generation
- HTTP requests to localhost:8000
- Complex setup

### ✅ New Way (Direct Supabase)
- No backend needed
- Uses same database as frontend
- Direct database inserts
- Simple setup (just 2 env vars)

## Example Output

When running a workflow, you'll see:

```
✅ Supabase uploader enabled for project: Demo Project
✅ Traceloop initialized: demo_workflow

🚀 Starting demo workflow...
✅ Started execution: 123e4567-e89b-12d3-a456-426614174000
  ✓ Processed item #1
  ✓ Processed item #2

✅ Workflow completed successfully!
✅ Completed execution: 123e4567-e89b-12d3-a456-426614174000 (success)
```

Then in your frontend Monitoring page, you'll see that execution!

## Next Steps

1. Run the demo: `python demo_workflow.py`
2. Check the Monitoring page
3. Click "View Details" to see the timeline
4. Try adding more nodes to see them appear in the timeline

All data goes directly to the same Supabase database your website uses!
