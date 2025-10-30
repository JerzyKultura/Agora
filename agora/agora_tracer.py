# ==============================================================
# agora_tracer.py - COMPLETE STANDALONE MODULE
# ==============================================================

"""
Traceloop integration for Agora workflows.

Usage:
    from agora_tracer import TracedAsyncNode, init_traceloop
    
    # Initialize once at start
    init_traceloop(app_name="my_app", export_to_console=True)
    
    # Use traced classes
    class MyNode(TracedAsyncNode):
        async def exec_async(self, data):
            return process(data)
"""

from opentelemetry import trace
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from traceloop.sdk import Traceloop
from agora import AsyncNode, AsyncFlow, AsyncBatchNode, AsyncParallelBatchNode
import os, time, asyncio

_initialized = False
tracer = None

def init_traceloop(
    app_name="agora_app",
    export_to_console=True,
    export_to_file=None,
    disable_content_logging=True
):
    """
    Initialize Traceloop for Agora telemetry.
    
    Args:
        app_name: Name of your application
        export_to_console: Print spans to console (default: True)
        export_to_file: Path to JSONL file for export (default: None)
        disable_content_logging: Don't log prompt/response content (default: True)
    """
    global _initialized, tracer
    
    if _initialized:
        print("⚠️  Traceloop already initialized")
        return
    
    # Configure environment
    if disable_content_logging:
        os.environ["TRACELOOP_TRACE_CONTENT"] = "false"
    os.environ["TRACELOOP_TELEMETRY"] = "false"
    os.environ["TRACELOOP_SUPPRESS_WARNINGS"] = "true"
    
    # Create processors
    processors = []
    
    if export_to_console:
        processors.append(SimpleSpanProcessor(ConsoleSpanExporter()))
    
    if export_to_file:
        from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult
        from opentelemetry.sdk.trace import ReadableSpan
        from typing import Sequence
        import json
        from datetime import datetime
        
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
    
    # Initialize Traceloop
    Traceloop.init(
        app_name=app_name,
        disable_batch=True,
        processor=processors if processors else None
    )
    
    tracer = trace.get_tracer("agora_tracer")
    _initialized = True
    print(f"✅ Traceloop initialized: {app_name}")


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
                span.set_attribute("duration_ms", round((time.time() - start) * 1000, 2))
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
            try:
                result = await self.exec_async(prep_res)
                span.set_attribute("duration_ms", round((time.time() - start) * 1000, 2))
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
                span.set_attribute("duration_ms", round((time.time() - start) * 1000, 2))
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
        with trace.get_tracer("agora_tracer").start_as_current_span(f"{self.name}.node") as span:
            span.set_attribute("agora.node", self.name)
            span.set_attribute("agora.kind", "node")
            node_start = time.time()
            await self.before_run_async(shared)
            try:
                prep_res = await self._traced_prep(shared)
                exec_res = await self._exec_async(prep_res)
                post_res = await self._traced_post(shared, prep_res, exec_res)
                await self.after_run_async(shared)
                span.set_attribute("total_duration_ms", round((time.time() - node_start) * 1000, 2))
                return post_res
            except Exception as exc:
                span.record_exception(exc)
                return await self.on_error_async(exc, shared)


class TracedAsyncFlow(AsyncFlow):
    """AsyncFlow with automatic telemetry"""
    
    async def _run_async(self, shared):
        with trace.get_tracer("agora_tracer").start_as_current_span(f"{self.name}.flow") as span:
            span.set_attribute("agora.flow", self.name)
            flow_start = time.time()
            await self.before_run_async(shared)
            try:
                prep_res = await self.prep_async(shared)
                orch_res = await self._orch_async(shared)
                post_res = await self.post_async(shared, prep_res, orch_res)
                await self.after_run_async(shared)
                span.set_attribute("total_duration_ms", round((time.time() - flow_start) * 1000, 2))
                return post_res
            except Exception as exc:
                span.record_exception(exc)
                return await self.on_error_async(exc, shared)


# Export public API
__all__ = ['init_traceloop', 'TracedAsyncNode', 'TracedAsyncFlow']
