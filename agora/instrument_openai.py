import time
from typing import Any, Dict, List, Optional

try:
    from opentelemetry import trace
    from opentelemetry.trace import Status, StatusCode
    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    trace = None


def trace_openai_call(client, **kwargs) -> Any:
    """
    Wrapper around client.chat.completions.create with OpenTelemetry tracing.
    
    Captures Traceloop-style attributes:
    - llm.provider, llm.operation, llm.model
    - llm.temperature, llm.top_p, llm.max_tokens
    - prompt.preview, response.preview
    - tokens.prompt, tokens.completion
    - llm.api.latency_ms
    
    Args:
        client: OpenAI client instance
        **kwargs: Arguments passed to client.chat.completions.create()
    
    Returns:
        OpenAI completion response object
    
    Example:
        >>> from openai import OpenAI
        >>> from agora.instrument_openai import trace_openai_call
        >>> 
        >>> client = OpenAI()
        >>> response = trace_openai_call(
        ...     client,
        ...     model="gpt-4o-mini",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
        >>> print(response.choices[0].message.content)
    """
    if not OTEL_AVAILABLE:
        # Fallback: call API without tracing
        return client.chat.completions.create(**kwargs)
    
    # Get tracer
    tracer = trace.get_tracer(__name__)
    
    # Start span
    with tracer.start_as_current_span("openai.chat.completions.create") as span:
        # Extract parameters
        model = kwargs.get("model", "unknown")
        messages = kwargs.get("messages", [])
        temperature = kwargs.get("temperature")
        top_p = kwargs.get("top_p")
        max_tokens = kwargs.get("max_tokens")
        
        # Set basic LLM attributes
        span.set_attribute("llm.provider", "openai")
        span.set_attribute("llm.operation", "chat.completions.create")
        span.set_attribute("llm.model", model)
        
        if temperature is not None:
            span.set_attribute("llm.temperature", str(temperature))
        if top_p is not None:
            span.set_attribute("llm.top_p", str(top_p))
        if max_tokens is not None:
            span.set_attribute("llm.max_tokens", str(max_tokens))
        
        # Extract prompt preview (first 500 chars of last user message)
        prompt_preview = _extract_prompt_preview(messages)
        if prompt_preview:
            span.set_attribute("prompt.preview", prompt_preview[:500])
        
        # Record start time
        start_time = time.time()
        
        try:
            # Make the API call
            response = client.chat.completions.create(**kwargs)
            
            # Calculate latency
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("llm.api.latency_ms", str(round(latency_ms, 2)))
            
            # Extract response preview
            response_text = response.choices[0].message.content if response.choices else ""
            span.set_attribute("response.preview", response_text[:500])
            span.set_attribute("result_type", type(response_text).__name__)
            
            # Extract token usage
            if hasattr(response, 'usage') and response.usage:
                if hasattr(response.usage, 'prompt_tokens'):
                    span.set_attribute("tokens.prompt", str(response.usage.prompt_tokens))
                if hasattr(response.usage, 'completion_tokens'):
                    span.set_attribute("tokens.completion", str(response.usage.completion_tokens))
                if hasattr(response.usage, 'total_tokens'):
                    span.set_attribute("tokens.total", str(response.usage.total_tokens))
            
            # Mark span as successful
            span.set_status(Status(StatusCode.OK))
            
            return response
            
        except Exception as e:
            # Record exception
            latency_ms = (time.time() - start_time) * 1000
            span.set_attribute("llm.api.latency_ms", str(round(latency_ms, 2)))
            
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.set_attribute("error.type", type(e).__name__)
            span.set_attribute("error.message", str(e))
            
            raise


def _extract_prompt_preview(messages: List[Dict[str, str]]) -> Optional[str]:
    """
    Extract prompt text from messages list.
    
    Returns the content of the last user message, or concatenates
    all messages if no user message is found.
    """
    if not messages:
        return None
    
    # Try to find last user message
    for msg in reversed(messages):
        if msg.get("role") == "user":
            return msg.get("content", "")
    
    # Fallback: concatenate all messages
    return " ".join(msg.get("content", "") for msg in messages)


# ======================================================================
# OPTIONAL: Auto-instrumentation wrapper
# ======================================================================

def instrument_openai_client(client):
    """
    Monkey-patch an OpenAI client to automatically trace all API calls.
    
    Args:
        client: OpenAI client instance to instrument
    
    Returns:
        The same client instance with tracing enabled
    
    Example:
        >>> from openai import OpenAI
        >>> from agora.instrument_openai import instrument_openai_client
        >>> 
        >>> client = OpenAI()
        >>> instrument_openai_client(client)
        >>> 
        >>> # All subsequent calls are automatically traced
        >>> response = client.chat.completions.create(
        ...     model="gpt-4o-mini",
        ...     messages=[{"role": "user", "content": "Hello!"}]
        ... )
    """
    if not OTEL_AVAILABLE:
        return client
    
    # Store original method
    original_create = client.chat.completions.create
    
    # Create wrapper
    def traced_create(**kwargs):
        return trace_openai_call(client, **kwargs)
    
    # Replace method
    client.chat.completions.create = traced_create
    
    return client
