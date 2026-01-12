# Google Colab + Agora Monitoring Platform Integration

This guide shows you how to run LLM applications in Google Colab and view full telemetry in your Agora monitoring platform.

## Quick Start

### 1. Copy the Example Code

Use `colab_rag_with_monitoring.py` - it's ready to copy-paste into Google Colab!

The code is split into 3 cells:
- **Cell 1**: Install dependencies
- **Cell 2**: Set credentials (pre-filled for you)
- **Cell 3**: Run RAG chat demo with full monitoring

### 2. What Gets Captured

Every LLM call, embedding, and Qdrant search is automatically traced with:

**Technical Metrics:**
- Model name & provider
- Token usage (prompt + completion)
- Cost estimation
- Latency & duration
- Error messages (if any)

**Business Context (Wide Events):**
- User ID
- Subscription tier
- Session ID
- Conversation turn
- Custom attributes (collection name, models, etc.)

### 3. View in Monitoring Platform

After running the Colab notebook:

1. **Start the monitoring UI** (if not already running):
   ```bash
   cd /home/user/Agora/platform/frontend
   npm install
   npm run dev
   ```

2. **Open http://localhost:5173/**

3. **Navigate to "Monitoring"** in the left sidebar

4. **Switch to "Traces" view**

5. **Find your execution:**
   - Search by session ID (e.g., `chat_1768183968`)
   - Search by user ID (e.g., `demo_user_123`)
   - Sort by recent (your execution will be at the top)

6. **Click on a trace** to see:
   - **Messages Tab**: Full conversation with prompts & completions
   - **LLM Data Tab**: Token usage, costs, model info
   - **Details Tab**: Business context attributes
   - **Raw Tab**: Full JSON dump of span data

## How It Works

### Wide Events Integration

The magic happens with the `set_business_context()` API:

```python
from agora.wide_events import set_business_context

# Set business context ONCE
set_business_context(
    user_id="user_123",
    subscription_tier="pro",
    session_id="chat_session_456",
    workflow_type="rag_chat",
    custom={"model": "gpt-4o-mini"}
)

# Now ALL LLM calls automatically include this context!
response = openai_client.chat.completions.create(...)  # ✅ Auto-enriched!
embedding = openai_client.embeddings.create(...)       # ✅ Auto-enriched!
```

**Behind the scenes:**
1. Traceloop auto-instruments OpenAI calls → creates OpenTelemetry spans
2. `BusinessContextSpanProcessor` (enabled by `init_agora()`) adds business context to every span
3. `SupabaseSpanExporter` uploads spans to your Supabase database
4. Monitoring UI queries Supabase and displays the data

### Architecture

```
┌─────────────────┐
│  Google Colab   │
│                 │
│  1. init_agora()│──────┐
│  2. set_context │      │
│  3. OpenAI call │      │
└─────────────────┘      │
                         │ OpenTelemetry
                         │ spans
                         ▼
┌─────────────────────────────────┐
│  BusinessContextSpanProcessor   │
│  (adds user_id, session_id, etc)│
└─────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────┐
│   SupabaseSpanExporter          │
│   (uploads to Supabase)         │
└─────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────┐
│   Supabase Database             │
│   - executions table            │
│   - telemetry_spans table       │
└─────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────┐
│   Monitoring UI (localhost:5173)│
│   - Trace timeline              │
│   - Token/cost analytics        │
│   - Business context viewer     │
└─────────────────────────────────┘
```

## Database Schema

Your telemetry is stored in these Supabase tables:

### `executions` Table
- `id` (UUID) - Execution identifier
- `workflow_id` (UUID) - Links to workflow
- `status` (text) - running, success, error
- `started_at` (timestamp)
- `completed_at` (timestamp)
- `tokens_used` (bigint)
- `estimated_cost` (decimal)

### `telemetry_spans` Table
- `span_id` (text) - Unique span identifier
- `trace_id` (text) - Groups related spans
- `execution_id` (UUID) - Links to execution
- `name` (text) - Span name (e.g., "openai.chat")
- `kind` (text) - Span kind (CLIENT, SERVER, etc.)
- `status` (text) - OK, ERROR
- `start_time` (timestamp)
- `end_time` (timestamp)
- `duration_ms` (int)
- **`attributes` (JSONB)** - ⭐ **Business context lives here!**
- `tokens_used` (int)
- `estimated_cost` (decimal)

### Business Context in `attributes`

The `attributes` JSONB field contains:

```json
{
  "user.id": "demo_user_123",
  "user.subscription_tier": "pro",
  "session.id": "chat_1768183968",
  "session.conversation_turn": 1,
  "app.workflow_type": "rag_chat",
  "app.version": "1.0.0",
  "custom.qdrant_collection": "agora_docs",
  "custom.embedding_model": "text-embedding-3-small",
  "custom.chat_model": "gpt-4o-mini",
  "custom.user_query": "What is Agora?",
  "llm.usage.total_tokens": 150,
  "llm.usage.prompt_tokens": 100,
  "llm.usage.completion_tokens": 50,
  "llm.model": "gpt-4o-mini",
  "llm.provider": "openai"
}
```

## Querying Your Data

### Via Supabase SQL Editor

```sql
-- Get all executions
SELECT * FROM executions
ORDER BY started_at DESC
LIMIT 10;

-- Get spans for a specific execution
SELECT
    name,
    duration_ms,
    tokens_used,
    estimated_cost,
    attributes->>'user.id' as user_id,
    attributes->>'session.id' as session_id
FROM telemetry_spans
WHERE execution_id = 'fcac8b10-59f6-4e02-970e-b4e2b20d37e1'
ORDER BY start_time;

-- Find all LLM calls by a specific user
SELECT
    span_id,
    name,
    attributes->>'user.id' as user_id,
    attributes->>'user.subscription_tier' as tier,
    tokens_used,
    estimated_cost
FROM telemetry_spans
WHERE attributes->>'user.id' = 'demo_user_123'
ORDER BY start_time DESC;

-- Aggregate costs by subscription tier
SELECT
    attributes->>'user.subscription_tier' as tier,
    COUNT(*) as llm_calls,
    SUM(tokens_used) as total_tokens,
    SUM(estimated_cost) as total_cost
FROM telemetry_spans
WHERE name LIKE '%chat%'
  AND tokens_used IS NOT NULL
GROUP BY attributes->>'user.subscription_tier';
```

### Via Python (Supabase Client)

```python
from supabase import create_client
import os

supabase = create_client(
    os.environ['VITE_SUPABASE_URL'],
    os.environ['VITE_SUPABASE_ANON_KEY']
)

# Get execution details
result = supabase.table('executions') \
    .select('*') \
    .eq('id', 'fcac8b10-59f6-4e02-970e-b4e2b20d37e1') \
    .execute()

# Get spans with business context
result = supabase.table('telemetry_spans') \
    .select('*') \
    .eq('execution_id', 'fcac8b10-59f6-4e02-970e-b4e2b20d37e1') \
    .order('start_time') \
    .execute()

for span in result.data:
    print(f"Span: {span['name']}")
    print(f"  User: {span['attributes'].get('user.id')}")
    print(f"  Tokens: {span['tokens_used']}")
    print(f"  Cost: ${span['estimated_cost']}")
```

## Troubleshooting

### "Execution not found in monitoring UI"

1. **Check Supabase credentials** are correct in `.env.local`:
   ```bash
   cat /home/user/Agora/platform/frontend/.env.local
   ```

2. **Verify data was uploaded** by checking Supabase dashboard:
   - Go to https://supabase.com/dashboard
   - Select your project
   - Open "Table Editor"
   - Check `executions` and `telemetry_spans` tables

3. **Check frontend is connected** to the same Supabase instance:
   - Frontend `.env.local` should match the Colab credentials
   - Restart frontend after changing `.env.local`

### "No business context in spans"

1. **Verify `set_business_context()` was called** before LLM calls
2. **Check init_agora() enabled wide events**:
   ```python
   # Should see this message:
   # ✅ Wide events (business context) processor enabled
   ```
3. **View raw span data** in "Raw" tab to see all attributes

### "Cloud uploader not available"

1. **Install supabase-py**:
   ```bash
   pip install supabase
   ```

2. **Set environment variables**:
   ```python
   os.environ['VITE_SUPABASE_URL'] = 'https://...'
   os.environ['VITE_SUPABASE_ANON_KEY'] = 'eyJ...'
   ```

3. **Verify credentials** are loaded before `init_agora()`

## Custom Business Context

Add your own business metrics:

```python
set_business_context(
    user_id="user_123",
    subscription_tier="enterprise",

    # Session context
    session_id="session_456",
    conversation_turn=5,

    # Feature flags
    feature_flags={
        "new_chat_ui": True,
        "gpt4_access": True
    },

    # Business metrics
    lifetime_value_cents=250000,  # $2,500 LTV
    account_age_days=90,

    # Custom fields
    custom={
        "team_id": "team_789",
        "department": "sales",
        "priority": "high",
        "campaign_id": "summer_2024"
    }
)
```

All of these fields will appear in the `attributes` column and be queryable!

## Next Steps

1. **Customize the business context** for your use case
2. **Add more LLM calls** - they'll all be auto-traced
3. **Build dashboards** querying the `telemetry_spans` table
4. **Set up alerts** based on cost, errors, or latency
5. **Analyze user behavior** by querying business context attributes

## Reference

- **Agora Documentation**: `/home/user/Agora/README.md`
- **Wide Events Module**: `/home/user/Agora/agora/wide_events.py`
- **Monitoring UI Source**: `/home/user/Agora/platform/frontend/src/pages/Monitoring.tsx`
- **Example Code**: `/home/user/Agora/examples/colab_rag_with_monitoring.py`
