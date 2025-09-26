# Agora Framework

**Workflow orchestration with comprehensive audit logging and distributed tracing**

Agora is a fork of [PocketFlow](https://github.com/The-Pocket/PocketFlow) that adds comprehensive observability features while preserving PocketFlow's elegant 100-line workflow design. Where PocketFlow provides minimal, efficient workflow orchestration, Agora extends this foundation with detailed audit logging, OpenTelemetry integration, and monitoring capabilities.

## Relationship to PocketFlow

Agora builds directly upon PocketFlow's core concepts and API design. If you're familiar with PocketFlow's `Node`, `Flow`, and async patterns, you already know Agora's basic usage. We've preserved the intuitive syntax while adding observability features that make workflows traceable and auditable in production environments.

**What's the same:**
- Same workflow patterns: `Node >> Node`, `Flow.start()`, conditional routing
- Same three-phase execution: `prep()`, `exec()`, `post()`
- Same async support and batch processing capabilities
- Same clean, minimal API design

**What's different:**
- **Comprehensive Audit Logging**: Every node execution, timing, and flow transition logged to structured JSON
- **OpenTelemetry Integration**: Automatic distributed tracing with span creation and context propagation  
- **Enhanced Error Handling**: Detailed error tracking with retry counts and timing
- **Node Naming & Context**: Named nodes and context passing throughout workflows
- **Phase-Level Performance Monitoring**: Precise timing for prep/exec/post phases
- **Production Observability**: Features needed for monitoring and debugging complex workflows

## Key Features

- ** Workflow Orchestration**: PocketFlow's proven node-based architecture
- ** Comprehensive Audit Logging**: Track every execution with detailed JSON audit trails
- ** OpenTelemetry Integration**: Built-in distributed tracing and observability
- ** Async & Sync Support**: Full support for both synchronous and asynchronous workflows
- ** Retry Logic & Error Handling**: Robust error handling with configurable retry mechanisms
- ** Batch Processing**: Sequential and parallel batch processing capabilities
- ** Conditional Flow Control**: Dynamic workflow routing based on execution results
- ** Visual Flow Diagrams**: Generate Mermaid diagrams of your workflows

## Installation

```bash
pip install git+https://github.com/JerzyKultura/Agora.git
```

For OpenTelemetry support:
```bash
pip install git+https://github.com/JerzyKultura/Agora.git opentelemetry-api opentelemetry-sdk
```

## Quick Start

### Basic Workflow (Same as PocketFlow)

```python
from agora import Node, Flow

class ProcessData(Node):
    def exec(self, prep_res):
        return f"Processed: {prep_res}"
    
    def prep(self, shared):
        return shared.get("input", "default")

class SaveResults(Node):
    def exec(self, prep_res):
        print(f"Saving: {prep_res}")
        return "saved"

# Build the workflow (identical to PocketFlow)
process = ProcessData()
save = SaveResults()

flow = Flow()
flow.start(process) >> save

# Execute
shared = {"input": "my data"}
result = flow.run(shared)
```

### With Audit Logging (Agora Extension)

```python
from agora.telemetry import AuditLogger, AuditedNode, AuditedFlow

class DataProcessor(AuditedNode):
    def __init__(self, name, audit_logger):
        super().__init__(name, audit_logger)
    
    def exec(self, prep_res):
        # Your processing logic here
        return processed_data

# Create audit logger
logger = AuditLogger("data-pipeline-session")

# Create audited nodes with names
processor = DataProcessor("processor", logger)
flow = AuditedFlow("Pipeline", logger)

# Run workflow - same API as PocketFlow
result = flow.run(shared)

# Export detailed audit trail (new capability)
print(logger.get_summary())
logger.save_json("audit_trail.json")
```

## Core Concepts (Extended from PocketFlow)

### Nodes
Agora preserves PocketFlow's three-phase execution model but adds comprehensive logging:

```python
class CustomNode(AuditedNode):
    def prep(self, shared):
        # Same as PocketFlow - prepare data
        return shared.get("input")
    
    def exec(self, data):
        # Same as PocketFlow - main logic
        return process(data)
    
    def post(self, shared, prep_res, exec_res):
        # Same as PocketFlow - post-processing
        shared["result"] = exec_res
        return "success"

# Agora automatically logs timing for each phase:
# {"prep": 1.2ms, "exec": 450.8ms, "post": 0.5ms}
```

### Flows
Same conditional routing as PocketFlow, with automatic transition logging:

```python
flow = AuditedFlow("ConditionalFlow", audit_logger)
flow.start(validator)

# Same PocketFlow syntax
validator - "valid" >> processor
validator - "invalid" >> error_handler
processor >> success_handler

# Agora logs: validator->processor (action: valid)
```

## Observability Features (Agora Extensions)

### Automatic Audit Logging

Every execution is logged with structured data:

```python
# Example audit log entry
{
    "event_type": "node_success",
    "node_name": "DataProcessor", 
    "node_type": "AuditedNode",
    "latency_ms": 234.5,
    "phase_latencies": {"prep": 1.2, "exec": 230.1, "post": 3.2},
    "timestamp": "2024-01-15T10:30:00Z"
}
```

### OpenTelemetry Integration

Built-in distributed tracing with automatic span creation:

```python
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

# Setup tracing
trace.set_tracer_provider(TracerProvider())

# Nodes automatically create spans with detailed attributes
logger = AuditLogger()  # Auto-detects OpenTelemetry setup
audited_node = AuditedNode("traced-node", audit_logger=logger)
```

### Visual Diagrams

Generate workflow visualizations (same API as PocketFlow):

```python
flow = Flow("MyWorkflow")
# ... build your flow

# Generate Mermaid diagram
mermaid_code = flow.to_mermaid()
print(mermaid_code)
# graph TD
#     NodeA --> NodeB
#     NodeB -->|success| NodeC
```

## Async Support (Enhanced from PocketFlow)

```python
from agora import AsyncNode, AsyncFlow
from agora.telemetry import AuditedAsyncNode, AuditedAsyncFlow

class AsyncProcessor(AuditedAsyncNode):
    async def exec_async(self, prep_res):
        await asyncio.sleep(1)  # Async operation
        return {"data": "processed"}

# Same async patterns as PocketFlow, with full audit logging
async def main():
    processor = AsyncProcessor("async-processor", audit_logger)
    flow = AuditedAsyncFlow("AsyncPipeline", audit_logger)
    flow.start(processor)
    
    result = await flow.run_async({})
    print(result)
```


## License

MIT License - see [LICENSE](LICENSE) file for details.

## Acknowledgments

Agora is built upon [PocketFlow](https://github.com/The-Pocket/PocketFlow)'s elegant workflow design. PocketFlow's 100-line implementation demonstrates that powerful workflow orchestration doesn't require complexity. Agora extends this philosophy by adding the observability features needed for production use while preserving PocketFlow's clean, intuitive API.

Special thanks to @zachary62 for creating such an elegant foundation to build upon.
