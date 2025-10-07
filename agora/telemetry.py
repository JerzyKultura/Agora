import json
import time
import uuid
import os
import warnings
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager

# Import base classes from the core
from agora import (
    BaseNode, Node, BatchNode, Flow, 
    AsyncNode, AsyncBatchNode, AsyncParallelBatchNode, AsyncFlow, 
    AsyncBatchFlow, AsyncParallelBatchFlow
)

# Optional OpenTelemetry integration
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None


# ======================================================================
# AUDIT LOGGER (ENHANCED WITH HIERARCHICAL SPAN SUPPORT)
# ======================================================================

class AuditLogger:
    """Records node execution events and flow transitions with JSON export capability"""
    
    def __init__(self, session_id: Optional[str] = None, save_dir: str = "./logs"):
        self.session_id = session_id or str(uuid.uuid4())
        self.events: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
        self.save_dir = save_dir
        self.tracer = None
        
        # Storage for completed spans (for JSON export)
        self.completed_spans: List[Dict[str, Any]] = []
        self.span_hierarchy: Dict[int, Optional[int]] = {}  # child_id -> parent_id
        
        # Ensure save directory exists
        os.makedirs(save_dir, exist_ok=True)
        
        # Initialize OpenTelemetry tracer if available
        if OTEL_AVAILABLE:
            self.tracer = trace.get_tracer(__name__)
    
    def log_event(self, event_type: str, **kwargs):
        """Log a single event with timestamp"""
        event = {
            "session_id": self.session_id,
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            **kwargs
        }
        self.events.append(event)
    
    def log_node_start(self, node_name: str, node_type: str, params: Dict[str, Any] = None):
        """Log node execution start"""
        self.log_event(
            "node_start",
            node_name=node_name,
            node_type=node_type,
            params=params or {}
        )
    
    def log_node_success(self, node_name: str, node_type: str, result: Any = None, 
                        latency_ms: float = 0, phase_latencies: Dict[str, float] = None):
        """Log successful node execution"""
        self.log_event(
            "node_success",
            node_name=node_name,
            node_type=node_type,
            result_type=type(result).__name__ if result is not None else "None",
            latency_ms=latency_ms,
            phase_latencies=phase_latencies or {}
        )
    
    def log_node_error(self, node_name: str, node_type: str, error: Exception,
                      retry_count: int = 0, latency_ms: float = 0):
        """Log node execution error"""
        self.log_event(
            "node_error",
            node_name=node_name,
            node_type=node_type,
            error_type=type(error).__name__,
            error_message=str(error),
            retry_count=retry_count,
            latency_ms=latency_ms
        )
    
    def log_flow_transition(self, from_node: str, to_node: str, action: str = "default"):
        """Log flow edge transition"""
        self.log_event(
            "flow_transition",
            from_node=from_node,
            to_node=to_node,
            action=action
        )
    
    def log_flow_start(self, flow_name: str, flow_type: str):
        """Log flow execution start"""
        self.log_event(
            "flow_start",
            flow_name=flow_name,
            flow_type=flow_type
        )
    
    def log_flow_end(self, flow_name: str, flow_type: str, result: Any = None, 
                    total_latency_ms: float = 0):
        """Log flow execution end"""
        self.log_event(
            "flow_end",
            flow_name=flow_name,
            flow_type=flow_type,
            result_type=type(result).__name__ if result is not None else "None",
            total_latency_ms=total_latency_ms
        )
    
    def to_json(self, indent: int = 2) -> str:
        """Export all events as JSON string"""
        summary = {
            "session_id": self.session_id,
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total_events": len(self.events),
            "event_counts": self._get_event_counts(),
            "events": self.events
        }
        return json.dumps(summary, indent=indent)
    
    def save_json(self, filename: str):
        """Save audit log to JSON file"""
        filepath = os.path.join(self.save_dir, filename) if not os.path.isabs(filename) else filename
        with open(filepath, 'w') as f:
            f.write(self.to_json())
    
    def get_summary(self) -> Dict[str, Any]:
        """Get audit session summary"""
        return {
            "session_id": self.session_id,
            "total_events": len(self.events),
            "event_counts": self._get_event_counts(),
            "duration_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }
    
    def _get_event_counts(self) -> Dict[str, int]:
        """Count events by type"""
        counts = {}
        for event in self.events:
            event_type = event.get("event_type", "unknown")
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts
    
    # ====================================================================
    # HIERARCHICAL SPAN MANAGEMENT
    # ====================================================================
    
    def create_span(self, name: str, parent=None, **attrs):
        """
        Create a span with optional parent for hierarchical tracing.
        
        Args:
            name: Span name (e.g., "flow.chat_flow", "node.send_prompt")
            parent: Parent span object (None for root spans)
            **attrs: Additional attributes to set on the span
        
        Returns:
            Span object or None if OTel unavailable
        """
        if not self.tracer:
            return None
        
        # Create span with parent context if provided
        if parent is not None:
            # Create a context from the parent span
            ctx = trace.set_span_in_context(parent)
            span = self.tracer.start_span(name, context=ctx)
            
            # Track hierarchy
            span_id = id(span)
            parent_id = id(parent)
            self.span_hierarchy[span_id] = parent_id
        else:
            # Root span (no parent)
            span = self.tracer.start_span(name)
            self.span_hierarchy[id(span)] = None
        
        # Set custom attributes
        for key, value in attrs.items():
            span.set_attribute(key, str(value) if value is not None else "None")
        
        # Store start time for duration calculation
        if not hasattr(span, '_agora_start_time'):
            span._agora_start_time = time.time()
        
        return span
    
    def end_span(self, span, error: Exception = None):
        """
        End a span and record it for JSON export.
        
        Args:
            span: The span to end (can be None)
            error: Optional exception to mark span as failed
        """
        if span is None:
            return
        
        # Set error status if provided
        if error:
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.set_attribute("error.type", type(error).__name__)
            span.set_attribute("error.message", str(error))
        
        # Calculate duration
        duration_ms = (time.time() - getattr(span, '_agora_start_time', time.time())) * 1000
        
        # Extract span information for JSON export
        span_context = span.get_span_context()
        span_id = id(span)
        parent_id = self.span_hierarchy.get(span_id)
        
        # Get parent span ID from hierarchy
        parent_span_id = None
        if parent_id:
            # Look up parent in completed spans
            for completed in self.completed_spans:
                if completed.get("_internal_id") == parent_id:
                    parent_span_id = completed.get("span_id")
                    break
        
        # Store completed span info
        span_info = {
            "name": span.name if hasattr(span, 'name') else "unknown",
            "trace_id": format(span_context.trace_id, '032x') if span_context else None,
            "span_id": format(span_context.span_id, '016x') if span_context else None,
            "parent_span_id": parent_span_id,
            "duration_ms": round(duration_ms, 2),
            "attributes": {},
            "status": "error" if error else "ok",
            "start_time": datetime.fromtimestamp(
                getattr(span, '_agora_start_time', time.time())
            ).isoformat(),
            "_internal_id": span_id  # For parent lookup
        }
        
        # Extract attributes from span
        if hasattr(span, 'attributes') and span.attributes:
            span_info["attributes"] = dict(span.attributes)
        
        self.completed_spans.append(span_info)
        
        # End the span
        span.end()
    
    def save_trace_json(self, filename: str = "trace.json"):
        """
        Save hierarchical trace data to JSON file.
        
        Args:
            filename: Output filename (relative to save_dir or absolute path)
        """
        filepath = os.path.join(self.save_dir, filename) if not os.path.isabs(filename) else filename
        
        # Get trace_id from first span if available
        trace_id = None
        if self.completed_spans:
            trace_id = self.completed_spans[0].get("trace_id")
        
        trace_data = {
            "trace_id": trace_id,
            "session_id": self.session_id,
            "service_name": "agora",
            "start_time": self.start_time.isoformat(),
            "end_time": datetime.utcnow().isoformat(),
            "total_spans": len(self.completed_spans),
            "spans": self.completed_spans
        }
        
        with open(filepath, 'w') as f:
            f.write(json.dumps(trace_data, indent=2))
        
        print(f"✅ Trace saved to {filepath}")


# ======================================================================
# AUDIT MIXINS (WITH SPAN HIERARCHY SUPPORT)
# ======================================================================

class AuditMixin:
    """Common audit functionality for sync nodes"""
    
    def _time_phase(self, phase_name: str, func, *args, **kwargs):
        """Time a phase execution"""
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            self.phase_times[phase_name] = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            self.phase_times[phase_name] = (time.time() - start_time) * 1000
            raise
    
    def _audit_run(self, shared):
        """Common audited run logic for sync nodes with span hierarchy"""
        self.audit_logger.log_node_start(self.name, self.__class__.__name__, self.params)
        total_start = time.time()
        
        # Get parent span from shared context
        parent_span = shared.get("parent_span")
        
        # Create child span with parent relationship
        span = self.audit_logger.create_span(
            f"node.{self.name}",
            parent=parent_span,
            node_name=self.name,
            node_type=self.__class__.__name__
        )
        
        try:
            self.before_run(shared)
            
            # Time each phase
            prep_result = self._time_phase("prep", self.prep, shared)
            exec_result = self._time_phase("exec", self._exec, prep_result)
            post_result = self._time_phase("post", self.post, shared, prep_result, exec_result)
            
            self.after_run(shared)
            
            total_latency = (time.time() - total_start) * 1000
            
            # Track batch sizes
            input_size = len(prep_result) if hasattr(prep_result, '__len__') else None
            output_size = len(exec_result) if hasattr(exec_result, '__len__') else None
            
            phase_latencies_with_sizes = {
                **self.phase_times.copy(),
                "input_batch_size": input_size,
                "output_batch_size": output_size
            }
            
            self.audit_logger.log_node_success(
                self.name, 
                self.__class__.__name__, 
                post_result,
                total_latency,
                phase_latencies_with_sizes
            )
            
            # Set span attributes
            if span:
                span.set_attribute("latency_ms", str(total_latency))
                span.set_attribute("result_type", type(post_result).__name__)
                if input_size is not None:
                    span.set_attribute("input_batch_size", str(input_size))
                if output_size is not None:
                    span.set_attribute("output_batch_size", str(output_size))
            
            self.audit_logger.end_span(span)
            
            return post_result
            
        except Exception as exc:
            total_latency = (time.time() - total_start) * 1000
            retry_count = getattr(self, 'cur_retry', 0)
            
            self.audit_logger.log_node_error(
                self.name,
                self.__class__.__name__,
                exc,
                retry_count,
                total_latency
            )
            
            if span:
                span.set_attribute("latency_ms", str(total_latency))
                span.set_attribute("retry_count", str(retry_count))
            
            self.audit_logger.end_span(span, error=exc)
            
            return self.on_error(exc, shared)


class AsyncAuditMixin:
    """Common audit functionality for async nodes"""
    
    async def _time_phase_async(self, phase_name: str, func, *args, **kwargs):
        """Time an async phase execution"""
        start_time = time.time()
        try:
            result = await func(*args, **kwargs)
            self.phase_times[phase_name] = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            self.phase_times[phase_name] = (time.time() - start_time) * 1000
            raise
    
    async def _audit_run_async(self, shared):
        """Common audited run logic for async nodes with span hierarchy"""
        self.audit_logger.log_node_start(self.name, self.__class__.__name__, self.params)
        total_start = time.time()
        
        # Get parent span from shared context
        parent_span = shared.get("parent_span")
        
        # Create child span with parent relationship
        span = self.audit_logger.create_span(
            f"node.{self.name}",
            parent=parent_span,
            node_name=self.name,
            node_type=self.__class__.__name__
        )
        
        try:
            await self.before_run_async(shared)
            
            # Time each phase
            prep_result = await self._time_phase_async("prep", self.prep_async, shared)
            exec_result = await self._time_phase_async("exec", self._exec_async, prep_result)
            post_result = await self._time_phase_async("post", self.post_async, shared, prep_result, exec_result)
            
            await self.after_run_async(shared)
            
            total_latency = (time.time() - total_start) * 1000
            
            # Track batch sizes
            input_size = len(prep_result) if hasattr(prep_result, '__len__') else None
            output_size = len(exec_result) if hasattr(exec_result, '__len__') else None
            
            phase_latencies_with_sizes = {
                **self.phase_times.copy(),
                "input_batch_size": input_size,
                "output_batch_size": output_size
            }
            
            self.audit_logger.log_node_success(
                self.name,
                self.__class__.__name__,
                post_result,
                total_latency,
                phase_latencies_with_sizes
            )
            
            if span:
                span.set_attribute("latency_ms", str(total_latency))
                span.set_attribute("result_type", type(post_result).__name__)
                if input_size is not None:
                    span.set_attribute("input_batch_size", str(input_size))
                if output_size is not None:
                    span.set_attribute("output_batch_size", str(output_size))
            
            self.audit_logger.end_span(span)
            
            return post_result
            
        except Exception as exc:
            total_latency = (time.time() - total_start) * 1000
            retry_count = getattr(self, 'cur_retry', 0)
            
            self.audit_logger.log_node_error(
                self.name,
                self.__class__.__name__,
                exc,
                retry_count,
                total_latency
            )
            
            if span:
                span.set_attribute("latency_ms", str(total_latency))
                span.set_attribute("retry_count", str(retry_count))
            
            self.audit_logger.end_span(span, error=exc)
            
            return await self.on_error_async(exc, shared)


# ======================================================================
# AUDITED SYNC CLASSES (UNCHANGED)
# ======================================================================

class AuditedNode(AuditMixin, Node):
    """Node with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, name=None, audit_logger: AuditLogger = None, max_retries=1, wait=0):
        super().__init__(name, max_retries, wait)
        self.audit_logger = audit_logger
        self.phase_times = {}
    
    def _run(self, shared):
        if self.audit_logger:
            return self._audit_run(shared)
        else:
            return super()._run(shared)


class AuditedBatchNode(AuditMixin, BatchNode):
    """BatchNode with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, name=None, audit_logger: AuditLogger = None, max_retries=1, wait=0):
        super().__init__(name, max_retries, wait)
        self.audit_logger = audit_logger
        self.phase_times = {}
    
    def _run(self, shared):
        if self.audit_logger:
            return self._audit_run(shared)
        else:
            return super()._run(shared)


class AuditedFlow(Flow):
    """Flow with audit logging and hierarchical span support"""
    
    def __init__(self, name=None, audit_logger: AuditLogger = None, start=None):
        super().__init__(name, start)
        self.audit_logger = audit_logger
    
    def get_next_node(self, curr, action):
        """Override to log transitions"""
        next_node = super().get_next_node(curr, action)
        if next_node and self.audit_logger:
            self.audit_logger.log_flow_transition(curr.name, next_node.name, action or "default")
        return next_node
    
    def _run(self, shared):
        if not self.audit_logger:
            return super()._run(shared)
        
        self.audit_logger.log_flow_start(self.name, self.__class__.__name__)
        total_start = time.time()
        
        # Create root span for the flow
        span = self.audit_logger.create_span(
            f"flow.{self.name}",
            flow_name=self.name,
            flow_type=self.__class__.__name__
        )
        
        # Store parent span in shared context for child nodes
        shared["parent_span"] = span
        
        try:
            self.before_run(shared)
            
            prep_result = self.prep(shared)
            orch_result = self._orch(shared)
            post_result = self.post(shared, prep_result, orch_result)
            
            self.after_run(shared)
            
            total_latency = (time.time() - total_start) * 1000
            
            self.audit_logger.log_flow_end(
                self.name,
                self.__class__.__name__,
                post_result,
                total_latency
            )
            
            if span:
                span.set_attribute("total_latency_ms", str(total_latency))
            
            self.audit_logger.end_span(span)
            
            return post_result
            
        except Exception as exc:
            total_latency = (time.time() - total_start) * 1000
            
            self.audit_logger.log_node_error(
                self.name,
                self.__class__.__name__,
                exc,
                0,
                total_latency
            )
            
            if span:
                span.set_attribute("total_latency_ms", str(total_latency))
            
            self.audit_logger.end_span(span, error=exc)
            
            return self.on_error(exc, shared)


# ======================================================================
# AUDITED ASYNC CLASSES
# ======================================================================

class AuditedAsyncNode(AsyncAuditMixin, AsyncNode):
    """AsyncNode with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, name=None, audit_logger: AuditLogger = None, max_retries=1, wait=0):
        super().__init__(name, max_retries, wait)
        self.audit_logger = audit_logger
        self.phase_times = {}
    
    async def _run_async(self, shared):
        if self.audit_logger:
            return await self._audit_run_async(shared)
        else:
            return await super()._run_async(shared)


class AuditedAsyncBatchNode(AsyncAuditMixin, AsyncBatchNode):
    """AsyncBatchNode with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, name=None, audit_logger: AuditLogger = None, max_retries=1, wait=0):
        super().__init__(name, max_retries, wait)
        self.audit_logger = audit_logger
        self.phase_times = {}
    
    async def _run_async(self, shared):
        if self.audit_logger:
            return await self._audit_run_async(shared)
        else:
            return await super()._run_async(shared)


class AuditedAsyncParallelBatchNode(AsyncAuditMixin, AsyncParallelBatchNode):
    """AsyncParallelBatchNode with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, name=None, audit_logger: AuditLogger = None, max_retries=1, wait=0):
        super().__init__(name, max_retries, wait)
        self.audit_logger = audit_logger
        self.phase_times = {}
    
    async def _run_async(self, shared):
        if self.audit_logger:
            return await self._audit_run_async(shared)
        else:
            return await super()._run_async(shared)


class AuditedAsyncFlow(AsyncFlow):
    """AsyncFlow with audit logging and hierarchical span support"""
    
    def __init__(self, name=None, audit_logger: AuditLogger = None, start=None):
        super().__init__(name, start)
        self.audit_logger = audit_logger
    
    def get_next_node(self, curr, action):
        """Override to log transitions"""
        next_node = super().get_next_node(curr, action)
        if next_node and self.audit_logger:
            self.audit_logger.log_flow_transition(curr.name, next_node.name, action or "default")
        return next_node
    
    async def _run_async(self, shared):
        if not self.audit_logger:
            return await super()._run_async(shared)
        
        self.audit_logger.log_flow_start(self.name, self.__class__.__name__)
        total_start = time.time()
        
        # Create root span for the flow
        span = self.audit_logger.create_span(
            f"flow.{self.name}",
            flow_name=self.name,
            flow_type=self.__class__.__name__
        )
        
        # Store parent span in shared context for child nodes
        shared["parent_span"] = span
        
        try:
            await self.before_run_async(shared)
            
            prep_result = await self.prep_async(shared)
            orch_result = await self._orch_async(shared)
            post_result = await self.post_async(shared, prep_result, orch_result)
            
            await self.after_run_async(shared)
            
            total_latency = (time.time() - total_start) * 1000
            
            self.audit_logger.log_flow_end(
                self.name,
                self.__class__.__name__,
                post_result,
                total_latency
            )
            
            if span:
                span.set_attribute("total_latency_ms", str(total_latency))
            
            self.audit_logger.end_span(span)
            
            return post_result
            
        except Exception as exc:
            total_latency = (time.time() - total_start) * 1000
            
            self.audit_logger.log_node_error(
                self.name,
                self.__class__.__name__,
                exc,
                0,
                total_latency
            )
            
            if span:
                span.set_attribute("total_latency_ms", str(total_latency))
            
            self.audit_logger.end_span(span, error=exc)
            
            return await self.on_error_async(exc, shared)


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    'AuditLogger',
    'AuditedNode', 'AuditedBatchNode', 'AuditedFlow',
    'AuditedAsyncNode', 'AuditedAsyncBatchNode', 'AuditedAsyncParallelBatchNode', 
    'AuditedAsyncFlow'
]
