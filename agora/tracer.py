"""Lightweight tracing for Agora workflows.

Tracks timing, node status, and custom attributes for each node execution.
Provides console logging and JSON export capabilities.
"""

import json
import time
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class NodeSpan:
    """Represents a single node execution trace."""

    node_name: str
    node_type: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "running"
    action: Optional[str] = None
    error: Optional[str] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    parent_span_id: Optional[str] = None
    span_id: str = field(default_factory=lambda: f"span_{id(object())}")

    def end(
        self,
        status: str = "success",
        action: Optional[str] = None,
        error: Optional[str] = None,
    ) -> None:
        """Mark the span as complete."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status
        self.action = action
        self.error = error

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


@dataclass
class FlowTrace:
    """Represents a complete flow execution trace."""

    flow_name: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    status: str = "running"
    spans: List[NodeSpan] = field(default_factory=list)
    attributes: Dict[str, Any] = field(default_factory=dict)
    trace_id: str = field(default_factory=lambda: f"trace_{id(object())}")

    def end(self, status: str = "success") -> None:
        """Mark the trace as complete."""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000
        self.status = status

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["spans"] = [span.to_dict() for span in self.spans]
        return data


class Tracer:
    """Lightweight tracer for Agora workflows.

    Tracks timing, status, and attributes for node/flow executions.
    Supports console logging and JSON line export.
    """

    def __init__(self, enable_console: bool = True, enable_json: bool = False):
        """Initialize tracer.

        Args:
            enable_console: Print human-readable logs to console.
            enable_json: Output JSON lines for each span.
        """
        self.enable_console = enable_console
        self.enable_json = enable_json
        self.current_trace: Optional[FlowTrace] = None
        self.traces: List[FlowTrace] = []
        self._span_stack: List[NodeSpan] = []

    def start_flow_trace(self, flow_name: str, **attributes: Any) -> FlowTrace:
        """Start a new flow trace."""
        trace = FlowTrace(
            flow_name=flow_name, start_time=time.time(), attributes=attributes
        )
        self.current_trace = trace
        self.traces.append(trace)

        if self.enable_console:
            print(f"[TRACE] Starting flow: {flow_name}")

        return trace

    def end_flow_trace(
        self, status: str = "success", error: Optional[str] = None
    ) -> None:
        """End the current flow trace."""
        if self.current_trace:
            self.current_trace.end(status)

            if self.enable_console:
                print(
                    f"[TRACE] Flow completed: {self.current_trace.flow_name} "
                    f"({self.current_trace.duration_ms:.2f}ms) - {status}"
                )

            if error and self.enable_console:
                print(f"[TRACE] Error: {error}")

    @contextmanager
    def start_node_span(self, node_name: str, node_type: str, **attributes: Any):
        """Context manager for tracing a node execution.

        Usage:
            with tracer.start_node_span("MyNode", "Node"):
                # execute node logic
                pass
        """
        parent_span_id = (
            self._span_stack[-1].span_id if self._span_stack else None
        )

        span = NodeSpan(
            node_name=node_name,
            node_type=node_type,
            start_time=time.time(),
            parent_span_id=parent_span_id,
            attributes=attributes,
        )

        self._span_stack.append(span)

        if self.current_trace:
            self.current_trace.spans.append(span)

        if self.enable_console:
            indent = "  " * (len(self._span_stack) - 1)
            print(f"{indent}[NODE] → {node_name} ({node_type})")

        try:
            yield span
        except Exception as e:
            span.end(status="error", error=str(e))
            if self.enable_console:
                indent = "  " * (len(self._span_stack) - 1)
                print(f"{indent}[NODE] ✗ {node_name} - ERROR: {str(e)}")
            raise
        finally:
            self._span_stack.pop()

    def end_node_span(self, span: NodeSpan, action: Optional[str] = None) -> None:
        """End a node span with an action result."""
        span.end(status="success", action=action)

        if self.enable_console:
            indent = "  " * len(self._span_stack)
            action_str = f" → {action}" if action else ""
            print(
                f"{indent}[NODE] ✓ {span.node_name} "
                f"({span.duration_ms:.2f}ms){action_str}"
            )

        if self.enable_json:
            print(json.dumps(span.to_dict()))

    def emit_metrics(self) -> Dict[str, Any]:
        """Emit accumulated metrics for all traces."""
        if not self.current_trace:
            return {}

        trace = self.current_trace

        total_nodes = len(trace.spans)
        successful = sum(1 for s in trace.spans if s.status == "success")
        failed = sum(1 for s in trace.spans if s.status == "error")

        metrics = {
            "flow_name": trace.flow_name,
            "total_duration_ms": trace.duration_ms,
            "total_nodes": total_nodes,
            "successful_nodes": successful,
            "failed_nodes": failed,
            "trace_id": trace.trace_id,
        }

        if self.enable_console:
            print("\n[METRICS]")
            for key, value in metrics.items():
                print(f"  {key}: {value}")

        return metrics

    def get_trace_data(self) -> List[Dict[str, Any]]:
        """Get all trace data as dictionaries."""
        return [trace.to_dict() for trace in self.traces]

    def export_json(self, filepath: str) -> None:
        """Export all traces to a JSON file."""
        with open(filepath, "w") as f:
            json.dump(self.get_trace_data(), f, indent=2)

    def reset(self) -> None:
        """Reset tracer state."""
        self.current_trace = None
        self.traces = []
        self._span_stack = []
