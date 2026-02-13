# OpenTelemetry Telemetry Integration

## Overview

The Agora platform now supports **OpenTelemetry (OTel) JSON format** for telemetry ingestion, making it compatible with industry-standard observability tools like **Traceloop** and **OpenLLMetry**.

## Quick Start

### 1. Configure Your Application

```python
from traceloop.sdk import Traceloop

# Initialize Traceloop to send to Agora
Traceloop.init(
    api_endpoint="https://your-backend.com/telemetry/traces",
    headers={"Authorization": "Bearer agora_your_api_key_here"}
)
```

### 2. Instrument Your Code

```python
from openai import OpenAI

client = OpenAI()

# This will automatically send telemetry to Agora
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello!"}]
)
```

### 3. View in Dashboard

All spans will appear in your Agora dashboard under **Monitoring → Telemetry**.

---

## API Reference

### Endpoint

```
POST /telemetry/traces
```

### Authentication

**Option 1: Bearer Token (Recommended)**
```http
Authorization: Bearer agora_your_api_key
```

**Option 2: X-API-Key Header (Legacy)**
```http
X-API-Key: agora_your_api_key
```

### Request Body

OpenTelemetry JSON format:

```json
{
  "resourceSpans": [{
    "resource": {
      "attributes": [
        {"key": "service.name", "value": {"stringValue": "my-service"}}
      ]
    },
    "scopeSpans": [{
      "scope": {
        "name": "opentelemetry.instrumentation.openai",
        "version": "0.1.0"
      },
      "spans": [{
        "traceId": "1234567890abcdef1234567890abcdef",
        "spanId": "1234567890abcdef",
        "name": "openai.chat.completions",
        "kind": 3,
        "startTimeUnixNano": "1704067200000000000",
        "endTimeUnixNano": "1704067201500000000",
        "attributes": [
          {"key": "llm.model", "value": {"stringValue": "gpt-4"}},
          {"key": "llm.tokens.total", "value": {"intValue": 225}}
        ],
        "status": {"code": 1}
      }]
    }]
  }]
}
```

### Response

```json
{
  "spans_ingested": 1,
  "organization_id": "7dec9756-4af9-4118-89d7-c11588052c9c"
}
```

---

## Data Mapping

### Trace & Span IDs

- **OTel Format**: Hex strings (32 chars for traceId, 16 for spanId)
- **Supabase Storage**: Stored as `TEXT` (not converted to UUID)

### Timestamps

- **OTel Format**: Unix nanoseconds (e.g., `"1704067200000000000"`)
- **Supabase Storage**: ISO 8601 timestamps (e.g., `"2024-01-01T00:00:00+00:00"`)

### Attributes

- **OTel Format**: Array of key-value pairs with typed values
  ```json
  [
    {"key": "http.method", "value": {"stringValue": "GET"}},
    {"key": "http.status_code", "value": {"intValue": 200}}
  ]
  ```
- **Supabase Storage**: Flat JSONB dictionary
  ```json
  {
    "http.method": "GET",
    "http.status_code": 200
  }
  ```

### Span Kind

| OTel Code | String Value |
|-----------|--------------|
| 0 | UNSPECIFIED |
| 1 | INTERNAL |
| 2 | SERVER |
| 3 | CLIENT |
| 4 | PRODUCER |
| 5 | CONSUMER |

### Span Status

| OTel Code | String Value |
|-----------|--------------|
| 0 | UNSET |
| 1 | OK |
| 2 | ERROR |

---

## Linking to Agora Executions

To link OTel spans to Agora workflow executions, include the `agora.execution_id` attribute:

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("my_operation") as span:
    # Link to Agora execution
    span.set_attribute("agora.execution_id", "exec-abc-123")
    
    # Your code here
    result = do_work()
```

This will populate the `execution_id` column in the `telemetry_spans` table, enabling:
- Filtering spans by execution
- Viewing execution timeline in dashboard
- Correlating LLM costs with workflow runs

---

## Resource Attributes

Resource attributes (service name, host, etc.) are automatically prefixed with `resource.` in the attributes dictionary:

**OTel Payload:**
```json
{
  "resource": {
    "attributes": [
      {"key": "service.name", "value": {"stringValue": "my-service"}}
    ]
  }
}
```

**Stored Attributes:**
```json
{
  "resource.service.name": "my-service"
}
```

---

## Multi-Tenancy

All spans are automatically stamped with `organization_id` based on the API key used for authentication. This ensures:
- **Data Isolation**: Organizations can only see their own telemetry
- **Secure Access**: Row-level security enforced by Supabase
- **Automatic Routing**: No need to manually specify organization

---

## Performance

### Bulk Insert

Spans are inserted in batches of **100** for optimal performance:

```python
BATCH_SIZE = 100

for i in range(0, len(flat_spans), BATCH_SIZE):
    batch = flat_spans[i:i + BATCH_SIZE]
    supabase.table("telemetry_spans").insert(batch).execute()
```

### Recommended Limits

- **Max Payload Size**: 10MB
- **Max Spans per Request**: 1000
- **Rate Limit**: 100 requests/minute per organization

---

## Example: Traceloop Integration

### Python

```python
from traceloop.sdk import Traceloop
from openai import OpenAI

# Initialize Traceloop
Traceloop.init(
    api_endpoint="https://api.agora.com/telemetry/traces",
    headers={"Authorization": "Bearer agora_kZm1BBglxdHyEyaz1NmpxowSLbYvZWyK"}
)

# Use OpenAI normally - telemetry is automatic
client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Explain quantum computing"}]
)

print(response.choices[0].message.content)
```

### JavaScript/TypeScript

```typescript
import * as traceloop from "@traceloop/node-server-sdk";
import OpenAI from "openai";

// Initialize Traceloop
traceloop.initialize({
  apiEndpoint: "https://api.agora.com/telemetry/traces",
  headers: {
    Authorization: "Bearer agora_kZm1BBglxdHyEyaz1NmpxowSLbYvZWyK"
  }
});

// Use OpenAI normally
const openai = new OpenAI();
const response = await openai.chat.completions.create({
  model: "gpt-4",
  messages: [{ role: "user", content: "Explain quantum computing" }]
});

console.log(response.choices[0].message.content);
```

---

## Troubleshooting

### 401 Unauthorized

**Cause**: Invalid or missing API key

**Solution**: 
- Verify API key starts with `agora_`
- Check key is not revoked in dashboard
- Ensure header format is correct: `Authorization: Bearer agora_xxx`

### 422 Validation Error

**Cause**: Invalid OTel payload structure

**Solution**:
- Verify payload matches OTel JSON schema
- Check required fields: `traceId`, `spanId`, `name`, `startTimeUnixNano`, `endTimeUnixNano`
- Ensure IDs are valid hex strings (32 chars for trace, 16 for span)

### Spans Not Appearing in Dashboard

**Possible Causes**:
1. **Wrong Organization**: Check `organization_id` in response matches your dashboard
2. **Missing execution_id**: Spans without `execution_id` won't link to workflows
3. **RLS Policies**: Verify you're logged in as a user in the correct organization

---

## Database Schema

```sql
CREATE TABLE telemetry_spans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    execution_id UUID REFERENCES executions(id),
    span_id TEXT NOT NULL,
    trace_id TEXT NOT NULL,
    parent_span_id TEXT,
    name TEXT NOT NULL,
    kind TEXT,
    status TEXT,
    start_time TIMESTAMPTZ NOT NULL,
    end_time TIMESTAMPTZ,
    duration_ms INTEGER,
    attributes JSONB DEFAULT '{}',
    events JSONB DEFAULT '[]',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_telemetry_spans_trace_id ON telemetry_spans(trace_id);
CREATE INDEX idx_telemetry_spans_org_id ON telemetry_spans(organization_id);
CREATE INDEX idx_telemetry_spans_execution_id ON telemetry_spans(execution_id);
```

---

## Migration from Legacy Format

If you're currently using the legacy Agora telemetry format, both endpoints are supported:

- **Legacy**: `POST /telemetry/executions/{id}/spans` (still works)
- **OTel**: `POST /telemetry/traces` (recommended)

The legacy endpoint will be deprecated in a future release. We recommend migrating to OTel format for:
- **Better tooling**: Compatible with Jaeger, Zipkin, Grafana
- **Industry standard**: Works with any OTel exporter
- **Richer data**: Full support for events, links, and resource attributes

---

## Support

For questions or issues:
- **Documentation**: https://docs.agora.com/telemetry
- **GitHub**: https://github.com/your-org/agora/issues
- **Discord**: https://discord.gg/agora
