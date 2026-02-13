"""
OpenTelemetry Span Transformer

Flattens nested OTel JSON structure into flat Supabase records.

Key Features:
- Converts OTel attributes array to flat JSONB dict
- Handles hex trace/span IDs (keeps as strings, not UUIDs)
- Converts nanosecond timestamps to ISO 8601
- Calculates duration in milliseconds
- Maps OTel enums to human-readable strings
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from models.otel import (
    OTelTracesData,
    OTelKeyValue,
    OTelValue,
    OTelResourceSpans,
    OTelScopeSpans,
    OTelSpan
)


def flatten_otel_attributes(attributes: List[OTelKeyValue]) -> Dict[str, Any]:
    """
    Flatten OTel attributes array into a simple dict.
    
    Converts:
      [{"key": "http.method", "value": {"stringValue": "GET"}}]
    To:
      {"http.method": "GET"}
    
    Handles int-as-string (some SDKs send "123" instead of 123).
    
    Args:
        attributes: List of OTel key-value pairs
        
    Returns:
        Flat dictionary with extracted values
    """
    result = {}
    
    for attr in attributes:
        key = attr.key
        value = attr.value
        
        # Extract the actual value based on type
        if value.stringValue is not None:
            result[key] = value.stringValue
        elif value.intValue is not None:
            # Handle int-as-string (convert to int if possible)
            if isinstance(value.intValue, str):
                try:
                    result[key] = int(value.intValue)
                except ValueError:
                    result[key] = value.intValue  # Keep as string if not parseable
            else:
                result[key] = value.intValue
        elif value.doubleValue is not None:
            result[key] = value.doubleValue
        elif value.boolValue is not None:
            result[key] = value.boolValue
        elif value.bytesValue is not None:
            result[key] = value.bytesValue
        elif value.arrayValue is not None:
            result[key] = value.arrayValue
        elif value.kvlistValue is not None:
            result[key] = value.kvlistValue
    
    return result


def nano_to_iso(nano_timestamp: str) -> str:
    """
    Convert Unix nanoseconds to ISO 8601 timestamp.
    
    Example: "1704067200000000000" -> "2024-01-01T00:00:00.000000+00:00"
    
    Args:
        nano_timestamp: Unix timestamp in nanoseconds (as string)
        
    Returns:
        ISO 8601 formatted timestamp string
    """
    nanos = int(nano_timestamp)
    seconds = nanos / 1_000_000_000
    dt = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return dt.isoformat()


def calculate_duration_ms(start_nano: str, end_nano: Optional[str]) -> Optional[int]:
    """
    Calculate duration in milliseconds from nano timestamps.
    
    Handles missing or empty end times (active spans).
    
    Args:
        start_nano: Start time in nanoseconds
        end_nano: End time in nanoseconds (may be None or empty for active spans)
        
    Returns:
        Duration in milliseconds, or None if end time is missing
    """
    if not end_nano or end_nano == "" or end_nano == "0":
        return None  # Active span, no duration yet
    
    start = int(start_nano)
    end = int(end_nano)
    
    if end <= start:
        return 0  # Invalid or same timestamp
    
    duration_nanos = end - start
    return int(duration_nanos / 1_000_000)  # Convert to milliseconds


def map_otel_kind_to_string(kind: int) -> str:
    """
    Map OTel span kind enum to string.
    
    Args:
        kind: OTel span kind (0-5)
        
    Returns:
        Human-readable span kind
    """
    mapping = {
        0: "UNSPECIFIED",
        1: "INTERNAL",
        2: "SERVER",
        3: "CLIENT",
        4: "PRODUCER",
        5: "CONSUMER"
    }
    return mapping.get(kind, "UNSPECIFIED")


def map_otel_status_to_string(status_code: int) -> str:
    """
    Map OTel status code to string.
    
    Args:
        status_code: OTel status code (0-2)
        
    Returns:
        Human-readable status
    """
    mapping = {
        0: "UNSET",
        1: "OK",
        2: "ERROR"
    }
    return mapping.get(status_code, "UNSET")


def flatten_otel_spans(
    otel_data: OTelTracesData,
    organization_id: str
) -> List[Dict[str, Any]]:
    """
    Flatten nested OTel structure into flat span records for Supabase.
    
    Important notes:
    - traceId and spanId are kept as hex strings (not converted to UUIDs)
    - execution_id is extracted from attributes["agora.execution_id"] if present
    - Resource attributes are prefixed with "resource." in the attributes dict
    
    Args:
        otel_data: OTel traces data (nested structure)
        organization_id: Organization ID from authenticated API key
        
    Returns:
        List of flat span dicts ready for bulk insert into telemetry_spans table
    """
    flat_spans = []
    
    for resource_span in otel_data.resourceSpans:
        # Extract resource attributes (service name, host, etc.)
        resource_attrs = {}
        if resource_span.resource and resource_span.resource.attributes:
            resource_attrs = flatten_otel_attributes(resource_span.resource.attributes)
        
        for scope_span in resource_span.scopeSpans:
            # Extract scope info (instrumentation library)
            scope_name = None
            scope_version = None
            if scope_span.scope:
                scope_name = scope_span.scope.name
                scope_version = scope_span.scope.version
            
            for span in scope_span.spans:
                # Flatten span attributes
                attributes = flatten_otel_attributes(span.attributes or [])
                
                # Merge resource attributes (prefixed to avoid collisions)
                for key, value in resource_attrs.items():
                    attributes[f"resource.{key}"] = value
                
                # Add scope info
                if scope_name:
                    attributes["otel.scope.name"] = scope_name
                if scope_version:
                    attributes["otel.scope.version"] = scope_version
                
                # Convert timestamps
                start_time = nano_to_iso(span.startTimeUnixNano)
                
                # Handle missing end time (active spans)
                end_time = None
                if span.endTimeUnixNano and span.endTimeUnixNano != "0":
                    end_time = nano_to_iso(span.endTimeUnixNano)
                
                duration_ms = calculate_duration_ms(
                    span.startTimeUnixNano,
                    span.endTimeUnixNano if span.endTimeUnixNano else None
                )
                
                # Map kind and status
                kind = map_otel_kind_to_string(span.kind or 0)
                status = map_otel_status_to_string(
                    span.status.code if span.status else 0
                )
                
                # Add status message if present
                if span.status and span.status.message:
                    attributes["otel.status.message"] = span.status.message
                
                # Flatten events
                events = []
                for event in span.events or []:
                    events.append({
                        "name": event.name,
                        "timestamp": nano_to_iso(event.timeUnixNano),
                        "attributes": flatten_otel_attributes(event.attributes or [])
                    })
                
                # Extract execution_id from attributes if present
                # This allows Agora SDK to link OTel spans to executions
                execution_id = attributes.get("agora.execution_id")
                
                # Create flat span record
                # Note: traceId and spanId are normalized to lowercase hex strings
                flat_span = {
                    "organization_id": organization_id,
                    "trace_id": span.traceId.lower(),  # Normalize to lowercase hex
                    "span_id": span.spanId.lower(),    # Normalize to lowercase hex
                    "parent_span_id": span.parentSpanId.lower() if span.parentSpanId else None,
                    "name": span.name,
                    "kind": kind,
                    "status": status,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration_ms": duration_ms,
                    "attributes": attributes,
                    "events": events,
                    "execution_id": execution_id,  # May be None
                }
                
                flat_spans.append(flat_span)
    
    return flat_spans


def validate_hex_id(hex_id: str, expected_length: int, id_type: str) -> bool:
    """
    Validate that an ID is a valid hex string of expected length.
    
    Args:
        hex_id: The hex string to validate
        expected_length: Expected length (32 for traceId, 16 for spanId)
        id_type: Type of ID for error messages ("trace" or "span")
        
    Returns:
        True if valid
        
    Raises:
        ValueError: If invalid
    """
    if not hex_id:
        raise ValueError(f"{id_type}_id cannot be empty")
    
    if len(hex_id) != expected_length:
        raise ValueError(
            f"{id_type}_id must be {expected_length} characters, got {len(hex_id)}"
        )
    
    try:
        int(hex_id, 16)  # Verify it's valid hex
    except ValueError:
        raise ValueError(f"{id_type}_id must be a valid hexadecimal string")
    
    return True
