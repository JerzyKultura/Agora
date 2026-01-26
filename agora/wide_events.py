"""
Wide Event / Business Context Enrichment for Agora

This module provides helpers to enrich OpenTelemetry spans with business context,
following the "wide events" pattern described in modern observability practices.

Instead of just capturing:
    - Model name
    - Tokens used
    - Prompt/completion

We also capture:
    - User context (subscription, LTV, account age)
    - Feature flags
    - Session context
    - Business metrics
    - App-specific context

This makes debugging and analytics WAY more powerful.
"""

from typing import Dict, Any, Optional
from opentelemetry import trace
from opentelemetry.trace import Span
from datetime import datetime


class BusinessContext:
    """
    Container for business context that should be attached to telemetry spans.

    Usage:
        context = BusinessContext(
            user_id="user_123",
            subscription_tier="premium",
            feature_flags={"new_chat_ui": True}
        )
        enrich_current_span(context)
    """

    def __init__(
        self,
        # User context
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        subscription_tier: Optional[str] = None,  # free, pro, enterprise
        lifetime_value_cents: Optional[int] = None,
        account_age_days: Optional[int] = None,

        # Session context
        session_id: Optional[str] = None,
        conversation_turn: Optional[int] = None,
        total_tokens_this_session: Optional[int] = None,

        # Feature flags
        feature_flags: Optional[Dict[str, bool]] = None,

        # App-specific context
        workflow_type: Optional[str] = None,  # e.g., "customer_support", "sales", "research"
        priority: Optional[str] = None,  # e.g., "high", "medium", "low"
        app_version: Optional[str] = None,

        # Business metrics
        cart_value_cents: Optional[int] = None,
        items_in_cart: Optional[int] = None,

        # Custom attributes
        custom: Optional[Dict[str, Any]] = None
    ):
        self.user_id = user_id
        self.user_email = user_email
        self.subscription_tier = subscription_tier
        self.lifetime_value_cents = lifetime_value_cents
        self.account_age_days = account_age_days

        self.session_id = session_id
        self.conversation_turn = conversation_turn
        self.total_tokens_this_session = total_tokens_this_session

        self.feature_flags = feature_flags or {}

        self.workflow_type = workflow_type
        self.priority = priority
        self.app_version = app_version

        self.cart_value_cents = cart_value_cents
        self.items_in_cart = items_in_cart

        self.custom = custom or {}

    def to_attributes(self) -> Dict[str, Any]:
        """Convert business context to OpenTelemetry span attributes"""
        attrs = {}

        # User context
        if self.user_id:
            attrs["user.id"] = self.user_id
        if self.user_email:
            attrs["user.email"] = self.user_email
        if self.subscription_tier:
            attrs["user.subscription_tier"] = self.subscription_tier
        if self.lifetime_value_cents is not None:
            attrs["user.lifetime_value_cents"] = self.lifetime_value_cents
        if self.account_age_days is not None:
            attrs["user.account_age_days"] = self.account_age_days

        # Session context
        if self.session_id:
            attrs["session.id"] = self.session_id
        if self.conversation_turn is not None:
            attrs["session.conversation_turn"] = self.conversation_turn
        if self.total_tokens_this_session is not None:
            attrs["session.total_tokens"] = self.total_tokens_this_session

        # Feature flags
        for flag_name, enabled in self.feature_flags.items():
            attrs[f"feature_flags.{flag_name}"] = enabled

        # App-specific
        if self.workflow_type:
            attrs["app.workflow_type"] = self.workflow_type
        if self.priority:
            attrs["app.priority"] = self.priority
        if self.app_version:
            attrs["app.version"] = self.app_version

        # Business metrics
        if self.cart_value_cents is not None:
            attrs["business.cart_value_cents"] = self.cart_value_cents
        if self.items_in_cart is not None:
            attrs["business.items_in_cart"] = self.items_in_cart

        # Custom attributes
        for key, value in self.custom.items():
            attrs[f"custom.{key}"] = value

        return attrs


def enrich_span(span: Span, context: BusinessContext) -> None:
    """
    Enrich an OpenTelemetry span with business context.

    Args:
        span: The span to enrich
        context: Business context to add

    Example:
        with tracer.start_as_current_span("chat_completion") as span:
            enrich_span(span, context)
            response = client.chat.completions.create(...)
    """
    if span is None:
        return

    attributes = context.to_attributes()
    span.set_attributes(attributes)


def enrich_current_span(context: BusinessContext) -> None:
    """
    Enrich the current active span with business context.

    This is the easiest way to add context - just call this function
    and it will enrich whatever span is currently active.

    Example:
        # Traceloop auto-instruments this, creating a span
        enrich_current_span(context)  # Add your business context
        response = client.chat.completions.create(...)
    """
    span = trace.get_current_span()
    if span is None:
        print("⚠️  No active span to enrich. Make sure telemetry is initialized.")
        return

    enrich_span(span, context)


def create_wide_event_decorator(context_builder):
    """
    Decorator that automatically enriches spans with business context.

    Args:
        context_builder: Function that takes request args and returns BusinessContext

    Example:
        def build_context(user_id, session_id):
            user = get_user(user_id)
            return BusinessContext(
                user_id=user_id,
                subscription_tier=user.subscription,
                session_id=session_id
            )

        @create_wide_event_decorator(build_context)
        def process_chat(user_id, session_id, message):
            enrich_current_span(build_context(user_id, session_id))
            return client.chat.completions.create(...)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Build context from function args
            context = context_builder(*args, **kwargs)

            # Enrich current span
            enrich_current_span(context)

            # Call original function
            return func(*args, **kwargs)

        return wrapper
    return decorator


# Quick helper for common use cases
def enrich_with_user(
    user_id: str,
    subscription_tier: str = None,
    lifetime_value_cents: int = None,
    **kwargs
):
    """
    Quick helper to enrich current span with user context.

    Example:
        enrich_with_user(
            user_id="user_123",
            subscription_tier="premium",
            lifetime_value_cents=50000
        )
        response = client.chat.completions.create(...)
    """
    context = BusinessContext(
        user_id=user_id,
        subscription_tier=subscription_tier,
        lifetime_value_cents=lifetime_value_cents,
        **kwargs
    )
    enrich_current_span(context)


def enrich_with_feature_flags(flags: Dict[str, bool]):
    """
    Quick helper to enrich current span with feature flags.

    Example:
        enrich_with_feature_flags({
            "new_chat_ui": True,
            "gpt4_access": True,
            "experimental_mode": False
        })
    """
    context = BusinessContext(feature_flags=flags)
    enrich_current_span(context)


# ==============================================================
# WIDE EVENT EMISSION TO SUPABASE
# ==============================================================

from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan
from collections import defaultdict
import os
import json

class BusinessContextSpanProcessor(SpanProcessor):
    """
    Span processor that collects all spans for an execution and emits
    ONE wide event to Supabase when the execution completes.
    
    This implements the "wide events" pattern: one comprehensive event
    per execution with all business context.
    """
    
    def __init__(self):
        self.executions = defaultdict(list)  # execution_id -> list of spans
        self.supabase_client = None
        
        # Try to initialize Supabase client
        try:
            from supabase import create_client
            url = os.getenv("VITE_SUPABASE_URL", "").strip('"')
            key = os.getenv("VITE_SUPABASE_ANON_KEY", "").strip('"')
            
            if url and key:
                self.supabase_client = create_client(url, key)
                print("✅ Wide events: Supabase client initialized")
        except Exception as e:
            print(f"⚠️  Wide events: Supabase client not available: {e}")
    
    def on_start(self, span: ReadableSpan, parent_context=None):
        """Called when a span starts - we don't need to do anything here"""
        pass
    
    def on_end(self, span: ReadableSpan):
        """Called when a span ends - collect it for wide event emission"""
        if not span:
            return
        
        # Extract execution_id from span attributes
        execution_id = None
        for key, value in (span.attributes or {}).items():
            if key == "execution_id":
                execution_id = value
                break
        
        if not execution_id:
            return  # Not part of an Agora execution
        
        # Add span to execution collection
        self.executions[execution_id].append(span)
        
        # Check if this is the root span (workflow completion)
        # Root spans have kind = INTERNAL and name ending in ".flow"
        is_root = (
            span.name.endswith(".flow") or 
            span.name.endswith("Flow") or
            "workflow" in span.name.lower()
        )
        
        if is_root:
            # Execution complete - emit wide event
            self._emit_wide_event(execution_id)
    
    def _emit_wide_event(self, execution_id: str):
        """Emit one wide event for the entire execution"""
        if not self.supabase_client:
            return
        
        spans = self.executions.get(execution_id, [])
        if not spans:
            return
        
        try:
            # Aggregate data from all spans
            root_span = spans[0]  # First span is usually the root
            
            # Extract node path (ordered list of nodes executed)
            node_path = [s.name for s in sorted(spans, key=lambda s: s.start_time)]
            
            # Calculate total duration
            start_times = [s.start_time for s in spans]
            end_times = [s.end_time for s in spans if s.end_time]
            
            if start_times and end_times:
                duration_ns = max(end_times) - min(start_times)
                duration_ms = int(duration_ns / 1_000_000)
            else:
                duration_ms = 0
            
            # Aggregate performance metrics
            total_tokens = sum(
                s.attributes.get("llm.usage.total_tokens", 0) 
                for s in spans if s.attributes
            )
            
            total_cost = sum(
                float(s.attributes.get("gen_ai.usage.cost", 0) or 0)
                for s in spans if s.attributes
            )
            
            llm_calls = sum(
                1 for s in spans 
                if s.attributes and "llm" in s.name.lower()
            )
            
            # Extract business context from root span
            attrs = root_span.attributes or {}
            
            # Determine status
            status = "success"
            error_type = None
            error_message = None
            
            for span in spans:
                if span.status and hasattr(span.status, 'status_code'):
                    if str(span.status.status_code) == "StatusCode.ERROR":
                        status = "error"
                        # Try to get error details
                        if span.events:
                            for event in span.events:
                                if event.name == "exception":
                                    error_type = event.attributes.get("exception.type")
                                    error_message = event.attributes.get("exception.message")
                        break
            
            # Build wide event
            wide_event = {
                "execution_id": execution_id,
                "trace_id": str(root_span.context.trace_id) if root_span.context else None,
                "timestamp": datetime.fromtimestamp(root_span.start_time / 1_000_000_000).isoformat(),
                
                # Workflow context
                "workflow_name": root_span.name,
                "workflow_version": attrs.get("app.version"),
                "node_path": node_path,
                
                # User/Org context
                "user_id": attrs.get("user.id"),
                "organization_id": os.getenv("AGORA_ORG_ID"),
                "subscription_tier": attrs.get("user.subscription_tier"),
                "account_age_days": attrs.get("user.account_age_days"),
                
                # Performance
                "duration_ms": duration_ms,
                "tokens_used": int(total_tokens) if total_tokens else None,
                "estimated_cost": float(total_cost) if total_cost else None,
                "llm_calls_count": llm_calls if llm_calls > 0 else None,
                
                # Outcome
                "status": status,
                "error_type": error_type,
                "error_message": error_message,
                
                # Context
                "feature_flags": self._extract_feature_flags(attrs),
                "deployment_id": os.getenv("DEPLOYMENT_ID"),
                "region": os.getenv("REGION", "local"),
                "service_version": os.getenv("SERVICE_VERSION"),
                
                # Full event as JSONB
                "event": {
                    "execution_id": execution_id,
                    "node_path": node_path,
                    "duration_ms": duration_ms,
                    "tokens_used": total_tokens,
                    "cost": total_cost,
                    "llm_calls": llm_calls,
                    "status": status,
                    "attributes": dict(attrs) if attrs else {}
                }
            }
            
            # Insert into Supabase
            self.supabase_client.table('telemetry_wide_events').insert(wide_event).execute()
            
            print(f"✅ Wide event emitted: {execution_id} ({status}, {duration_ms}ms)")
            
        except Exception as e:
            print(f"❌ Failed to emit wide event: {e}")
        finally:
            # Clean up collected spans
            del self.executions[execution_id]
    
    def _extract_feature_flags(self, attrs: dict) -> dict:
        """Extract feature flags from span attributes"""
        flags = {}
        for key, value in (attrs or {}).items():
            if key.startswith("feature_flags."):
                flag_name = key.replace("feature_flags.", "")
                flags[flag_name] = value
        return flags if flags else None
    
    def shutdown(self):
        """Called when processor is shutting down"""
        pass
    
    def force_flush(self, timeout_millis: int = 30000):
        """Force flush any pending events"""
        return True