"""
Cloud client for Agora Platform integration.

This module provides CloudAuditLogger that extends AuditLogger to automatically
send telemetry data to the Agora Cloud Platform.
"""

import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
from .telemetry import AuditLogger
from uuid import UUID


class CloudAuditLogger(AuditLogger):
    """
    Audit logger that sends telemetry to Agora Cloud Platform.

    Usage:
        logger = CloudAuditLogger(
            session_id="my-session",
            api_url="http://localhost:8000",
            access_token="your-jwt-token",
            workflow_id="uuid-of-workflow"
        )

        # Use like normal AuditLogger
        node = AuditedNode("processor", logger)
        flow = AuditedFlow("MyFlow", logger)
        flow.start(node)
        result = flow.run(shared)

        # Automatically uploads on completion
        logger.upload()
    """

    def __init__(
        self,
        session_id: str,
        api_url: str,
        access_token: str,
        workflow_id: str,
        auto_upload: bool = True
    ):
        """
        Initialize CloudAuditLogger.

        Args:
            session_id: Unique identifier for this execution session
            api_url: Base URL of Agora Platform API (e.g., http://localhost:8000)
            access_token: JWT access token for authentication
            workflow_id: UUID of the workflow in the platform
            auto_upload: If True, automatically upload on flow completion
        """
        super().__init__(session_id)
        self.api_url = api_url.rstrip("/")
        self.access_token = access_token
        self.workflow_id = workflow_id
        self.auto_upload = auto_upload
        self.execution_start_time = datetime.now()
        self.execution_end_time: Optional[datetime] = None
        self.execution_status = "running"
        self.execution_error: Optional[str] = None

        # Store node ID mapping (node_name -> node_id from platform)
        self.node_id_map: Dict[str, str] = {}

    def set_node_id_mapping(self, node_name: str, node_id: str):
        """Map node name to platform node ID."""
        self.node_id_map[node_name] = node_id

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

            # Get node_id from mapping or generate placeholder
            node_id = self.node_id_map.get(node_name, "00000000-0000-0000-0000-000000000000")

            node_exec = {
                "node_id": node_id,
                "node_name": node_name,
                "node_type": data["node_type"],
                "status": status,
                "started_at": start_event.get("timestamp"),
                "completed_at": end_event.get("timestamp") if end_event else None,
                "prep_duration_ms": phase_latencies.get("prep"),
                "exec_duration_ms": phase_latencies.get("exec"),
                "post_duration_ms": phase_latencies.get("post"),
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
            payload = {
                "workflow_id": self.workflow_id,
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

            # Send to platform
            headers = {
                "Authorization": f"Bearer {self.access_token}",
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

                print(f"✅ Telemetry uploaded successfully. Execution ID: {execution_id}")
                return execution_id

        except httpx.HTTPError as e:
            print(f"❌ Failed to upload telemetry: {e}")
            return None
        except Exception as e:
            print(f"❌ Unexpected error during upload: {e}")
            return None
