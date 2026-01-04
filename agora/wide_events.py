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
from opentelemetry.sdk.trace import SpanProcessor, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult
from contextvars import ContextVar

# Thread-safe storage for current business context
_current_business_context: ContextVar[Optional['BusinessContext']] = ContextVar('business_context', default=None)


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


# ============================================================================
# PLUG-AND-PLAY API: Set context once, enriches ALL spans automatically!
# ============================================================================

def set_business_context(context: Optional[BusinessContext] = None, **kwargs) -> None:
    """
    Set the business context that will be automatically added to ALL future spans.

    This is the EASIEST way to use wide events - just set the context once,
    and every LLM call will automatically include it!

    Args:
        context: A BusinessContext object, OR
        **kwargs: Pass context fields directly (user_id, subscription_tier, etc.)

    Example 1 - Pass a BusinessContext:
        context = BusinessContext(user_id="user_123", subscription_tier="premium")
        set_business_context(context)

        # Now ALL LLM calls automatically get enriched!
        response = client.chat.completions.create(...)  # ✅ Has business context!

    Example 2 - Pass kwargs directly:
        set_business_context(
            user_id="user_123",
            subscription_tier="premium",
            lifetime_value_cents=50000,
            feature_flags={"new_ui": True}
        )

        # Now ALL LLM calls automatically get enriched!
        response = client.chat.completions.create(...)  # ✅ Has business context!
    """
    if context is None and kwargs:
        context = BusinessContext(**kwargs)

    _current_business_context.set(context)


def get_business_context() -> Optional[BusinessContext]:
    """Get the currently set business context."""
    return _current_business_context.get()


def clear_business_context() -> None:
    """Clear the business context (stop enriching spans)."""
    _current_business_context.set(None)


class BusinessContextSpanProcessor(SpanProcessor):
    """
    Span processor that automatically enriches ALL spans with business context.

    This is what makes the plug-and-play API work! When you call set_business_context(),
    this processor reads it and adds it to every span that gets created.
    """

    def on_start(self, span: Span, parent_context=None) -> None:
        """Called when a span starts - enrich it with business context if set."""
        context = get_business_context()
        if context:
            try:
                attributes = context.to_attributes()
                span.set_attributes(attributes)
            except Exception as e:
                # Don't crash the span if enrichment fails
                print(f"⚠️  Failed to enrich span with business context: {e}")

    def on_end(self, span: ReadableSpan) -> None:
        """Called when a span ends - nothing to do."""
        pass

    def shutdown(self) -> None:
        """Called on shutdown - nothing to do."""
        pass

    def force_flush(self, timeout_millis: int = 30000) -> bool:
        """Called to force flush - nothing to do."""
        return True
