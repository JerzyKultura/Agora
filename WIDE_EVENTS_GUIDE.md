# Wide Events / Business Context Enrichment Guide

## What Are Wide Events?

**Wide events** are comprehensive, context-rich telemetry events that contain everything you need to debug an issue. Instead of logging what your code is doing across 20 log lines, you emit one event per request with all the business context attached.

### The Problem with Traditional Logging

```python
# Traditional approach - hard to debug
logger.info("Processing request")
logger.debug(f"User ID: {user_id}")
logger.debug(f"Subscription: {subscription}")
logger.info("Calling LLM")
response = client.chat.completions.create(...)
logger.info("LLM call complete")
```

**Issues:**
- 5 separate log lines for one request
- Hard to correlate across services
- Missing business context (is this a VIP user? What feature flags?)
- Can't query efficiently ("show me errors for premium users")

### The Wide Events Solution

```python
from agora.wide_events import BusinessContext, enrich_current_span

# Build business context
context = BusinessContext(
    user_id=user.id,
    subscription_tier=user.subscription,
    lifetime_value_cents=user.ltv,
    feature_flags={"gpt4_access": True},
    workflow_type="customer_support"
)

# Enrich the span BEFORE making the LLM call
enrich_current_span(context)

# Make the call (Traceloop auto-instruments this)
response = client.chat.completions.create(...)
```

**Result:** One span with ALL context:
- User details (subscription, LTV, account age)
- Feature flags
- Session info
- Business metrics
- Prompt/completion content
- Token usage
- Everything!

## Why This Matters

### Traditional Debugging

User reports: *"The AI gave me a wrong answer"*

You search logs:
```
2024-01-15 10:23:45 INFO Processing request
2024-01-15 10:23:46 INFO LLM call complete
```

You know... nothing. No user context. No feature flags. No business metrics.

### Wide Events Debugging

Same user report, but with wide events:

```sql
SELECT * FROM telemetry_spans
WHERE user_id = 'user_456'
AND timestamp > NOW() - INTERVAL '1 hour'
```

You instantly see:
- ✅ User is **enterprise** tier (high priority!)
- ✅ They have **$1,500 LTV** (VIP customer!)
- ✅ Feature flag `new_model_v2` was **enabled** (potential correlation!)
- ✅ This was their **15th message** in the session (context matters!)
- ✅ The actual prompt and completion
- ✅ Token usage and cost

You can now ask questions like:
- *"Is this only affecting enterprise users?"*
- *"Is the new model causing issues?"*
- *"Are long conversations more error-prone?"*

## How to Use It

### Basic Usage

```python
from agora.agora_tracer import init_agora
from agora.wide_events import BusinessContext, enrich_current_span
from traceloop.sdk import Traceloop
from openai import OpenAI

# Initialize telemetry
Traceloop.init(app_name="my-app", disable_batch=True)
init_agora(app_name="my-app", enable_cloud_upload=True)

client = OpenAI()

# In your request handler
def handle_chat(user, session, message):
    # Build business context
    context = BusinessContext(
        user_id=user.id,
        subscription_tier=user.subscription,
        lifetime_value_cents=user.ltv,
        session_id=session.id,
        conversation_turn=session.turn_number,
        feature_flags={
            "new_ui": user.has_flag("new_ui"),
            "gpt4_access": user.can_use_gpt4()
        }
    )

    # Enrich the span
    enrich_current_span(context)

    # Make LLM call (automatically instrumented)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": message}]
    )

    return response.choices[0].message.content
```

### Quick Helpers

For simpler cases:

```python
from agora.wide_events import enrich_with_user, enrich_with_feature_flags

# Quick user enrichment
enrich_with_user(
    user_id="user_123",
    subscription_tier="premium",
    lifetime_value_cents=50000
)

# Quick feature flag enrichment
enrich_with_feature_flags({
    "beta_features": True,
    "advanced_mode": False
})

# Make your LLM call
response = client.chat.completions.create(...)
```

## What Context to Add

### Always Include:
1. **User Identity**
   - `user_id` - for searching
   - `user_email` - for customer support
   - `subscription_tier` - for prioritizing issues

2. **Feature Flags**
   - Every experiment/rollout flag
   - Helps identify if new features are causing issues

3. **Session Context**
   - `session_id` - group related requests
   - `conversation_turn` - understand conversation flow

### Consider Including:
4. **Business Metrics**
   - `lifetime_value_cents` - prioritize VIP users
   - `account_age_days` - new vs old users
   - `cart_value_cents` - revenue at risk

5. **App-Specific Context**
   - `workflow_type` - support vs sales vs research
   - `priority` - high vs normal
   - `app_version` - track version-specific issues

6. **Custom Attributes**
   - Anything specific to your domain
   - Time of day, location, device type, etc.

## Available Fields

The `BusinessContext` class supports:

```python
context = BusinessContext(
    # User context
    user_id="user_123",
    user_email="user@example.com",
    subscription_tier="premium",  # or "free", "enterprise"
    lifetime_value_cents=150000,  # $1,500
    account_age_days=365,          # 1 year old account

    # Session context
    session_id="sess_abc",
    conversation_turn=5,           # 5th message in conversation
    total_tokens_this_session=2500,

    # Feature flags (dict of flag_name -> bool)
    feature_flags={
        "new_ui": True,
        "gpt4_access": True,
        "experimental_mode": False
    },

    # App-specific
    workflow_type="customer_support",  # or "sales", "research", etc.
    priority="high",                   # or "normal", "low"
    app_version="1.2.3",

    # Business metrics
    cart_value_cents=50000,  # $500 cart
    items_in_cart=3,

    # Custom attributes (dict of any key-value pairs)
    custom={
        "device_type": "mobile",
        "time_zone": "America/New_York",
        "referrer": "google_search",
        "is_vip": True
    }
)
```

All fields are optional - add what makes sense for your use case.

## Viewing the Data

### In the Monitoring Dashboard

1. Open http://localhost:5173/monitoring
2. Click the **Traces** tab
3. Click on a trace
4. Click on the **openai.chat** span
5. View tabs:
   - **Prompt** - See the input messages
   - **Completions** - See the AI response
   - **LLM Data** - Model, tokens, cost
   - **Details** - **YOUR BUSINESS CONTEXT IS HERE!**
   - **Raw** - Complete JSON

### Querying with SQL

If you export your Supabase data to BigQuery/ClickHouse/etc., you can run queries like:

```sql
-- Error rate by subscription tier
SELECT
  attributes->>'user.subscription_tier' as tier,
  COUNT(*) FILTER (WHERE status = 'ERROR') as errors,
  COUNT(*) as total,
  ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'ERROR') / COUNT(*), 2) as error_rate_pct
FROM telemetry_spans
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY tier;

-- Slow requests for VIP users
SELECT
  trace_id,
  attributes->>'user.id' as user_id,
  attributes->>'user.lifetime_value_cents' as ltv,
  duration_ms
FROM telemetry_spans
WHERE duration_ms > 2000
  AND (attributes->>'user.lifetime_value_cents')::int > 100000
ORDER BY duration_ms DESC;

-- Feature flag impact
SELECT
  attributes->>'feature_flags.new_model_v2' as has_flag,
  COUNT(*) FILTER (WHERE status = 'ERROR') as errors,
  COUNT(*) as total
FROM telemetry_spans
WHERE created_at > NOW() - INTERVAL '1 day'
GROUP BY has_flag;
```

## Real-World Example

See `examples/chatbot_with_wide_events.py` for a complete working example.

```bash
python examples/chatbot_with_wide_events.py
```

## Testing in Google Colab

We have a test script specifically for Colab:

1. Open Google Colab
2. Create a new notebook
3. Copy the contents of `test_colab.py`
4. Paste your API keys (OpenAI, Supabase)
5. Run the cell
6. Check your localhost dashboard

The script demonstrates:
- How to enrich spans with business context
- What the enriched data looks like
- How to use quick helper methods

## Comparison with Traditional Logging

| Traditional Logs | Wide Events |
|-----------------|-------------|
| 20+ log lines per request | 1 event per request per service |
| Missing business context | Rich business context included |
| Hard to correlate | Everything grouped by trace_id |
| String search only | Structured querying (SQL) |
| "What happened?" | "What happened, to whom, why, and in what context?" |

## Best Practices

### DO:
✅ Add context **before** the LLM call (so errors have context)
✅ Include user subscription tier (helps prioritize)
✅ Include feature flags (track experiment impact)
✅ Include business metrics (LTV, cart value, etc.)
✅ Use meaningful custom attributes for your domain

### DON'T:
❌ Add sensitive PII (passwords, credit cards, SSNs)
❌ Add hundreds of fields (keep it focused)
❌ Forget to enrich before the operation
❌ Rely only on auto-instrumentation (add your context!)

## Cost Management

Wide events mean more data. Use sampling:

```python
# In agora_tracer.py, implement tail sampling
def should_keep_span(span):
    # Always keep errors
    if span.status == 'ERROR':
        return True

    # Always keep slow requests
    if span.duration_ms > 2000:
        return True

    # Always keep VIP users
    if span.attributes.get('user.subscription_tier') == 'enterprise':
        return True

    # Sample 5% of successful requests
    return random.random() < 0.05
```

## Further Reading

This pattern is inspired by:
- **Stripe's Canonical Log Lines** - https://stripe.com/blog/canonical-log-lines
- **Honeycomb's Wide Events** - https://www.honeycomb.io/blog/how-are-structured-logs-different-from-events
- The article you shared about modern observability

## Summary

**Wide events = One comprehensive event with all business context**

Instead of searching through scattered logs, you query structured data with full context. This makes debugging 100x faster and enables powerful analytics.

The key insight: **Logs optimized for writing are terrible for querying. Wide events are optimized for querying.**

Agora gives you this superpower with one simple pattern:

```python
context = BusinessContext(user_id=..., subscription_tier=..., feature_flags=...)
enrich_current_span(context)
# Make your LLM call
```

That's it. Now your telemetry tells the whole story.
