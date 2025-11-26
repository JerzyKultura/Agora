# 🔥 TELEMETRY SETUP - WHERE DOES THE DATA GO?

## THE PROBLEM YOU HAD

**NO DATA in your Supabase tables** because `supabase-py` wasn't installed!

The code was perfect, but the Python library wasn't there, so:
- ✅ Code: Perfect
- ❌ Library: Missing
- ❌ Result: No data uploaded

## THE SOLUTION

### 1. Install Dependencies

```bash
pip install traceloop-sdk supabase openai
```

Or install with the telemetry extras:

```bash
pip install -e ".[telemetry]"
```

### 2. Set Environment Variables

```bash
# From your .env file
export VITE_SUPABASE_URL="https://xxxxx.supabase.co"
export VITE_SUPABASE_ANON_KEY="eyJhbGci..."

# Your OpenAI key for the demos
export OPENAI_API_KEY="sk-..."
```

### 3. Run a Demo

```bash
python demo_workflow.py
```

## WHERE THE DATA GOES

```
┌─────────────────────────────────────────────────────────────┐
│  YOUR PYTHON SCRIPT (demo_workflow.py, colab_demo.py)      │
│                                                             │
│  1. init_traceloop(enable_cloud_upload=True)                │
│  2. Creates SupabaseUploader with your credentials          │
│  3. Wraps your @agora_node functions                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ supabase-py client
                      │ Direct database writes
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  YOUR SUPABASE DATABASE                                     │
│                                                             │
│  Tables:                                                    │
│  ├─ organizations    (your org)                             │
│  ├─ projects         (your project)                         │
│  ├─ workflows        (your workflow definitions)            │
│  ├─ executions       (every time you run)                   │
│  ├─ node_executions  (each node that runs)                  │
│  ├─ telemetry_spans  (OpenTelemetry timing data)           │
│  └─ telemetry_events (logs, errors, events)                │
└─────────────────────┬───────────────────────────────────────┘
                      │
                      │ Same database!
                      │
                      ▼
┌─────────────────────────────────────────────────────────────┐
│  YOUR REACT FRONTEND (Monitoring Page)                     │
│                                                             │
│  Reads from same database and shows:                        │
│  ├─ Execution list                                          │
│  ├─ Timeline visualization                                  │
│  ├─ Node details                                            │
│  └─ Performance metrics                                     │
└─────────────────────────────────────────────────────────────┘
```

## WHAT HAPPENS WHEN YOU RUN

### Step 1: Import and Initialize
```python
from agora.agora_tracer import init_traceloop, agora_node, TracedAsyncFlow

init_traceloop(
    app_name="my_app",
    enable_cloud_upload=True,  # ← KEY!
    project_name="My Project"
)
```

**What it does:**
- Creates `SupabaseUploader` instance
- Connects to your Supabase database
- Prints: `✅ Supabase uploader enabled for project: My Project`

### Step 2: Start Workflow
```python
flow = TracedAsyncFlow("MyWorkflow")
await flow.start({"input": "hello"})
```

**What it does:**
1. Gets/creates organization in `organizations` table
2. Gets/creates project in `projects` table
3. Gets/creates workflow in `workflows` table
4. Creates new execution in `executions` table
5. Prints: `✅ Started execution: abc-123-def-456`

### Step 3: Nodes Execute
```python
@agora_node(name="ProcessData")
async def process_data(shared):
    result = do_work(shared["input"])
    return "next"
```

**What it does:**
1. Records start time
2. Executes your function
3. Records end time
4. Writes to `node_executions` table
5. Writes OpenTelemetry spans to `telemetry_spans` table

### Step 4: Workflow Completes
```python
# Automatic at end of flow.start()
```

**What it does:**
1. Calculates total duration
2. Updates `executions` table with status="success"
3. Prints: `✅ Completed execution: abc-123-def-456 (success)`

## VIEW YOUR DATA

### Option 1: Supabase Dashboard

```
https://app.supabase.com/project/YOUR_PROJECT_ID/editor
```

Click "Table Editor" → see all tables with your data

### Option 2: SQL Query

```sql
-- See all executions
SELECT * FROM executions ORDER BY started_at DESC LIMIT 10;

-- See execution details
SELECT
  e.id,
  w.name as workflow,
  e.status,
  e.duration_ms,
  e.started_at
FROM executions e
JOIN workflows w ON w.id = e.workflow_id
ORDER BY e.started_at DESC;

-- See node executions for a workflow run
SELECT
  ne.started_at,
  n.name as node_name,
  ne.status,
  ne.exec_duration_ms
FROM node_executions ne
JOIN nodes n ON n.id = ne.node_id
WHERE ne.execution_id = 'YOUR_EXECUTION_ID'
ORDER BY ne.started_at;
```

### Option 3: Your Frontend (Best!)

```
http://localhost:5173/monitoring
```

Shows:
- ✅ List of all workflow executions
- ✅ Status, duration, timestamps
- ✅ Click for detailed timeline view
- ✅ Node execution graph
- ✅ Performance metrics

## TROUBLESHOOTING

### ⚠️  "Supabase upload not available"

**Problem:** `supabase-py` not installed

**Solution:**
```bash
pip install supabase
```

### ⚠️  "VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY not set"

**Problem:** Environment variables missing

**Solution:**
```bash
export VITE_SUPABASE_URL="https://xxxxx.supabase.co"
export VITE_SUPABASE_ANON_KEY="eyJhbGci..."
```

Get them from your `.env` file in the project root!

### ⚠️  "Failed to get organization"

**Problem:** Database permissions issue

**Solution:** Check your Row Level Security policies. The Supabase anon key needs access to:
- organizations (SELECT, INSERT)
- projects (SELECT, INSERT)
- workflows (SELECT, INSERT)
- executions (SELECT, INSERT, UPDATE)
- node_executions (SELECT, INSERT, UPDATE)
- telemetry_spans (SELECT, INSERT)
- telemetry_events (SELECT, INSERT)

### ⚠️  Still no data?

**Debug steps:**

1. Check if SupabaseUploader loaded:
```python
from agora.supabase_uploader import SupabaseUploader
print("Supabase uploader available!")
```

2. Check if it's enabled:
```python
# After init_traceloop()
from agora.agora_tracer import cloud_uploader
print(f"Enabled: {cloud_uploader.enabled if cloud_uploader else 'None'}")
```

3. Check database connection:
```bash
# Test with supabase client directly
python3 -c "
from supabase import create_client
import os
client = create_client(
    os.environ['VITE_SUPABASE_URL'],
    os.environ['VITE_SUPABASE_ANON_KEY']
)
result = client.table('organizations').select('*').execute()
print(f'Organizations: {len(result.data)}')
"
```

## SUMMARY

### Before (BROKEN):
- ❌ `supabase-py` not installed
- ❌ `cloud_uploader.enabled = False`
- ❌ No data in database
- ❌ Empty tables

### After (WORKING):
- ✅ `pip install supabase traceloop-sdk`
- ✅ Set `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY`
- ✅ Run `python demo_workflow.py`
- ✅ Data flows: Script → Supabase → Frontend
- ✅ View at `/monitoring` page

## NO API KEYS NEEDED!

The old `AGORA_API_KEY` system is deprecated. You just need:
1. Supabase URL
2. Supabase anon key
3. Python library installed

That's it! The data goes directly to your database.
