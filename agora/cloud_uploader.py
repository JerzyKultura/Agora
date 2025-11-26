import os
import json
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
from uuid import UUID

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    httpx = None


class CloudUploader:
    """Uploads telemetry data to Agora Cloud Platform"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        platform_url: Optional[str] = None,
        project_name: Optional[str] = None,
        batch_size: int = 50,
        auto_flush: bool = True
    ):
        self.api_key = api_key or os.environ.get("AGORA_API_KEY")
        self.platform_url = platform_url or os.environ.get(
            "AGORA_PLATFORM_URL",
            "https://your-platform.com"
        )
        self.project_name = project_name or "default"
        self.batch_size = batch_size
        self.auto_flush = auto_flush

        self.execution_id: Optional[str] = None
        self.workflow_name: Optional[str] = None

        self.events_buffer: List[Dict[str, Any]] = []
        self.spans_buffer: List[Dict[str, Any]] = []
        self.node_executions_buffer: List[Dict[str, Any]] = []

        self.enabled = bool(self.api_key and HTTPX_AVAILABLE)

        if not self.enabled:
            if not self.api_key:
                print("⚠️  AGORA_API_KEY not set - cloud upload disabled")
            if not HTTPX_AVAILABLE:
                print("⚠️  httpx not installed - cloud upload disabled")
                print("   Install with: pip install httpx")

    def set_workflow(self, workflow_name: str):
        """Set the workflow name for this execution"""
        self.workflow_name = workflow_name

    async def start_execution(self, workflow_name: str, input_data: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Start a new execution on the platform"""
        if not self.enabled:
            return None

        self.workflow_name = workflow_name

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.platform_url}/telemetry/executions/start",
                    json={
                        "workflow_name": workflow_name,
                        "project_name": self.project_name,
                        "input_data": input_data or {}
                    },
                    headers={"X-API-Key": self.api_key}
                )
                response.raise_for_status()
                data = response.json()
                self.execution_id = data["execution_id"]
                print(f"✅ Started execution: {self.execution_id}")
                return self.execution_id
        except Exception as e:
            print(f"⚠️  Failed to start execution: {e}")
            return None

    async def complete_execution(
        self,
        status: str = "success",
        output_data: Optional[Dict[str, Any]] = None,
        error_message: Optional[str] = None
    ):
        """Mark execution as complete"""
        if not self.enabled or not self.execution_id:
            return

        await self.flush()

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.platform_url}/telemetry/executions/{self.execution_id}/complete",
                    json={
                        "status": status,
                        "output_data": output_data,
                        "error_message": error_message
                    },
                    headers={"X-API-Key": self.api_key}
                )
                response.raise_for_status()
                print(f"✅ Completed execution: {self.execution_id} ({status})")
        except Exception as e:
            print(f"⚠️  Failed to complete execution: {e}")

    def add_event(self, event_type: str, timestamp: datetime, data: Optional[Dict[str, Any]] = None):
        """Add a telemetry event to the buffer"""
        if not self.enabled:
            return

        self.events_buffer.append({
            "event_type": event_type,
            "timestamp": timestamp.isoformat(),
            "data": data or {}
        })

        if self.auto_flush and len(self.events_buffer) >= self.batch_size:
            asyncio.create_task(self.flush())

    def add_node_execution(
        self,
        node_name: str,
        node_type: str,
        status: str,
        started_at: datetime,
        completed_at: Optional[datetime] = None,
        prep_duration_ms: Optional[int] = None,
        exec_duration_ms: Optional[int] = None,
        post_duration_ms: Optional[int] = None,
        error_message: Optional[str] = None,
        retry_count: int = 0
    ):
        """Add a node execution to the buffer"""
        if not self.enabled:
            return

        self.node_executions_buffer.append({
            "node_name": node_name,
            "node_type": node_type,
            "status": status,
            "started_at": started_at.isoformat(),
            "completed_at": completed_at.isoformat() if completed_at else None,
            "prep_duration_ms": prep_duration_ms,
            "exec_duration_ms": exec_duration_ms,
            "post_duration_ms": post_duration_ms,
            "error_message": error_message,
            "retry_count": retry_count
        })

        if self.auto_flush and len(self.node_executions_buffer) >= self.batch_size:
            asyncio.create_task(self.flush())

    def add_span(
        self,
        span_id: str,
        trace_id: str,
        name: str,
        start_time: datetime,
        parent_span_id: Optional[str] = None,
        end_time: Optional[datetime] = None,
        duration_ms: Optional[int] = None,
        kind: Optional[str] = None,
        status: Optional[str] = None,
        attributes: Optional[Dict[str, Any]] = None,
        events: Optional[List[Dict[str, Any]]] = None
    ):
        """Add a telemetry span to the buffer"""
        if not self.enabled:
            return

        self.spans_buffer.append({
            "span_id": span_id,
            "trace_id": trace_id,
            "parent_span_id": parent_span_id,
            "name": name,
            "kind": kind,
            "status": status,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat() if end_time else None,
            "duration_ms": duration_ms,
            "attributes": attributes or {},
            "events": events or []
        })

        if self.auto_flush and len(self.spans_buffer) >= self.batch_size:
            asyncio.create_task(self.flush())

    async def flush(self):
        """Flush all buffered data to the platform"""
        if not self.enabled or not self.execution_id:
            return

        if not (self.events_buffer or self.spans_buffer or self.node_executions_buffer):
            return

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.platform_url}/telemetry/batch",
                    json={
                        "execution_id": self.execution_id,
                        "workflow_name": self.workflow_name,
                        "project_name": self.project_name,
                        "events": self.events_buffer,
                        "spans": self.spans_buffer,
                        "node_executions": self.node_executions_buffer
                    },
                    headers={"X-API-Key": self.api_key}
                )
                response.raise_for_status()

                self.events_buffer.clear()
                self.spans_buffer.clear()
                self.node_executions_buffer.clear()
        except Exception as e:
            print(f"⚠️  Failed to flush telemetry: {e}")

    def __enter__(self):
        """Context manager support"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Flush on exit"""
        if self.enabled:
            asyncio.run(self.flush())


def create_cloud_uploader(
    workflow_name: str,
    api_key: Optional[str] = None,
    platform_url: Optional[str] = None,
    project_name: Optional[str] = None
) -> CloudUploader:
    """
    Create and initialize a cloud uploader

    Usage:
        uploader = create_cloud_uploader("my_workflow")
        await uploader.start_execution("my_workflow")
        uploader.add_event("node_start", datetime.now(), {"node": "node1"})
        await uploader.complete_execution()
    """
    return CloudUploader(
        api_key=api_key,
        platform_url=platform_url,
        project_name=project_name
    )
