"""
Example: Using Agora with Cloud Platform + OpenTelemetry Spans

This example uses TracedAsyncNode which captures proper OpenTelemetry spans!
"""

import asyncio
from agora.agora_tracer import TracedAsyncNode, TracedAsyncFlow, init_traceloop
from agora.cloud_client import CloudAuditLogger

# ============================================================================
# STEP 1: Get Your API Key from the Platform
# ============================================================================
API_KEY = "aagora_key_hraf8PI8-sKCmD_heUmOaOg00-OYwLNKrwGX4amN6B8"

# ============================================================================
# STEP 2: Define Your Workflow with TracedAsyncNode (captures spans!)
# ============================================================================

class DataProcessor(TracedAsyncNode):
    """Process some data"""
    
    async def prep_async(self, shared):
        return shared.get("input", "default data")
    
    async def exec_async(self, data):
        print(f"📝 Processing: {data}")
        result = data.upper()
        return result
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["processed"] = exec_res
        return "validate"


class Validator(TracedAsyncNode):
    """Validate the processed data"""
    
    async def prep_async(self, shared):
        return shared.get("processed", "")
    
    async def exec_async(self, data):
        print(f"✅ Validating: {data}")
        is_valid = len(data) > 0
        return {"valid": is_valid, "data": data}
    
    async def post_async(self, shared, prep_res, exec_res):
        if exec_res["valid"]:
            shared["final_result"] = exec_res["data"]
            return "success"
        return "error"


class SuccessHandler(TracedAsyncNode):
    """Handle successful completion"""
    
    async def exec_async(self, prep_res):
        print("🎉 Workflow completed successfully!")
        return "done"


# ============================================================================
# STEP 3: Custom OTel Exporter for CloudAuditLogger
# ============================================================================

from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace import ReadableSpan
from typing import Sequence

class CloudAuditLoggerExporter(SpanExporter):
    """Captures OTel spans and sends them to CloudAuditLogger"""
    
    def __init__(self, logger):
        self.logger = logger
        self.spans = []
    
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Called by OTel when spans complete"""
        from datetime import datetime
        
        for span in spans:
            # Convert nanosecond timestamps to ISO datetime strings
            start_dt = datetime.fromtimestamp(span.start_time / 1_000_000_000)
            end_dt = datetime.fromtimestamp(span.end_time / 1_000_000_000)
            
            # Convert OTel span to our format
            span_data = {
                "span_id": format(span.context.span_id, '016x'),
                "trace_id": format(span.context.trace_id, '032x'),
                "parent_span_id": format(span.parent.span_id, '016x') if span.parent else None,
                "name": span.name,
                "kind": str(span.kind),
                "status": span.status.status_code.name,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "duration_ms": int((span.end_time - span.start_time) / 1_000_000),  # nanoseconds to ms, as int
                "attributes": dict(span.attributes or {}),
                "events": [
                    {
                        "name": e.name,
                        "timestamp": datetime.fromtimestamp(e.timestamp / 1_000_000_000).isoformat(),
                        "attributes": dict(e.attributes or {})
                    }
                    for e in span.events
                ]
            }
            self.spans.append(span_data)
            
        return SpanExportResult.SUCCESS
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
    
    def shutdown(self):
        pass


# ============================================================================
# STEP 4: Run Workflow with Full Telemetry
# ============================================================================

async def run_workflow_async(input_data: str):
    """
    Run workflow with OpenTelemetry spans captured!
    """
    
    print(f"\n{'='*70}")
    print(f"🚀 Running Agora Workflow with Cloud Platform + OpenTelemetry")
    print(f"{'='*70}")
    print(f"Workflow: MyAwesomeWorkflow\n")
    
    # Create cloud logger
    logger = CloudAuditLogger(
        api_key=API_KEY,
        workflow_name="MyAwesomeWorkflow"
    )
    
    # Create custom exporter that captures spans
    span_exporter = CloudAuditLoggerExporter(logger)
    
    # Initialize Traceloop with our custom exporter
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    
    # Create tracer provider with our exporter
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(provider)
    
    # Initialize traceloop
    init_traceloop(
        app_name="MyAwesomeWorkflow",
        export_to_console=False  # Don't spam console
    )
    
    # Create nodes
    processor = DataProcessor("DataProcessor")
    validator = Validator("Validator")
    success = SuccessHandler("SuccessHandler")
    
    # Build flow
    flow = TracedAsyncFlow("MyAwesomeWorkflow")
    flow.start(processor)
    processor - "validate" >> validator
    validator - "success" >> success
    
    # Run the workflow
    try:
        shared = {"input": input_data}
        result = await flow.run_async(shared)
        
        # Inject captured spans into logger
        logger.completed_spans = span_exporter.spans
        
        # Mark complete and upload (includes spans!)
        logger.mark_complete(status="success")
        
        print(f"\n{'='*70}")
        print(f"✅ Workflow completed with {len(span_exporter.spans)} OpenTelemetry spans!")
        print(f"   Check your dashboard at: http://localhost:5173")
        print(f"{'='*70}\n")
        
        return result
        
    except Exception as e:
        logger.mark_complete(status="error", error=str(e))
        raise


# ============================================================================
# RUN IT!
# ============================================================================

if __name__ == "__main__":
    # Check if API key is set
    if API_KEY == "agora_key_PASTE_YOUR_KEY_HERE":
        print("\n" + "="*70)
        print("⚠️  PLEASE SET YOUR API KEY FIRST!")
        print("="*70)
        print("\nSteps:")
        print("1. Go to http://localhost:5173/api-keys")
        print("2. Click 'Generate New API Key'")
        print("3. Copy the key")
        print("4. Paste it in this script where it says:")
        print("   API_KEY = \"agora_key_PASTE_YOUR_KEY_HERE\"")
        print("\nThen run this script again!")
        print("="*70 + "\n")
    else:
        # Run the async workflow
        result = asyncio.run(run_workflow_async("hello world from agora with spans!"))
        print(f"Final result: {result}")