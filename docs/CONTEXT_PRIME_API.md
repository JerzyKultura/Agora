# Context Prime API - Usage Guide

## Overview

The Context Prime endpoint provides intelligent, LLM-generated summaries of project state by analyzing:
- Recent failures from telemetry
- Codebase changes
- Active execution state

## Quick Start

### Basic Request

```bash
curl -X POST https://api.agora.com/v1/context/prime \
  -H "Authorization: Bearer agora_your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "7dec9756-4af9-4118-89d7-c11588052c9c"
  }'
```

### Response

```json
{
  "project_id": "7dec9756-4af9-4118-89d7-c11588052c9c",
  "organization_id": "a1b2c3d4-...",
  "context_summary": "Project: Agora-Core. Status: Active debugging. Last failure: auth.py:verify_token raised KeyError. Recommended focus: Review token validation logic.",
  "metadata": {
    "recent_failures": [...],
    "codebase_snapshot": [...],
    "active_state": {...}
  },
  "generated_at": "2024-01-01T10:35:00Z",
  "llm_provider": "gemini"
}
```

---

## BYOK (Bring Your Own Key)

### Why BYOK?

- **Zero Cost**: Use your own LLM API keys
- **Privacy**: Your keys, your control
- **Flexibility**: Choose Gemini or OpenAI

### Setup

1. **Get an API Key**
   - **Gemini**: https://makersuite.google.com/app/apikey
   - **OpenAI**: https://platform.openai.com/api-keys

2. **Store in Organization Settings**
   ```sql
   UPDATE organizations
   SET 
     llm_api_key = 'your_encrypted_key_here',
     llm_provider = 'gemini'  -- or 'openai'
   WHERE id = 'your_org_id';
   ```

3. **Use Context Prime**
   - Endpoint automatically uses your key
   - Falls back to system keys if not configured
   - Falls back to rule-based summary if no keys available

---

## Intelligence Sources

### 1. Recent Failures

**Query:** Last 3 error spans from `telemetry_spans`

**Extracted Data:**
- Span name (e.g., `auth.verify_token`)
- Error message from attributes
- Trace ID for correlation
- Timestamp

**Example:**
```json
{
  "name": "auth.verify_token",
  "error_message": "KeyError: 'exp'",
  "trace_id": "abc123...",
  "timestamp": "2024-01-01T10:30:00Z"
}
```

### 2. Codebase Map

**Query:** Last 10 updated functions/classes from `nodes`

**Extracted Data:**
- Function/class names
- Signatures
- File paths
- Update timestamps

**Example:**
```json
{
  "name": "verify_token",
  "node_type": "function",
  "signature": "async def verify_token(token: str) -> Dict",
  "file_path": "backend/auth.py",
  "updated_at": "2024-01-01T09:00:00Z"
}
```

### 3. Active State

**Query:** Latest execution from `executions` with state snapshot

**Extracted Data:**
- Execution ID and status
- Workflow name
- Shared state data
- Timing information

**Example:**
```json
{
  "execution_id": "exec-123",
  "status": "failed",
  "workflow_name": "user_authentication",
  "snapshot_data": {"user_id": "123", "attempt": 3},
  "started_at": "2024-01-01T10:00:00Z"
}
```

---

## LLM Provider Priority

1. **Organization's BYOK** (if configured)
2. **System Gemini Key** (if `GEMINI_API_KEY` set)
3. **System OpenAI Key** (if `OPENAI_API_KEY` set)
4. **Rule-Based Fallback** (no LLM required)

---

## Response Fields

| Field | Type | Description |
|-------|------|-------------|
| `project_id` | UUID | Project identifier |
| `organization_id` | UUID | Organization identifier |
| `context_summary` | string | LLM-generated summary (2-3 sentences) |
| `metadata` | object | Raw intelligence data |
| `generated_at` | datetime | When summary was generated |
| `llm_provider` | string | "gemini", "openai", or "fallback" |

---

## Use Cases

### 1. AI Agent Context Priming

```python
from agora_sdk import AgoraClient

client = AgoraClient(api_key="agora_xxx")

# Get intelligent context
context = client.context.prime(project_id="...")

# Use in AI prompt
prompt = f"""
{context.context_summary}

Task: Debug the authentication issue.
"""
```

### 2. Dashboard Status Widget

```typescript
const context = await fetch('/v1/context/prime', {
  method: 'POST',
  headers: { 'Authorization': 'Bearer agora_xxx' },
  body: JSON.stringify({ project_id: 'xxx' })
}).then(r => r.json());

// Display: "Status: Debugging. Focus: Check JWT logic."
```

### 3. Slack Bot Integration

```python
# Daily project status
context = await prime_context(project_id)
slack_client.post_message(
    channel="#dev",
    text=f"📊 Daily Status: {context.context_summary}"
)
```

---

## Error Handling

### 401 Unauthorized
```json
{
  "detail": "Missing or invalid API key"
}
```

**Solution:** Check `Authorization` header

### 404 Not Found
```json
{
  "detail": "Project not found or access denied"
}
```

**Solution:** Verify `project_id` belongs to your organization

### 500 Internal Server Error
```json
{
  "detail": "Failed to generate context: ..."
}
```

**Solution:** Check logs, verify database connectivity

---

## Performance

- **Response Time:** < 2 seconds (including LLM call)
- **Rate Limit:** 10 requests/minute per organization (recommended)
- **Caching:** Consider caching summaries for 5-10 minutes

---

## Security

### Multi-Tenant Isolation

- ✅ All queries filtered by `organization_id`
- ✅ RLS policies enforced on all tables
- ✅ Project ownership verified before access

### API Key Storage

> **IMPORTANT:** Organization LLM keys should be encrypted at rest.
> 
> Current implementation stores keys as-is. For production:
> 1. Use encryption library (e.g., `cryptography`)
> 2. Encrypt before storing in `organizations.llm_api_key`
> 3. Decrypt when fetching for LLM calls

**Example Encryption:**
```python
from cryptography.fernet import Fernet

# Generate key (store securely)
encryption_key = Fernet.generate_key()
cipher = Fernet(encryption_key)

# Encrypt API key
encrypted_key = cipher.encrypt(api_key.encode())

# Store in database
supabase.table("organizations").update({
    "llm_api_key": encrypted_key.decode()
}).eq("id", org_id).execute()

# Decrypt when needed
decrypted_key = cipher.decrypt(encrypted_key).decode()
```

---

## Future Enhancements

1. **Context Caching** - Cache summaries per project (5-10 min TTL)
2. **Streaming** - Stream LLM response for faster perceived latency
3. **Custom Prompts** - Allow users to customize summary format
4. **Historical Trends** - Include week-over-week failure trends
5. **Dependency Graph** - Add most-called functions from telemetry
6. **Multi-Project** - Generate cross-project summaries

---

## Example Integration

### Python SDK

```python
import asyncio
from agora_sdk import AgoraClient

async def main():
    client = AgoraClient(api_key="agora_xxx")
    
    # Prime context
    context = await client.context.prime(
        project_id="7dec9756-4af9-4118-89d7-c11588052c9c"
    )
    
    print(f"Summary: {context.context_summary}")
    print(f"Provider: {context.llm_provider}")
    print(f"Failures: {len(context.metadata.recent_failures)}")

asyncio.run(main())
```

### JavaScript/TypeScript

```typescript
import { AgoraClient } from '@agora/sdk';

const client = new AgoraClient({ apiKey: 'agora_xxx' });

const context = await client.context.prime({
  projectId: '7dec9756-4af9-4118-89d7-c11588052c9c'
});

console.log(`Summary: ${context.contextSummary}`);
console.log(`Provider: ${context.llmProvider}`);
```

---

## Troubleshooting

### Summary is Generic

**Cause:** No telemetry data or recent activity

**Solution:** 
- Run workflows to generate telemetry
- Ingest codebase using `ingest_codebase.py`
- Wait for executions to complete

### LLM Provider is "fallback"

**Cause:** No API keys configured

**Solution:**
- Set `GEMINI_API_KEY` or `OPENAI_API_KEY` in `.env`
- OR configure organization BYOK in database

### Slow Response Time

**Cause:** LLM API latency

**Solution:**
- Implement caching (5-10 min TTL)
- Use faster LLM model (e.g., `gemini-pro` vs `gpt-4`)
- Consider streaming responses

---

## Support

For questions or issues:
- **Documentation:** https://docs.agora.com/context-prime
- **GitHub:** https://github.com/your-org/agora/issues
- **Discord:** https://discord.gg/agora
