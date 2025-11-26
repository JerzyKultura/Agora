"""
Cloud client for Agora Platform integration.

This module provides CloudAuditLogger that extends AuditLogger to automatically
send telemetry data to the Agora Cloud Platform using API keys.
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from .telemetry import AuditLogger


class CloudAuditLogger(AuditLogger):
    """
    Audit logger that sends telemetry to Agora Cloud Platform.

    Simple Usage:
        logger = CloudAuditLogger(
            api_key="agora_key_abc123xyz",
            workflow_name="MyWorkflow"
        )

        # Use with your Agora nodes/flows
        node = AuditedNode("processor", logger)
        flow = AuditedFlow("MyFlow", logger)
        result = flow.run(shared)

        # Automatically uploads on completion!
        logger.upload()
    """

    def __init__(
        self,
        api_key: str,
        workflow_name: str,
        api_url: str = "http://localhost:8000",
        session_id: Optional[str] = None,
        auto_upload: bool = True
    ):
        """
        Initialize CloudAuditLogger.

        Args:
            api_key: Your Agora platform API key (from Settings → API Keys)
            workflow_name: Name of your workflow (auto-created if doesn't exist)
            api_url: Base URL of Agora Platform API (default: http://localhost:8000)
            session_id: Optional unique identifier for this execution session
            auto_upload: If True, automatically upload on flow completion
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

    def mark_complete(self, status: str = "success", error: Optional[str] = None):
        """Mark execution as complete."""
        self.execution_end_time = datetime.now()
        self.execution_status = status
        self.execution_error = error

        if self.auto_upload:
            self.upload()

    def _convert_events_to_node_executions(self) -> List[Dict[str, Any]]:
        """
        Convert audit events into node execution records.
        Groups events by node name to create consolidated node execution records.
        """
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

    def _convert_spans_to_telemetry_spans(self) -> List[Dict[str, Any]]:
        """Convert OpenTelemetry spans to platform format."""
        telemetry_spans = []

        for span in self.completed_spans:
            telemetry_span = {
                "span_id": span.get("span_id", ""),
                "trace_id": span.get("trace_id", ""),
                "parent_span_id": span.get("parent_span_id"),
                "name": span.get("name", ""),
                "kind": span.get("kind"),
                "status": span.get("status"),
                "start_time": span.get("start_time"),
                "end_time": span.get("end_time"),
                "duration_ms": span.get("duration_ms"),
                "attributes": span.get("attributes", {}),
                "events": span.get("events", [])
            }
            telemetry_spans.append(telemetry_span)

        return telemetry_spans

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

        Returns:
            Execution ID from the platform, or None if upload fails
        """
        try:
            # Calculate duration
            duration_ms = None
            if self.execution_end_time:
                delta = self.execution_end_time - self.execution_start_time
                duration_ms = int(delta.total_seconds() * 1000)

            # Build telemetry payload
            # NOTE: workflow_id is actually the workflow NAME
            # Backend will auto-create if it doesn't exist!
            payload = {
                "workflow_id": self.workflow_name,  # ← Backend handles this!
                "session_id": self.session_id,
                "status": self.execution_status,
                "started_at": self.execution_start_time.isoformat(),
                "completed_at": self.execution_end_time.isoformat() if self.execution_end_time else None,
                "duration_ms": duration_ms,
                "error_message": self.execution_error,
                "node_executions": self._convert_events_to_node_executions(),
                "telemetry_spans": self._convert_spans_to_telemetry_spans(),
                "telemetry_events": self._convert_events_to_telemetry_events(),
                "shared_state_snapshots": []  # TODO: Implement state snapshot tracking
            }

            # Send to platform with API key authentication
            headers = {
                "X-API-Key": self.api_key,  # ← Simple API key auth!
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
        