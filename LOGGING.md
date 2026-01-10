# Comprehensive Logging in Agora SDK

## Overview

Agora SDK now includes **exhaustive, step-by-step logging** throughout all execution paths to make debugging and analysis trivial. Every decision, retry, state change, and error condition emits detailed log statements.

## Philosophy

> **"Logs are the primary source of truth."**

The logging system follows these principles:

1. **Exhaustive Coverage**: Missing or partial logs hide root causes. Every execution path emits logs.
2. **Verbose by Design**: Step-by-step logging is preferred over conciseness in debug mode.
3. **All Paths Logged**: Success, failure, and early exit paths all emit logs.
4. **Cross-Layer Correlation**: Logs track execution from SDK → exporter → backend → UI.

## Quick Start

### Enable Verbose Logging

```python
from agora.logging_config import enable_verbose_logging

# Enable DEBUG-level logging across ALL Agora modules
enable_verbose_logging()

# Now run your workflow - every step will be logged
from agora import AsyncFlow, AsyncNode

# ... your workflow code ...
```

### Example Output

When you enable verbose logging, you'll see:

```
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncFlow.run_async:601] AsyncFlow ExampleFlow: Public run_async() called, context=None
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncFlow._run_async:572] AsyncFlow ExampleFlow: === ASYNC FLOW EXECUTION START ===
[2026-01-10 12:00:00] [DEBUG   ] [agora.AsyncFlow._run_async:573] AsyncFlow ExampleFlow: Initial shared state keys: []
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncFlow._orch_async:538] AsyncFlow ExampleFlow: === ASYNC FLOW ORCHESTRATION START ===
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncFlow._orch_async:549] AsyncFlow ExampleFlow: --- Orchestration Step 1: Executing node Start ---
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncNode._run_async:389] AsyncNode Start: === ASYNC NODE EXECUTION START ===
[2026-01-10 12:00:00] [DEBUG   ] [agora.AsyncNode._run_async:396] AsyncNode Start: Starting prep_async phase
[2026-01-10 12:00:00] [DEBUG   ] [agora.AsyncNode._run_async:400] AsyncNode Start: Starting exec_async phase
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncNode._exec_async:375] AsyncNode Start: Execution succeeded on attempt 1/1
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncNode._run_async:411] AsyncNode Start: === ASYNC NODE EXECUTION SUCCESS === (result=process)
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncFlow._orch_async:556] AsyncFlow ExampleFlow: Node Start returned action='process'
[2026-01-10 12:00:00] [INFO    ] [agora.AsyncFlow.get_next_node:518] AsyncFlow ExampleFlow: Routing decision: Start --[process]--> Process
```

## What Gets Logged?

### SDK Core (`agora/__init__.py`)

**Node Lifecycle:**
- ✅ Node creation with configuration
- ✅ Successor registration and routing setup
- ✅ Each phase execution (prep, exec, post)
- ✅ Before/after run hooks
- ✅ Shared state keys at each step

**Retry Logic:**
- ✅ Each retry attempt with attempt number
- ✅ Wait duration before retry
- ✅ Success or failure of each attempt
- ✅ Fallback handler invocation

**Flow Orchestration:**
- ✅ Flow start and end
- ✅ Each orchestration step with node name
- ✅ Routing decisions (action → next node)
- ✅ Shared state evolution
- ✅ Flow completion with result

**Batch Operations:**
- ✅ Batch size (input/output)
- ✅ Sequential vs parallel processing
- ✅ Per-item progress

### Telemetry (`agora/telemetry.py`)

**AuditLogger:**
- ✅ Session creation with session ID
- ✅ Event logging (node_start, node_success, node_error, flow_transition)
- ✅ Span creation and hierarchy
- ✅ Span attributes and duration
- ✅ JSON export operations
- ✅ Trace save operations

**Span Management:**
- ✅ Root span creation
- ✅ Child span creation with parent linking
- ✅ Span hierarchy tracking
- ✅ Span attribute setting
- ✅ Span completion (success/error)
- ✅ Parent-child relationship mapping

### Event Engine (`agora/engine.py`)

**Flow Execution:**
- ✅ Flow cycle start/end
- ✅ Cycle count tracking (prevents infinite loops)
- ✅ Recursion detection and logging
- ✅ Metrics collection

**Retry with Exponential Backoff:**
- ✅ Each retry attempt
- ✅ Current delay and next delay calculation
- ✅ Error handler invocation
- ✅ Success on specific attempt

### Supabase Uploader (`agora/supabase_uploader.py`)

**Initialization:**
- ✅ Configuration validation
- ✅ Credential presence check
- ✅ Supabase client creation
- ✅ API key verification

**Upload Operations:**
- ✅ Batch buffer state
- ✅ Retry attempts with exponential backoff
- ✅ Schema mismatch detection (PGRST204)
- ✅ Column stripping on mismatch
- ✅ Upload success/failure

## Logging Levels

| Level | When to Use | What Gets Logged |
|-------|-------------|------------------|
| **DEBUG** | Development, debugging | Everything - every decision, every variable, every step |
| **INFO** | Production monitoring | Major events - node start/end, flow transitions, success/failure |
| **WARNING** | Anomaly detection | Retries, schema mismatches, unexpected conditions |
| **ERROR** | Failure investigation | Errors, exceptions, fallback handlers |
| **CRITICAL** | System failures | Unrecoverable errors |

## Configuration Options

### 1. Verbose Console Logging

```python
from agora.logging_config import enable_verbose_logging

# Debug level - see everything
enable_verbose_logging(level="DEBUG")

# Info level - major events only
enable_verbose_logging(level="INFO")
```

### 2. File Logging with Rotation

```python
from agora.logging_config import enable_file_logging

# Log to file with 10MB rotation, keep 5 backups
enable_file_logging("agora_debug.log")

# Custom configuration
enable_file_logging(
    "agora.log",
    level="DEBUG",
    max_bytes=50 * 1024 * 1024,  # 50MB
    backup_count=10
)
```

### 3. Structured JSON Logging

Perfect for log aggregation systems (ELK, Datadog, Splunk):

```python
from agora.logging_config import setup_structured_logging

setup_structured_logging(level="INFO")
```

Output format:
```json
{
  "timestamp": "2026-01-10T12:00:00.123456",
  "level": "INFO",
  "logger": "agora",
  "function": "run_async",
  "line": 601,
  "message": "AsyncFlow ExampleFlow: Public run_async() called",
  "correlation_id": "req-12345"
}
```

### 4. Correlation IDs for Cross-Layer Tracking

Track a single request across SDK → backend → UI:

```python
from agora.logging_config import set_correlation_id, enable_verbose_logging

enable_verbose_logging()
set_correlation_id("request-abc-123")

# All logs will now include correlation_id: "request-abc-123"
# Filter logs by this ID to see the entire request path
```

## Debugging Workflows

### Problem: Node is failing, but I don't know why

**Solution:**
```python
from agora.logging_config import enable_verbose_logging
enable_verbose_logging(level="DEBUG")

# Run your workflow
# Search logs for the node name to see:
# - What data it received (prep phase)
# - What it tried to execute (exec phase)
# - Retry attempts and errors
# - Shared state at that point
```

### Problem: Flow is taking an unexpected path

**Solution:**
```python
# Enable verbose logging
enable_verbose_logging()

# Look for routing decision logs:
# [INFO] AsyncFlow.get_next_node: Routing decision: NodeA --[action]--> NodeB
#
# This shows exactly which action led to which node
```

### Problem: Retries are happening, but I don't know how many

**Solution:**
```python
# Logs show each retry attempt:
# [DEBUG] Node._exec: Node MyNode: Retry attempt 1/3
# [WARNING] Node._exec: Attempt 1/3 failed: ValueError: ...
# [DEBUG] Node._exec: Waiting 1.0s before retry 2/3
# [DEBUG] Node._exec: Retry attempt 2/3
# [INFO] Node._exec: Execution succeeded on attempt 2/3
```

### Problem: Uploads to Supabase are failing

**Solution:**
```python
# Logs show detailed upload attempts:
# [DEBUG] SupabaseUploader._with_retry: Starting retry loop: max_retries=3
# [DEBUG] SupabaseUploader._with_retry: Attempt 1/3
# [WARNING] SupabaseUploader._with_retry: Attempt 1/3 failed: PGRST204: Missing column 'xyz'
# [ERROR] SupabaseUploader._with_retry: Schema mismatch detected: Missing column 'xyz', attempting to strip
# [DEBUG] SupabaseUploader._with_retry: Stripped 'xyz' from 5 items in list
# [INFO] SupabaseUploader._with_retry: Success on attempt 2
```

## Log Format Reference

### Standard Format (Verbose)

```
[timestamp] [level] [module:function:line] message
```

Example:
```
[2026-01-10 12:00:00] [INFO] [agora.AsyncNode._run_async:411] AsyncNode Start: === ASYNC NODE EXECUTION SUCCESS ===
```

### Components

- **timestamp**: UTC time in `YYYY-MM-DD HH:MM:SS` format
- **level**: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- **module**: Python module name (e.g., `agora`, `agora.telemetry`)
- **function**: Function name where log was emitted
- **line**: Line number in source file
- **message**: The log message with context

### Log Message Patterns

Messages follow a structured format:

```
[ModuleName.method_name] ClassName object_name: Event description (details)
```

Examples:
```
[AsyncNode._run_async] AsyncNode Start: === ASYNC NODE EXECUTION START ===
[Flow._orch] Flow ExampleFlow: --- Orchestration Step 1: Executing node Start ---
[SupabaseUploader._with_retry] upload_spans: Attempt 1/3
[EventEngine._run_flow_cycle] === FLOW CYCLE 1/100 STARTING ===
```

## Best Practices

### 1. Always Enable Logging During Development

```python
# Put this at the top of your script
from agora.logging_config import enable_verbose_logging
enable_verbose_logging()
```

### 2. Use File Logging for Long-Running Processes

```python
from agora.logging_config import enable_file_logging
enable_file_logging("agora_production.log", level="INFO")
```

### 3. Use Correlation IDs in Multi-Request Systems

```python
from agora.logging_config import set_correlation_id
import uuid

# At request start
request_id = str(uuid.uuid4())
set_correlation_id(request_id)

# All logs will include this ID
# Clear it when done
from agora.logging_config import clear_correlation_id
clear_correlation_id()
```

### 4. Disable Logging in Performance-Critical Production

```python
from agora.logging_config import enable_simple_logging
enable_simple_logging(level="WARNING")  # Only warnings and errors
```

### 5. Grep/Filter Logs Effectively

```bash
# Find all logs for a specific node
grep "Node MyNodeName" agora_debug.log

# Find all retry attempts
grep "Retry attempt" agora_debug.log

# Find all errors
grep "\[ERROR\]" agora_debug.log

# Follow log in real-time
tail -f agora_debug.log
```

## Integration with Existing Telemetry

Agora's logging system complements (doesn't replace) existing telemetry:

| System | Purpose | What It Logs |
|--------|---------|--------------|
| **Python logging** | Step-by-step execution details | Every decision, retry, state change |
| **AuditLogger** | Structured event timeline | node_start, node_success, flow_transition |
| **OpenTelemetry** | Distributed tracing | Span hierarchy, latencies, attributes |
| **Supabase** | Persistent telemetry storage | Execution records, spans, metrics |

Use them together for complete observability:
- **Logs**: Understand *what* happened and *why*
- **Events**: Timeline of major state changes
- **Spans**: Hierarchical performance breakdown
- **Metrics**: Aggregate statistics

## Troubleshooting

### Logs aren't appearing

**Check:** Is logging configured before importing Agora modules?

```python
# ✅ Correct
from agora.logging_config import enable_verbose_logging
enable_verbose_logging()

from agora import AsyncFlow, AsyncNode

# ❌ Wrong
from agora import AsyncFlow, AsyncNode
from agora.logging_config import enable_verbose_logging
enable_verbose_logging()  # Too late - modules already initialized
```

### Too much output

**Solution:** Use INFO level instead of DEBUG:

```python
enable_verbose_logging(level="INFO")
```

### Want logs only for specific modules

```python
import logging

# Enable verbose for everything
from agora.logging_config import enable_verbose_logging
enable_verbose_logging()

# But silence specific modules
logging.getLogger("agora.telemetry").setLevel(logging.WARNING)
logging.getLogger("agora.supabase_uploader").setLevel(logging.ERROR)
```

## Examples

See `examples/enable_verbose_logging.py` for a complete working example.

## Future Enhancements

Planned improvements to the logging system:

- [ ] Performance metrics logging (execution time, memory usage)
- [ ] Automatic sensitive data redaction
- [ ] Log sampling for high-volume production
- [ ] Integration with APM systems (New Relic, Datadog)
- [ ] Web-based log viewer UI

## Feedback

Found a missing log that would have helped debugging? Please open an issue!

We want logs to be the **primary source of truth** for debugging. If something isn't logged that should be, we want to know.
