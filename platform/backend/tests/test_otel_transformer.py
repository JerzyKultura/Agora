"""
Unit Tests for OpenTelemetry Transformer

Tests the span flattening logic, timestamp conversion, and attribute handling.
"""

import pytest
from datetime import datetime, timezone
from platform.backend.utils.otel_transformer import (
    flatten_otel_attributes,
    nano_to_iso,
    calculate_duration_ms,
    map_otel_kind_to_string,
    map_otel_status_to_string,
    flatten_otel_spans,
    validate_hex_id
)
from platform.backend.models.otel import (
    OTelValue,
    OTelKeyValue,
    OTelSpan,
    OTelScopeSpans,
    OTelResourceSpans,
    OTelTracesData,
    OTelResource,
    OTelSpanStatus
)


class TestFlattenAttributes:
    """Test attribute flattening."""
    
    def test_string_value(self):
        attrs = [
            OTelKeyValue(key="http.method", value=OTelValue(stringValue="GET"))
        ]
        result = flatten_otel_attributes(attrs)
        assert result == {"http.method": "GET"}
    
    def test_int_value(self):
        attrs = [
            OTelKeyValue(key="http.status_code", value=OTelValue(intValue=200))
        ]
        result = flatten_otel_attributes(attrs)
        assert result == {"http.status_code": 200}
    
    def test_double_value(self):
        attrs = [
            OTelKeyValue(key="response.time", value=OTelValue(doubleValue=1.23))
        ]
        result = flatten_otel_attributes(attrs)
        assert result == {"response.time": 1.23}
    
    def test_bool_value(self):
        attrs = [
            OTelKeyValue(key="is_error", value=OTelValue(boolValue=True))
        ]
        result = flatten_otel_attributes(attrs)
        assert result == {"is_error": True}
    
    def test_multiple_attributes(self):
        attrs = [
            OTelKeyValue(key="http.method", value=OTelValue(stringValue="GET")),
            OTelKeyValue(key="http.status_code", value=OTelValue(intValue=200)),
            OTelKeyValue(key="is_cached", value=OTelValue(boolValue=False))
        ]
        result = flatten_otel_attributes(attrs)
        assert result == {
            "http.method": "GET",
            "http.status_code": 200,
            "is_cached": False
        }


class TestTimestampConversion:
    """Test nanosecond to ISO conversion."""
    
    def test_nano_to_iso(self):
        # 2024-01-01 00:00:00 UTC
        nano = "1704067200000000000"
        iso = nano_to_iso(nano)
        
        # Parse back to verify
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        assert dt.year == 2024
        assert dt.month == 1
        assert dt.day == 1
        assert dt.hour == 0
        assert dt.minute == 0
        assert dt.second == 0
    
    def test_nano_to_iso_with_microseconds(self):
        # 2024-01-01 00:00:00.123456 UTC
        nano = "1704067200123456000"
        iso = nano_to_iso(nano)
        
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        assert dt.microsecond == 123456


class TestDurationCalculation:
    """Test duration calculation."""
    
    def test_calculate_duration_ms(self):
        start = "1704067200000000000"  # 2024-01-01 00:00:00
        end = "1704067201500000000"    # 2024-01-01 00:00:01.5
        duration = calculate_duration_ms(start, end)
        assert duration == 1500  # 1.5 seconds = 1500ms
    
    def test_calculate_duration_zero(self):
        start = "1704067200000000000"
        end = "1704067200000000000"
        duration = calculate_duration_ms(start, end)
        assert duration == 0


class TestEnumMapping:
    """Test OTel enum to string mapping."""
    
    def test_map_kind(self):
        assert map_otel_kind_to_string(0) == "UNSPECIFIED"
        assert map_otel_kind_to_string(1) == "INTERNAL"
        assert map_otel_kind_to_string(2) == "SERVER"
        assert map_otel_kind_to_string(3) == "CLIENT"
        assert map_otel_kind_to_string(4) == "PRODUCER"
        assert map_otel_kind_to_string(5) == "CONSUMER"
        assert map_otel_kind_to_string(99) == "UNSPECIFIED"  # Unknown
    
    def test_map_status(self):
        assert map_otel_status_to_string(0) == "UNSET"
        assert map_otel_status_to_string(1) == "OK"
        assert map_otel_status_to_string(2) == "ERROR"
        assert map_otel_status_to_string(99) == "UNSET"  # Unknown


class TestHexIdValidation:
    """Test hex ID validation."""
    
    def test_valid_trace_id(self):
        assert validate_hex_id("a" * 32, 32, "trace") is True
    
    def test_valid_span_id(self):
        assert validate_hex_id("b" * 16, 16, "span") is True
    
    def test_invalid_length(self):
        with pytest.raises(ValueError, match="must be 32 characters"):
            validate_hex_id("abc", 32, "trace")
    
    def test_invalid_hex(self):
        with pytest.raises(ValueError, match="must be a valid hexadecimal"):
            validate_hex_id("z" * 32, 32, "trace")
    
    def test_empty_id(self):
        with pytest.raises(ValueError, match="cannot be empty"):
            validate_hex_id("", 32, "trace")


class TestFlattenOtelSpans:
    """Test full span flattening."""
    
    def test_flatten_single_span(self):
        # Create minimal OTel payload
        span = OTelSpan(
            traceId="a" * 32,
            spanId="b" * 16,
            name="test_span",
            startTimeUnixNano="1704067200000000000",
            endTimeUnixNano="1704067201000000000",
            attributes=[
                OTelKeyValue(key="test.key", value=OTelValue(stringValue="test_value"))
            ]
        )
        
        scope_spans = OTelScopeSpans(spans=[span])
        resource_spans = OTelResourceSpans(scopeSpans=[scope_spans])
        traces = OTelTracesData(resourceSpans=[resource_spans])
        
        # Flatten
        org_id = "test-org-123"
        flat_spans = flatten_otel_spans(traces, org_id)
        
        # Verify
        assert len(flat_spans) == 1
        flat = flat_spans[0]
        
        assert flat["organization_id"] == org_id
        assert flat["trace_id"] == "a" * 32
        assert flat["span_id"] == "b" * 16
        assert flat["name"] == "test_span"
        assert flat["kind"] == "UNSPECIFIED"
        assert flat["status"] == "UNSET"
        assert flat["duration_ms"] == 1000
        assert flat["attributes"]["test.key"] == "test_value"
    
    def test_flatten_with_resource_attributes(self):
        # Create span with resource attributes
        resource = OTelResource(
            attributes=[
                OTelKeyValue(key="service.name", value=OTelValue(stringValue="my-service"))
            ]
        )
        
        span = OTelSpan(
            traceId="a" * 32,
            spanId="b" * 16,
            name="test_span",
            startTimeUnixNano="1704067200000000000",
            endTimeUnixNano="1704067201000000000"
        )
        
        scope_spans = OTelScopeSpans(spans=[span])
        resource_spans = OTelResourceSpans(
            resource=resource,
            scopeSpans=[scope_spans]
        )
        traces = OTelTracesData(resourceSpans=[resource_spans])
        
        flat_spans = flatten_otel_spans(traces, "test-org")
        
        # Resource attributes should be prefixed
        assert flat_spans[0]["attributes"]["resource.service.name"] == "my-service"
    
    def test_flatten_with_execution_id(self):
        # Create span with agora.execution_id attribute
        span = OTelSpan(
            traceId="a" * 32,
            spanId="b" * 16,
            name="test_span",
            startTimeUnixNano="1704067200000000000",
            endTimeUnixNano="1704067201000000000",
            attributes=[
                OTelKeyValue(
                    key="agora.execution_id",
                    value=OTelValue(stringValue="exec-123")
                )
            ]
        )
        
        scope_spans = OTelScopeSpans(spans=[span])
        resource_spans = OTelResourceSpans(scopeSpans=[scope_spans])
        traces = OTelTracesData(resourceSpans=[resource_spans])
        
        flat_spans = flatten_otel_spans(traces, "test-org")
        
        # execution_id should be extracted
        assert flat_spans[0]["execution_id"] == "exec-123"
    
    def test_flatten_with_parent_span(self):
        # Create span with parent
        span = OTelSpan(
            traceId="a" * 32,
            spanId="b" * 16,
            parentSpanId="c" * 16,
            name="child_span",
            startTimeUnixNano="1704067200000000000",
            endTimeUnixNano="1704067201000000000"
        )
        
        scope_spans = OTelScopeSpans(spans=[span])
        resource_spans = OTelResourceSpans(scopeSpans=[scope_spans])
        traces = OTelTracesData(resourceSpans=[resource_spans])
        
        flat_spans = flatten_otel_spans(traces, "test-org")
        
        assert flat_spans[0]["parent_span_id"] == "c" * 16
    
    def test_flatten_with_status(self):
        # Create span with error status
        span = OTelSpan(
            traceId="a" * 32,
            spanId="b" * 16,
            name="error_span",
            startTimeUnixNano="1704067200000000000",
            endTimeUnixNano="1704067201000000000",
            status=OTelSpanStatus(code=2, message="Something went wrong")
        )
        
        scope_spans = OTelScopeSpans(spans=[span])
        resource_spans = OTelResourceSpans(scopeSpans=[scope_spans])
        traces = OTelTracesData(resourceSpans=[resource_spans])
        
        flat_spans = flatten_otel_spans(traces, "test-org")
        
        assert flat_spans[0]["status"] == "ERROR"
        assert flat_spans[0]["attributes"]["otel.status.message"] == "Something went wrong"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
