# ==============================================================
# agora_tracer.py - COMPLETE STANDALONE MODULE
# ==============================================================

"""
Agora telemetry integration for workflows.
Usage:
    from agora_tracer import TracedAsyncNode, init_agora
    
    # Initialize once at start
    init_agora(app_name="my_app", export_to_console=True)
    
    # Use traced classes
    class MyNode(TracedAsyncNode):
        async def exec_async(self, data):
            return process(data)
"""

from opentelemetry import trace
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from traceloop.sdk import Traceloop
from agora import AsyncNode, AsyncFlow, AsyncBatchNode, AsyncParallelBatchNode
import os, time, asyncio, inspect, functools
from datetime import datetime
from typing import Optional, Sequence, Any, List, Dict
import json
from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
from opentelemetry.sdk.trace import ReadableSpan

try:
    from agora.supabase_uploader import SupabaseUploader
    SUPABASE_UPLOADER_AVAILABLE = True
except ImportError:
    SUPABASE_UPLOADER_AVAILABLE = False
    SupabaseUploader = None

try:
    from agora.wide_events import BusinessContextSpanProcessor
    WIDE_EVENTS_AVAILABLE = True
except ImportError:
    WIDE_EVENTS_AVAILABLE = False
    BusinessContextSpanProcessor = None

_initialized = False
tracer = None
cloud_uploader = None
_sampling_rate = 1.0  # 1.0 = trace everything, 0.5 = trace 50%
_capture_io_default = False  # Whether to capture input/output by default

import random

def init_agora(
    app_name: str = "agora-app",
    export_to_console: bool = False,
    export_to_file: Optional[str] = None,
    disable_content_logging: bool = True,
    enable_cloud_upload: bool = True,
    project_name: Optional[str] = None,
    api_key: Optional[str] = None,
    sampling_rate: float = 1.0,
    capture_io: bool = False,
    supabase_url: Optional[str] = None,
    supabase_key: Optional[str] = None
):
    """
    Initialize Agora telemetry system. One-line setup!
    
    If VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY are in your .env, 
    they will be auto-detected.
    """
    global _initialized, tracer, cloud_uploader, _sampling_rate, _capture_io_default

    if _initialized:
        return

    # Try to load .env file
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    # Set global config
    _sampling_rate = sampling_rate
    _capture_io_default = capture_io

    # Configure environment
    if disable_content_logging:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
    os.environ["TRACELOOP_TELEMETRY"] = "false"
    os.environ["TRACELOOP_SUPPRESS_WARNINGS"] = "true"

    # Create processors
    processors = []

    # ALWAYS add the business context processor (for plug-and-play wide events!)
    if WIDE_EVENTS_AVAILABLE:
        processors.append(BusinessContextSpanProcessor())
        print("✅ Wide events (business context) processor enabled")

    if export_to_console:
        processors.append(SimpleSpanProcessor(ConsoleSpanExporter()))

    if export_to_file:

        class JSONFileExporter(SpanExporter):
            def __init__(self, path):
                self.path = path

            def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
                with open(self.path, 'a') as f:
                    for span in spans:
                        f.write(json.dumps({
                            "timestamp": datetime.now().isoformat(),
                            "name": span.name,
                            "trace_id": format(span.context.trace_id, '032x'),
                            "attributes": dict(span.attributes or {})
                        }) + '\n')
                return SpanExportResult.SUCCESS

        processors.append(SimpleSpanProcessor(JSONFileExporter(export_to_file)))

    if enable_cloud_upload and SUPABASE_UPLOADER_AVAILABLE:

        class SupabaseSpanExporter(SpanExporter):
            def export(self, spans: Sequence[ReadableSpan]) -> SpanExportResult:
                global cloud_uploader
                if not cloud_uploader or not cloud_uploader.enabled:
                    return SpanExportResult.SUCCESS



                formatted = []
                for span in spans:
                    attrs = dict(span.attributes or {})

                    # Extract usage metrics if available (standard OTel / Traceloop attrs)
                    tokens = attrs.get("llm.usage.total_tokens") or \
                             attrs.get("traceloop.usage.total_tokens") or \
                             attrs.get("usage.total_tokens") or \
                             attrs.get("gen_ai.usage.input_tokens", 0) + attrs.get("gen_ai.usage.output_tokens", 0)

                    cost = attrs.get("traceloop.cost.usd") or \
                           attrs.get("llm.usage.cost") or \
                           attrs.get("usage.cost")

                    # Basic span data
                    formatted.append({
                        "span_id": format(span.context.span_id, '016x'),
                        "trace_id": format(span.context.trace_id, '032x'),
                        "parent_span_id": format(span.parent.span_id, '016x') if span.parent else None,
                        "name": span.name,
                        "kind": str(span.kind),
                        "status": span.status.status_code.name,
                        "start_time": datetime.fromtimestamp(span.start_time / 1e9).isoformat(),
                        "end_time": datetime.fromtimestamp(span.end_time / 1e9).isoformat() if span.end_time else None,
                        "duration_ms": int((span.end_time - span.start_time) / 1e6) if span.end_time else None,
                        "attributes": attrs,
                        "tokens_used": int(tokens) if tokens is not None and tokens > 0 else None,
                        "estimated_cost": float(cost) if cost is not None else None,
                        "events": [
                            {"name": event.name, "timestamp": datetime.fromtimestamp(event.timestamp / 1e9).isoformat(), "attributes": dict(event.attributes or {})}
                            for event in span.events
                        ]
                    })

                if formatted:
                    try:
                        try:
                            loop = asyncio.get_running_loop()
                            loop.create_task(cloud_uploader.add_spans(formatted))
                        except RuntimeError:
                            asyncio.run(cloud_uploader.add_spans(formatted))
                    except Exception:
                        pass  # Silently ignore upload errors

                return SpanExportResult.SUCCESS

            def shutdown(self):
                pass

        processors.append(SimpleSpanProcessor(SupabaseSpanExporter()))

    # Initialize Traceloop
    Traceloop.init(
        app_name=app_name,
        disable_batch=True,
        processor=processors if processors else None
    )

    tracer = trace.get_tracer("agora_tracer")

    if enable_cloud_upload and SUPABASE_UPLOADER_AVAILABLE:
        cloud_uploader = SupabaseUploader(
            project_name=project_name or app_name,
            api_key=api_key
        )
        cloud_uploader.batch_size = 1  # Immediate flushing
    elif enable_cloud_upload and not SUPABASE_UPLOADER_AVAILABLE:
        print("⚠️  Supabase upload not available (install supabase-py: pip install supabase)")

    _initialized = True
    print(f"✅ agora initialized: {app_name}")


# ==============================================================
# DECORATOR - Wrap functions into TracedAsyncNode
# ==============================================================

def agora_node(name=None, max_retries=1, wait=0, capture_io=None):
    """
    Decorator to convert any function into a TracedAsyncNode.
    This allows you to wrap existing functions without subclassing.
    The function receives the shared dict and can read/write to it.
    Usage:
        @agora_node(name="MyAgent")
        async def my_agent(shared):
            # Access shared state
            user_input = shared.get("input", "")
            # Do your work (existing code!)
            result = await openai.call(user_input)
            # Store results
            shared["result"] = result
            # Return action for routing
            return "next"
    Args:
        name: Optional node name (defaults to function name)
        max_retries: Number of retry attempts (default: 1)
        wait: Wait time between retries in seconds (default: 0)
        capture_io: Whether to log input/output in spans (default: use global setting)
    Returns:
        TracedAsyncNode instance with your function as exec_async
    """
    def decorator(func):
        # Get function name if name not provided
        node_name = name or func.__name__

        # Check if function is async or sync
        is_async = inspect.iscoroutinefunction(func)
        
        # Determine capture_io setting
        should_capture_io = capture_io if capture_io is not None else _capture_io_default

        # Capture the original function's source code
        try:
            actual_code = inspect.getsource(func)
        except Exception:
            actual_code = None

        # Create a custom node class dynamically
        class DecoratedNode(TracedAsyncNode):
            def __init__(self):
                super().__init__(node_name, max_retries=max_retries, wait=wait)
                self._wrapped_func = func
                self._capture_io = should_capture_io
                self.code = actual_code

            async def exec_async(self, prep_res):
                """
                Execute the wrapped function.
                prep_res is the shared dict passed from prep_async.
                """
                if is_async:
                    # Async function - await it directly
                    return await self._wrapped_func(prep_res)
                else:
                    # Sync function - run in thread to avoid blocking
                    return await asyncio.to_thread(self._wrapped_func, prep_res)

            async def prep_async(self, shared):
                """
                Default prep: just pass the shared dict to exec.
                Users can still subclass if they need custom prep/post.
                """
                return shared

            async def post_async(self, shared, prep_res, exec_res):
                """
                Default post: return the exec result as the action.
                This allows the wrapped function's return value to control routing.
                """
                return exec_res

        # Return an instance of the node
        return DecoratedNode()

    return decorator


def task(name=None, max_retries=1, wait=0):
    """
    Alias for @agora_node decorator - matches common terminology.
    Usage:
        @task(name="ProcessData")
        def process_data(shared):
            return shared["data"].upper()
    """
    return agora_node(name=name, max_retries=max_retries, wait=wait)


# ==============================================================
# TRACED CLASSES
# ==============================================================

# Traced classes (same as before)
class TracedAsyncNode(AsyncNode):
    """AsyncNode with automatic telemetry"""

    async def _traced_prep(self, shared):
        with trace.get_tracer("agora_tracer").start_as_current_span(f"{self.name}.prep") as span:
            span.set_attribute("agora.node", self.name)
            span.set_attribute("agora.phase", "prep")
            start = time.time()
            try:
                result = await self.prep_async(shared)
                span.set_attribute("duration_ms", int((time.time() - start) * 1000))
                return result
            except Exception as e:
                span.record_exception(e)
                raise

    async def _traced_exec(self, prep_res, retry_count=0):
        with trace.get_tracer("agora_tracer").start_as_current_span(f"{self.name}.exec") as span:
            span.set_attribute("agora.node", self.name)
            span.set_attribute("agora.phase", "exec")
            span.set_attribute("retry_count", retry_count)
            start = time.time()
            
            # Capture input if enabled
            if getattr(self, '_capture_io', _capture_io_default):
                try:
                    import json
                    input_str = json.dumps(prep_res, default=str)[:1000]  # Limit to 1000 chars
                    span.set_attribute("input", input_str)
                except:
                    span.set_attribute("input", str(prep_res)[:1000])
            
            try:
                result = await self.exec_async(prep_res)
                span.set_attribute("duration_ms", int((time.time() - start) * 1000))
                
                # Capture output if enabled
                if getattr(self, '_capture_io', _capture_io_default):
                    try:
                        import json
                        output_str = json.dumps(result, default=str)[:1000]
                        span.set_attribute("output", output_str)
                    except:
                        span.set_attribute("output", str(result)[:1000])
                
                return result
            except Exception as e:
                span.record_exception(e)
                raise

    async def _traced_post(self, shared, prep_res, exec_res):
        with trace.get_tracer("agora_tracer").start_as_current_span(f"{self.name}.post") as span:
            span.set_attribute("agora.node", self.name)
            span.set_attribute("agora.phase", "post")
            start = time.time()
            try:
                result = await self.post_async(shared, prep_res, exec_res)
                span.set_attribute("duration_ms", int((time.time() - start) * 1000))
                span.set_attribute("next_action", str(result))
                return result
            except Exception as e:
                span.record_exception(e)
                raise

    async def _exec_async(self, prep_res):
        for retry in range(self.max_retries):
            try:
                return await self._traced_exec(prep_res, retry)
            except Exception as e:
                if retry == self.max_retries - 1:
                    return await self.exec_fallback_async(prep_res, e)
                if self.wait > 0:
                    await asyncio.sleep(self.wait)

    async def _run_async(self, shared):
        global cloud_uploader
        
        # Sampling: skip tracing if sampling rate check fails
        if random.random() > _sampling_rate:
            # Run without tracing
            await self.before_run_async(shared)
            try:
                prep_res = await self.prep_async(shared)
                exec_res = await self.exec_async(prep_res)
                post_res = await self.post_async(shared, prep_res, exec_res)
                await self.after_run_async(shared)
                return post_res
            except Exception as exc:
                return await self.on_error_async(exc, shared)

        with trace.get_tracer("agora_tracer").start_as_current_span(f"{self.name}.node") as span:
            span.set_attribute("agora.node", self.name)
            span.set_attribute("agora.kind", "node")
            node_start = time.time()
            started_at = datetime.utcnow()
            await self.before_run_async(shared)
            try:
                prep_res = await self._traced_prep(shared)
                exec_res = await self._exec_async(prep_res)
                post_res = await self._traced_post(shared, prep_res, exec_res)
                await self.after_run_async(shared)
                completed_at = datetime.utcnow()
                total_duration = int((time.time() - node_start) * 1000)
                span.set_attribute("total_duration_ms", total_duration)

                if cloud_uploader and cloud_uploader.enabled and cloud_uploader.execution_id:
                    await cloud_uploader.add_node_execution(
                        node_name=self.name,
                        node_type="async_node",
                        status="success",
                        started_at=started_at,
                        completed_at=completed_at,
                        exec_duration_ms=int(total_duration),
                        code=getattr(self, 'code', None)
                    )

                return post_res
            except Exception as exc:
                span.record_exception(exc)
                completed_at = datetime.utcnow()

                if cloud_uploader and cloud_uploader.enabled and cloud_uploader.execution_id:
                    await cloud_uploader.add_node_execution(
                        node_name=self.name,
                        node_type="async_node",
                        status="error",
                        started_at=started_at,
                        completed_at=completed_at,
                        error_message=str(exc),
                        code=getattr(self, 'code', None)
                    )

                return await self.on_error_async(exc, shared)


class TracedAsyncFlow(AsyncFlow):
    """AsyncFlow with automatic telemetry and cloud upload"""

    async def _run_async(self, shared):
        global cloud_uploader
        
        # Sampling: skip tracing if sampling rate check fails
        if random.random() > _sampling_rate:
            # Run without tracing
            await self.before_run_async(shared)
            try:
                prep_res = await self.prep_async(shared)
                orch_res = await self._orch_async(shared)
                post_res = await self.post_async(shared, prep_res, orch_res)
                await self.after_run_async(shared)
                return post_res
            except Exception as exc:
                return await self.on_error_async(exc, shared)

        execution_id = None
        if cloud_uploader and cloud_uploader.enabled:
            execution_id = await cloud_uploader.start_execution(
                workflow_name=self.name,
                input_data=shared.copy() if isinstance(shared, dict) else {}
            )
            # Register the workflow graph structure (nodes and edges)
            if hasattr(self, 'to_dict'):
                await cloud_uploader.register_workflow_graph(self.to_dict())

        with trace.get_tracer("agora_tracer").start_as_current_span(f"{self.name}.flow") as span:
            span.set_attribute("agora.flow", self.name)
            if execution_id:
                span.set_attribute("execution_id", str(execution_id))
            flow_start = time.time()
            await self.before_run_async(shared)
            try:
                prep_res = await self.prep_async(shared)
                orch_res = await self._orch_async(shared)
                post_res = await self.post_async(shared, prep_res, orch_res)
                await self.after_run_async(shared)
                total_duration = int((time.time() - flow_start) * 1000)
                span.set_attribute("total_duration_ms", total_duration)

                if cloud_uploader and cloud_uploader.enabled:
                    await cloud_uploader.complete_execution(
                        status="success",
                        output_data=shared.copy() if isinstance(shared, dict) else {}
                    )

                return post_res
            except Exception as exc:
                span.record_exception(exc)

                if cloud_uploader and cloud_uploader.enabled:
                    await cloud_uploader.complete_execution(
                        status="error",
                        error_message=str(exc)
                    )

                return await self.on_error_async(exc, shared)


# Backward compatibility alias
init_traceloop = init_agora

# Export public API
__all__ = [
    'init_agora',
    'init_traceloop',  # Backward compatibility
    'TracedAsyncNode',
    'TracedAsyncFlow',
    'agora_node',  # Decorator for wrapping functions
    'task',        # Alias for agora_node
]
