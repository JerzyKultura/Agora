"""
OpenTelemetry Data Models

Pydantic models for OpenTelemetry JSON format.
Compatible with Traceloop/OpenLLMetry exporters.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union


class OTelValue(BaseModel):
    """
    OTel attribute value (can be string, int, bool, double, bytes, array, or kvlist).
    
    Note: Some SDKs send ints as strings, so intValue accepts Union[int, str].
    arrayValue and kvlistValue use flexible Dict[str, Any] for nested structures.
    
    Only one field should be set per value.
    """
    stringValue: Optional[str] = None
    intValue: Optional[Union[int, str]] = None  # Some SDKs send ints as strings
    doubleValue: Optional[float] = None
    boolValue: Optional[bool] = None
    bytesValue: Optional[str] = None  # Base64-encoded bytes
    arrayValue: Optional[Dict[str, Any]] = None  # Flexible for nested arrays
    kvlistValue: Optional[Dict[str, Any]] = None  # Flexible for nested key-value lists


class OTelKeyValue(BaseModel):
    """OTel key-value pair for attributes."""
    key: str
    value: OTelValue


class OTelSpanEvent(BaseModel):
    """OTel span event (e.g., exceptions, logs)."""
    timeUnixNano: str
    name: str
    attributes: Optional[List[OTelKeyValue]] = []
    droppedAttributesCount: Optional[int] = 0


class OTelSpanLink(BaseModel):
    """OTel span link (connects spans across traces)."""
    traceId: str
    spanId: str
    traceState: Optional[str] = ""
    attributes: Optional[List[OTelKeyValue]] = []
    droppedAttributesCount: Optional[int] = 0


class OTelSpanStatus(BaseModel):
    """
    OTel span status.
    
    Code values:
    - 0: UNSET (default)
    - 1: OK
    - 2: ERROR
    """
    message: Optional[str] = ""
    code: Optional[int] = 0


class OTelSpan(BaseModel):
    """
    Individual OTel span.
    
    Note: traceId and spanId are hex strings (not UUIDs).
    - traceId: 32-character hex (128-bit)
    - spanId: 16-character hex (64-bit)
    """
    traceId: str
    spanId: str
    traceState: Optional[str] = ""
    parentSpanId: Optional[str] = ""
    name: str
    kind: Optional[int] = 0  # 0=Unspecified, 1=Internal, 2=Server, 3=Client, 4=Producer, 5=Consumer
    startTimeUnixNano: str
    endTimeUnixNano: str
    attributes: Optional[List[OTelKeyValue]] = []
    droppedAttributesCount: Optional[int] = 0
    events: Optional[List[OTelSpanEvent]] = []
    droppedEventsCount: Optional[int] = 0
    links: Optional[List[OTelSpanLink]] = []
    droppedLinksCount: Optional[int] = 0
    status: Optional[OTelSpanStatus] = None


class OTelInstrumentationScope(BaseModel):
    """Instrumentation scope (library/SDK info)."""
    name: str
    version: Optional[str] = ""
    attributes: Optional[List[OTelKeyValue]] = []
    droppedAttributesCount: Optional[int] = 0


class OTelScopeSpans(BaseModel):
    """Scope-level spans container."""
    scope: Optional[OTelInstrumentationScope] = None
    spans: List[OTelSpan]
    schemaUrl: Optional[str] = ""


class OTelResource(BaseModel):
    """Resource attributes (service name, host, etc.)."""
    attributes: Optional[List[OTelKeyValue]] = []
    droppedAttributesCount: Optional[int] = 0


class OTelResourceSpans(BaseModel):
    """Top-level resource spans container."""
    resource: Optional[OTelResource] = None
    scopeSpans: List[OTelScopeSpans]
    schemaUrl: Optional[str] = ""


class OTelTracesData(BaseModel):
    """
    Root OTel traces payload.
    
    This is the top-level structure sent by OTel exporters.
    """
    resourceSpans: List[OTelResourceSpans]
