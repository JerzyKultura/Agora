"""
OpenTelemetry initialization for Agora workflows.

This module provides a simple setup function for local OpenTelemetry tracing
without external exporters. Traces are printed to console and can be exported
to JSON format.
"""

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource


def init_otel(service_name="agora", console=True, output_path="./traces"):
    """
    Initialize OpenTelemetry with local console exporter.
    
    Args:
        service_name: Name of the service for trace identification
        console: Whether to print spans to console (default: True)
        output_path: Directory path for future JSON exports (default: "./traces")
    
    Returns:
        TracerProvider instance
    
    Example:
        >>> from agora.telemetry.instrument import init_otel
        >>> init_otel("my-workflow")
        ✅ OpenTelemetry initialized for my-workflow
    """
    # Create resource with service name
    resource = Resource.create({"service.name": service_name})
    
    # Create and set tracer provider
    provider = TracerProvider(resource=resource)
    trace.set_tracer_provider(provider)
    
    # Add console exporter if requested
    if console:
        console_exporter = ConsoleSpanExporter()
        console_processor = SimpleSpanProcessor(console_exporter)
        provider.add_span_processor(console_processor)
    
    print(f"✅ OpenTelemetry initialized for {service_name}")
    
    # Store configuration for future use (e.g., JSON export)
    provider._agora_config = {
        "service_name": service_name,
        "output_path": output_path
    }
    
    return provider
