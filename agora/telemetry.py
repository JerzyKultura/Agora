import json
import time
import uuid
import warnings
from datetime import datetime
from typing import Dict, Any, List, Optional, Union
from contextlib import contextmanager

# Import base classes from the core
from agora import BaseNode, Node, BatchNode, Flow, AsyncNode, AsyncBatchNode, AsyncParallelBatchNode, AsyncFlow, AsyncBatchFlow, AsyncParallelBatchFlow

# Optional OpenTelemetry integration
try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None


# ======================================================================
# AUDIT LOGGER
# ======================================================================

class AuditLogger:
    """Records node execution events and flow transitions with JSON export capability"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or str(uuid.uuid4())
        self.events: List[Dict[str, Any]] = []
        self.start_time = datetime.utcnow()
        self.tracer = None
        
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
        with open(filename, 'w') as f:
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
    
    @contextmanager
    def otel_span(self, name: str, **attributes):
        """Create OpenTelemetry span if available, otherwise no-op"""
        if self.tracer:
            with self.tracer.start_as_current_span(name) as span:
                for key, value in attributes.items():
                    span.set_attribute(key, str(value))
                try:
                    yield span
                except Exception as e:
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    raise
        else:
            yield None


# ======================================================================
# AUDITED SYNC CLASSES
# ======================================================================

class AuditedNode(Node):
    """Node with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, audit_logger: AuditLogger, name=None, max_retries=1, wait=0):
        super().__init__(name, max_retries, wait)
        self.audit_logger = audit_logger
        self.phase_times = {}
    
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
    
    def _run(self, shared):
        self.audit_logger.log_node_start(self.name, self.__class__.__name__, self.params)
        total_start = time.time()
        
        with self.audit_logger.otel_span(
            f"node.{self.name}",
            node_name=self.name,
            node_type=self.__class__.__name__
        ) as span:
            try:
                self.before_run(shared)
                
                # Time each phase
                prep_result = self._time_phase("prep", self.prep, shared)
                exec_result = self._time_phase("exec", self._exec, prep_result)
                post_result = self._time_phase("post", self.post, shared, prep_result, exec_result)
                
                self.after_run(shared)
                
                total_latency = (time.time() - total_start) * 1000
                
                # Log success
                self.audit_logger.log_node_success(
                    self.name, 
                    self.__class__.__name__, 
                    post_result,
                    total_latency,
                    self.phase_times.copy()
                )
                
                # Set span attributes
                if span:
                    span.set_attribute("latency_ms", total_latency)
                    span.set_attribute("result_type", type(post_result).__name__)
                
                return post_result
                
            except Exception as exc:
                total_latency = (time.time() - total_start) * 1000
                retry_count = getattr(self, 'cur_retry', 0)
                
                # Log error
                self.audit_logger.log_node_error(
                    self.name,
                    self.__class__.__name__,
                    exc,
                    retry_count,
                    total_latency
                )
                
                # Set span error status
                if span:
                    span.set_attribute("latency_ms", total_latency)
                    span.set_attribute("retry_count", retry_count)
                
                return self.on_error(exc, shared)


class AuditedBatchNode(BatchNode):
    """BatchNode with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, audit_logger: AuditLogger, name=None, max_retries=1, wait=0):
        super().__init__(name, max_retries, wait)
        self.audit_logger = audit_logger
        self.phase_times = {}
    
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
    
    def _run(self, shared):
        self.audit_logger.log_node_start(self.name, self.__class__.__name__, self.params)
        total_start = time.time()
        
        with self.audit_logger.otel_span(
            f"batch_node.{self.name}",
            node_name=self.name,
            node_type=self.__class__.__name__
        ) as span:
            try:
                self.before_run(shared)
                
                # Time each phase
                prep_result = self._time_phase("prep", self.prep, shared)
                exec_result = self._time_phase("exec", self._exec, prep_result)
                post_result = self._time_phase("post", self.post, shared, prep_result, exec_result)
                
                self.after_run(shared)
                
                total_latency = (time.time() - total_start) * 1000
                
                # Log success
                self.audit_logger.log_node_success(
                    self.name,
                    self.__class__.__name__,
                    post_result,
                    total_latency,
                    self.phase_times.copy()
                )
                
                # Set span attributes
                if span:
                    span.set_attribute("latency_ms", total_latency)
                    span.set_attribute("result_type", type(post_result).__name__)
                    if isinstance(exec_result, list):
                        span.set_attribute("batch_size", len(exec_result))
                
                return post_result
                
            except Exception as exc:
                total_latency = (time.time() - total_start) * 1000
                retry_count = getattr(self, 'cur_retry', 0)
                
                # Log error
                self.audit_logger.log_node_error(
                    self.name,
                    self.__class__.__name__,
                    exc,
                    retry_count,
                    total_latency
                )
                
                # Set span error status
                if span:
                    span.set_attribute("latency_ms", total_latency)
                    span.set_attribute("retry_count", retry_count)
                
                return self.on_error(exc, shared)


class AuditedFlow(Flow):
    """Flow with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, audit_logger: AuditLogger, name=None, start=None):
        super().__init__(name, start)
        self.audit_logger = audit_logger
    
    def get_next_node(self, curr, action):
        """Override to log transitions"""
        next_node = super().get_next_node(curr, action)
        if next_node:
            self.audit_logger.log_flow_transition(curr.name, next_node.name, action or "default")
        return next_node
    
    def _run(self, shared):
        self.audit_logger.log_flow_start(self.name, self.__class__.__name__)
        total_start = time.time()
        
        with self.audit_logger.otel_span(
            f"flow.{self.name}",
            flow_name=self.name,
            flow_type=self.__class__.__name__
        ) as span:
            try:
                self.before_run(shared)
                
                prep_result = self.prep(shared)
                orch_result = self._orch(shared)
                post_result = self.post(shared, prep_result, orch_result)
                
                self.after_run(shared)
                
                total_latency = (time.time() - total_start) * 1000
                
                # Log flow end
                self.audit_logger.log_flow_end(
                    self.name,
                    self.__class__.__name__,
                    post_result,
                    total_latency
                )
                
                # Set span attributes
                if span:
                    span.set_attribute("total_latency_ms", total_latency)
                
                return post_result
                
            except Exception as exc:
                total_latency = (time.time() - total_start) * 1000
                
                # Log flow error as node error
                self.audit_logger.log_node_error(
                    self.name,
                    self.__class__.__name__,
                    exc,
                    0,
                    total_latency
                )
                
                if span:
                    span.set_attribute("total_latency_ms", total_latency)
                
                return self.on_error(exc, shared)


# ======================================================================
# AUDITED ASYNC CLASSES
# ======================================================================

class AuditedAsyncNode(AsyncNode):
    """AsyncNode with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, audit_logger: AuditLogger, name=None, max_retries=1, wait=0):
        super().__init__(name, max_retries, wait)
        self.audit_logger = audit_logger
        self.phase_times = {}
    
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
    
    async def _run_async(self, shared):
        self.audit_logger.log_node_start(self.name, self.__class__.__name__, self.params)
        total_start = time.time()
        
        with self.audit_logger.otel_span(
            f"async_node.{self.name}",
            node_name=self.name,
            node_type=self.__class__.__name__
        ) as span:
            try:
                await self.before_run_async(shared)
                
                # Time each phase
                prep_result = await self._time_phase_async("prep", self.prep_async, shared)
                exec_result = await self._time_phase_async("exec", self._exec_async, prep_result)
                post_result = await self._time_phase_async("post", self.post_async, shared, prep_result, exec_result)
                
                await self.after_run_async(shared)
                
                total_latency = (time.time() - total_start) * 1000
                
                # Log success
                self.audit_logger.log_node_success(
                    self.name,
                    self.__class__.__name__,
                    post_result,
                    total_latency,
                    self.phase_times.copy()
                )
                
                # Set span attributes
                if span:
                    span.set_attribute("latency_ms", total_latency)
                    span.set_attribute("result_type", type(post_result).__name__)
                
                return post_result
                
            except Exception as exc:
                total_latency = (time.time() - total_start) * 1000
                retry_count = getattr(self, 'cur_retry', 0)
                
                # Log error
                self.audit_logger.log_node_error(
                    self.name,
                    self.__class__.__name__,
                    exc,
                    retry_count,
                    total_latency
                )
                
                # Set span error status
                if span:
                    span.set_attribute("latency_ms", total_latency)
                    span.set_attribute("retry_count", retry_count)
                
                return await self.on_error_async(exc, shared)


class AuditedAsyncFlow(AsyncFlow):
    """AsyncFlow with audit logging and optional OpenTelemetry tracing"""
    
    def __init__(self, audit_logger: AuditLogger, name=None, start=None):
        super().__init__(name, start)
        self.audit_logger = audit_logger
    
    def get_next_node(self, curr, action):
        """Override to log transitions"""
        next_node = super().get_next_node(curr, action)
        if next_node:
            self.audit_logger.log_flow_transition(curr.name, next_node.name, action or "default")
        return next_node
    
    async def _run_async(self, shared):
        self.audit_logger.log_flow_start(self.name, self.__class__.__name__)
        total_start = time.time()
        
        with self.audit_logger.otel_span(
            f"async_flow.{self.name}",
            flow_name=self.name,
            flow_type=self.__class__.__name__
        ) as span:
            try:
                await self.before_run_async(shared)
                
                prep_result = await self.prep_async(shared)
                orch_result = await self._orch_async(shared)
                post_result = await self.post_async(shared, prep_result, orch_result)
                
                await self.after_run_async(shared)
                
                total_latency = (time.time() - total_start) * 1000
                
                # Log flow end
                self.audit_logger.log_flow_end(
                    self.name,
                    self.__class__.__name__,
                    post_result,
                    total_latency
                )
                
                # Set span attributes
                if span:
                    span.set_attribute("total_latency_ms", total_latency)
                
                return post_result
                
            except Exception as exc:
                total_latency = (time.time() - total_start) * 1000
                
                # Log flow error
                self.audit_logger.log_node_error(
                    self.name,
                    self.__class__.__name__,
                    exc,
                    0,
                    total_latency
                )
                
                if span:
                    span.set_attribute("total_latency_ms", total_latency)
                
                return await self.on_error_async(exc, shared)


# ======================================================================
# PUBLIC API
# ======================================================================

__all__ = [
    'AuditLogger',
    'AuditedNode', 'AuditedBatchNode', 'AuditedFlow',
    'AuditedAsyncNode', 'AuditedAsyncFlow'
]
