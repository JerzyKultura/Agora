"""
Cloud client for Agora Platform integration with automatic OpenTelemetry capture.

Usage:
    from agora.cloud_client import CloudAuditLogger
    from agora.agora_tracer import agora_node, TracedAsyncFlow
    
    # Just create the logger - spans captured automatically!
    logger = CloudAuditLogger(
        api_key="agora_key_abc123",
        workflow_name="MyWorkflow"
    )
    
    # Define your nodes
    @agora_node
    async def my_node(shared):
        return "done"
    
    # Build and run flow
    flow = TracedAsyncFlow("MyWorkflow")
    flow.start(my_node)
    result = await flow.run_async(shared)
    
    # Upload automatically captures all OTel spans!
    logger.upload()
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from agora.telemetry import AuditLogger

# OpenTelemetry imports (optional - gracefully degrade if not installed)
try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult, SimpleSpanProcessor
    from opentelemetry.sdk.trace import ReadableSpan
    from typing import Sequence
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False


class _CloudSpanExporter(SpanExporter):
    """Internal exporter that captures OTel spans for CloudAuditLogger"""
    
    def __init__(self):
        self.spans = []
    
    def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
        """Convert OTel spans to platform format"""
        for span in spans:
            # Convert nanosecond timestamps to ISO datetime
            start_dt = datetime.fromtimestamp(span.start_time / 1_000_000_000)
            end_dt = datetime.fromtimestamp(span.end_time / 1_000_000_000)
            
            span_data = {
                "span_id": format(span.context.span_id, '016x'),
                "trace_id": format(span.context.trace_id, '032x'),
                "parent_span_id": format(span.parent.span_id, '016x') if span.parent else None,
                "name": span.name,
                "kind": str(span.kind),
                "status": span.status.status_code.name,
                "start_time": start_dt.isoformat(),
                "end_time": end_dt.isoformat(),
                "duration_ms": int((span.end_time - span.start_time) / 1_000_000),
                "attributes": dict(span.attributes or {}),
                "events": []
            }
            self.spans.append(span_data)
            
        return SpanExportResult.SUCCESS
    
    def force_flush(self, timeout_millis: int = 30000) -> bool:
        return True
    
    def shutdown(self):
        pass


class CloudAuditLogger(AuditLogger):
    """
    Audit logger that automatically captures OpenTelemetry spans and sends to Agora Cloud.
    
    Simple Usage:
        logger = CloudAuditLogger(
            api_key="agora_key_abc123",
            workflow_name="MyWorkflow"
        )
        
        # Use with TracedAsyncNode/TracedAsyncFlow
        # Spans are captured automatically!
        
        await flow.run_async(shared)
        logger.upload()  # Uploads with all captured spans
    """

    def __init__(
        self,
        api_key: str,
        workflow_name: str,
        api_url: str = "http://localhost:8000",
        session_id: Optional[str] = None,
        auto_upload: bool = True,
        capture_spans: bool = True
    ):
        """
        Initialize CloudAuditLogger with automatic OTel span capture.

        Args:
            api_key: Your Agora platform API key
            workflow_name: Name of your workflow
            api_url: Base URL of Agora Platform API
            session_id: Optional unique identifier for this execution
            auto_upload: If True, automatically upload on mark_complete()
            capture_spans: If True, automatically capture OpenTelemetry spans (default: True)
        """
        session_id = session_id or f"session-{int(datetime.now().timestamp())}"
        super().__init__(session_id)
        
        self.api_key = api_key
        self.workflow_name = workflow_name
        self.api_url = api_url.rstrip("/")
        self.auto_upload = auto_upload
        
        self.execution_start_time = datetime.now()
        self.execution_end_time: Optional[datetime] = None
        self.execution_status = "running"
        self.execution_error: Optional[str] = None
        
        # Setup automatic span capture
        self._span_exporter = None
        if capture_spans and OTEL_AVAILABLE:
            self._setup_span_capture()
        elif capture_spans and not OTEL_AVAILABLE:
            print("⚠️  OpenTelemetry not installed. Install with: pip install opentelemetry-api opentelemetry-sdk")

    def _setup_span_capture(self):
        """Setup OpenTelemetry to automatically capture spans"""
        try:
            # Create our custom exporter
            self._span_exporter = _CloudSpanExporter()
            
            # Get or create tracer provider
            provider = trace.get_tracer_provider()
            
            # If no provider set yet, create one
            if not isinstance(provider, TracerProvider):
                provider = TracerProvider()
                trace.set_tracer_provider(provider)
            
            # Add our exporter as a processor
            provider.add_span_processor(SimpleSpanProcessor(self._span_exporter))
            
            print(f"✅ OpenTelemetry span capture enabled for {self.workflow_name}")
        except Exception as e:
            print(f"⚠️  Failed to setup span capture: {e}")
            self._span_exporter = None

    def mark_complete(self, status: str = "success", error: Optional[str] = None):
        """Mark execution as complete."""
        self.execution_end_time = datetime.now()
        self.execution_status = status
        self.execution_error = error

        if self.auto_upload:
            self.upload()

    def _convert_events_to_node_executions(self) -> List[Dict[str, Any]]:
        """Convert audit events into node execution records."""
        node_executions = []
        node_data = {}

        # Group events by node
        for event in self.events:
            node_name = event.get("node_name")
            if not node_name:
                continue

            if node_name not in node_data:
                node_data[node_name] = {
                    "node_name": node_name,
                    "node_type": event.get("node_type", "Unknown"),
                    "events": []
                }

            node_data[node_name]["events"].append(event)

        # Convert to node execution records
        for node_name, data in node_data.items():
            events = data["events"]

            # Find start and end events
            start_event = next((e for e in events if e.get("event_type") == "node_start"), None)
            success_event = next((e for e in events if e.get("event_type") == "node_success"), None)
            error_event = next((e for e in events if e.get("event_type") == "node_error"), None)

            if not start_event:
                continue

            end_event = success_event or error_event
            status = "success" if success_event else ("error" if error_event else "running")

            # Extract phase latencies
            phase_latencies = (success_event or error_event or {}).get("phase_latencies", {})

            # Use placeholder UUID (backend will map to actual node_id)
            node_id = "00000000-0000-0000-0000-000000000000"

            node_exec = {
                "node_id": node_id,
                "node_name": node_name,
                "node_type": data["node_type"],
                "status": status,
                "started_at": start_event.get("timestamp"),
                "completed_at": end_event.get("timestamp") if end_event else None,
                "prep_duration_ms": int(phase_latencies.get("prep") * 1000) if phase_latencies.get("prep") else None,
                "exec_duration_ms": int(phase_latencies.get("exec") * 1000) if phase_latencies.get("exec") else None,
                "post_duration_ms": int(phase_latencies.get("post") * 1000) if phase_latencies.get("post") else None,
                "error_message": error_event.get("error_message") if error_event else None,
                "retry_count": error_event.get("retry_count", 0) if error_event else 0
            }

            node_executions.append(node_exec)

        return node_executions

    def _get_captured_spans(self) -> List[Dict[str, Any]]:
        """Get spans captured by OpenTelemetry exporter"""
        if self._span_exporter:
            return self._span_exporter.spans
        return self.completed_spans  # Fallback to manually added spans

    def _convert_events_to_telemetry_events(self) -> List[Dict[str, Any]]:
        """Convert audit events to platform telemetry events."""
        telemetry_events = []

        for event in self.events:
            telemetry_event = {
                "event_type": event.get("event_type", "unknown"),
                "timestamp": event.get("timestamp"),
                "data": event
            }
            telemetry_events.append(telemetry_event)

        return telemetry_events

    def upload(self) -> Optional[str]:
        """
        Upload telemetry data to Agora Cloud Platform.
        Automatically includes captured OpenTelemetry spans!

        Returns:
            Execution ID from the platform, or None if upload fails
        """
        try:
            # Calculate duration
            duration_ms = None
            if self.execution_end_time:
                delta = self.execution_end_time - self.execution_start_time
                duration_ms = int(delta.total_seconds() * 1000)

            # Build telemetry payload with auto-captured spans
            payload = {
                "workflow_id": self.workflow_name,
                "session_id": self.session_id,
                "status": self.execution_status,
                "started_at": self.execution_start_time.isoformat(),
                "completed_at": self.execution_end_time.isoformat() if self.execution_end_time else None,
                "duration_ms": duration_ms,
                "error_message": self.execution_error,
                "node_executions": self._convert_events_to_node_executions(),
                "telemetry_spans": self._get_captured_spans(),  # ← Auto-captured!
                "telemetry_events": self._convert_events_to_telemetry_events(),
                "shared_state_snapshots": []
            }

            # Send to platform with API key authentication
            headers = {
                "X-API-Key": self.api_key,
                "Content-Type": "application/json"
            }

            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    f"{self.api_url}/executions/ingest",
                    json=payload,
                    headers=headers
                )
                response.raise_for_status()

                result = response.json()
                execution_id = result.get("id")

                print(f"✅ Telemetry uploaded successfully!")
                print(f"   Execution ID: {execution_id}")
                print(f"   Workflow: {self.workflow_name}")
                print(f"   Spans captured: {len(self._get_captured_spans())}")
                print(f"   View at: {self.api_url.replace(':8000', ':5173')}/executions/{execution_id}")
                
                return execution_id

        except httpx.HTTPError as e:
            print(f"❌ Failed to upload telemetry: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    print(f"   Error details: {error_detail}")
                except:
                    print(f"   Response: {e.response.text}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during upload: {e}")
            return None
        