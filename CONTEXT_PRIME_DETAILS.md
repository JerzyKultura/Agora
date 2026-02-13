# Agora Context Prime - Technical Details

## What I Need

### 1. Golden Score Formula
**Status**: ❌ **NOT IMPLEMENTED** - Only conceptual

**Current State**: No salience/golden score calculation exists in the codebase. The system currently:
- Fetches last 3 errors (hardcoded limit)
- Fetches last 10 code changes (hardcoded limit)
- Fetches latest execution state
- No scoring/ranking/prioritization logic

**What exists instead**: Simple chronological ordering (most recent first)

---

### 2. Current State of Key Files

#### `platform/backend/utils/llm_client.py`

**Hardcoded Models**:
- **Line 115**: `model = genai.GenerativeModel('gemini-pro')` ⚠️ OLD MODEL
- **Line 134**: `model="gpt-4"` ⚠️ EXPENSIVE MODEL

**Current Flow**:
1. Try org BYOK key first (if configured)
2. Fallback to system `GEMINI_API_KEY` env var
3. Fallback to system `OPENAI_API_KEY` env var
4. Final fallback: rule-based summary (no LLM)

**Issues**:
- `gemini-pro` is deprecated (should use `gemini-1.5-flash` or `gemini-1.5-pro`)
- `gpt-4` is expensive ($0.03/1K tokens) - should use `gpt-4o-mini` ($0.00015/1K tokens)
- No caching mechanism
- No rate limiting

---

#### `platform/backend/routers/context.py`

**Current `/v1/context/prime` Implementation**:

**Endpoint**: `POST /v1/context/prime`

**Request**:
```json
{
  "project_id": "uuid"
}
```

**Response**:
```json
{
  "project_id": "uuid",
  "organization_id": "uuid",
  "context_summary": "Project: X. Status: Y. Recommended focus: Z.",
  "metadata": {
    "recent_failures": [...],
    "codebase_snapshot": [...],
    "active_state": {...}
  },
  "generated_at": "2026-02-12T21:47:18Z",
  "llm_provider": "gemini|openai|fallback"
}
```

**Data Fetching**:
- `fetch_recent_failures()`: Last 3 spans with `status='ERROR'` from `telemetry_spans`
- `fetch_codebase_map()`: Last 10 functions/classes from `nodes` table
- `fetch_active_state()`: Latest execution + state snapshot

**Issues**:
- No caching (every request hits DB + LLM)
- No rate limiting
- No salience scoring
- Hardcoded limits (3 failures, 10 code changes)

---

#### CLI Tool Location

**Path**: `scripts/agora-hook.sh`

**Current Output Format**:
```bash
🧠 Fetching context from Agora...
✅ Context Summary:

Project: Agora-Core. Status: Active debugging. Last failure: auth.py:verify_token raised KeyError on 'exp' claim. Recent changes to JWT validation logic. Recommended focus: Review token expiration handling in auth module.

📋 Copied to clipboard
💾 Saved to: /tmp/agora_context_7dec9756.txt
```

**Current Behavior**:
- Calls `POST /v1/context/prime` with project_id
- Extracts `context_summary` field from JSON response
- Copies to clipboard (macOS: `pbcopy`, Linux: `xclip`)
- Saves to `/tmp/agora_context_{project_id}.txt`

**Issues**:
- Only shows summary text (no metadata)
- No structured output option
- No error details
- No salience scores

---

### 3. Database Schema Clarity

#### `telemetry_spans` Table

**Schema** (from migrations):
```sql
CREATE TABLE telemetry_spans (
  id uuid PRIMARY KEY,
  execution_id uuid REFERENCES executions(id),
  node_execution_id uuid REFERENCES node_executions(id),
  span_id text NOT NULL,
  trace_id text NOT NULL,
  parent_span_id text,
  name text NOT NULL,
  kind text,
  status text,                    -- ✅ YES
  start_time timestamptz NOT NULL,
  end_time timestamptz,
  duration_ms integer,            -- ✅ YES
  attributes jsonb DEFAULT '{}',
  events jsonb DEFAULT '[]',
  created_at timestamptz,         -- ✅ YES
  organization_id uuid NOT NULL   -- ✅ YES (added in 20260121 migration)
);
```

**Field Availability**:
- ✅ `status` - YES
- ❌ `token_count` - **NO** (stored in `attributes.token_count` JSONB field)
- ✅ `duration_ms` - YES
- ✅ `created_at` - YES
- ✅ `organization_id` - YES

**Token Count Location**:
Token usage is stored in the `attributes` JSONB column:
```json
{
  "attributes": {
    "token_count": 1234,
    "llm.usage.prompt_tokens": 100,
    "llm.usage.completion_tokens": 50,
    "llm.usage.total_tokens": 150
  }
}
```

---

#### `context_cache` Table

**Status**: ❌ **DOES NOT EXIST**

**Need to Create**: YES

**Suggested Schema**:
```sql
CREATE TABLE context_cache (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  context_summary text NOT NULL,
  metadata jsonb NOT NULL,
  llm_provider text,
  generated_at timestamptz NOT NULL DEFAULT now(),
  expires_at timestamptz NOT NULL,
  created_at timestamptz DEFAULT now(),
  
  -- Ensure one cache entry per project
  UNIQUE(project_id)
);

CREATE INDEX idx_context_cache_project_id ON context_cache(project_id);
CREATE INDEX idx_context_cache_expires_at ON context_cache(expires_at);
```

---

## Quick Questions

### 1. Caching Preference

**Options**:
- **In-memory** (simple, loses on restart, no DB overhead)
- **Supabase table** (persistent, survives restarts, enables analytics)

**Recommendation**: **Supabase table** because:
- Context Prime is expensive (LLM calls)
- Persistence allows debugging ("what context did the AI see?")
- Can add TTL/expiration logic
- Can track cache hit rates

**Suggested TTL**: 5 minutes (balance freshness vs cost)

---

### 2. Rate Limiting

**Options**:
- None (risky - users can spam expensive LLM calls)
- Per-org (10 requests/minute per organization)
- Per-project (5 requests/minute per project)

**Recommendation**: **Per-org** rate limiting:
- 10 requests/minute per organization
- Returns HTTP 429 with `Retry-After` header
- Use in-memory sliding window (simple, no DB overhead)

**Why**: Even with BYOK, users shouldn't accidentally spam their own API keys

---

### 3. Model Preference

**Options**:
- Default to Gemini 1.5 Flash (fast, cheap)
- Let user choose in BYOK UI (more flexible)

**Recommendation**: **Default to Gemini 1.5 Flash** with UI option:
- Default: `gemini-1.5-flash` (fast, cheap, good enough)
- BYOK UI: Dropdown to choose model:
  - Gemini: `gemini-1.5-flash`, `gemini-1.5-pro`
  - OpenAI: `gpt-4o-mini`, `gpt-4o`, `gpt-4-turbo`

**Why**: Most users want "just works" but power users want control

---

## File Locations Summary

```
platform/backend/utils/llm_client.py          # LLM client (needs model updates)
platform/backend/routers/context.py           # /v1/context/prime endpoint
scripts/agora-hook.sh                         # CLI tool
supabase/migrations/20260212_add_byok_llm_config.sql  # BYOK schema (not applied yet)
```

---

## Missing Pieces

1. ❌ Salience scoring algorithm
2. ❌ Context caching (table + logic)
3. ❌ Rate limiting
4. ❌ Model configuration (hardcoded old models)
5. ❌ Token count extraction from JSONB
6. ❌ CLI structured output format
7. ❌ BYOK UI (Settings page)

---

## Next Steps

Once you provide:
1. **Golden score formula** (how to rank failures/changes by importance)
2. **Caching preference** (in-memory vs Supabase)
3. **Rate limiting preference** (per-org vs per-project)
4. **Model preference** (default vs user choice)

I can provide 3 surgical prompts for:
1. Model config + caching implementation
2. Salience scoring using your golden score
3. CLI output format improvements

Estimated implementation time: ~5 minutes with Claude Sonnet
