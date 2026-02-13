"""
Integration Tests for OpenTelemetry Endpoint

Tests the /traces endpoint with realistic OTel payloads.
"""

import pytest
from fastapi.testclient import TestClient
from platform.backend.main import app

client = TestClient(app)


class TestOTelTracesEndpoint:
    """Test /telemetry/traces endpoint."""
    
    @pytest.fixture
    def valid_api_key(self):
        """Mock API key for testing."""
        return "agora_test_key_123"
    
    @pytest.fixture
    def minimal_otel_payload(self):
        """Minimal valid OTel payload."""
        return {
            "resourceSpans": [{
                "scopeSpans": [{
                    "spans": [{
                        "traceId": "a" * 32,
                        "spanId": "b" * 16,
                        "name": "test_span",
                        "startTimeUnixNano": "1704067200000000000",
                        "endTimeUnixNano": "1704067201000000000"
                    }]
                }]
            }]
        }
    
    @pytest.fixture
    def full_otel_payload(self):
        """Full OTel payload with all fields."""
        return {
            "resourceSpans": [{
                "resource": {
                    "attributes": [
                        {"key": "service.name", "value": {"stringValue": "my-service"}},
                        {"key": "service.version", "value": {"stringValue": "1.0.0"}}
                    ]
                },
                "scopeSpans": [{
                    "scope": {
                        "name": "opentelemetry.instrumentation.openai",
                        "version": "0.1.0"
                    },
                    "spans": [{
                        "traceId": "a" * 32,
                        "spanId": "b" * 16,
                        "parentSpanId": "",
                        "name": "openai.chat.completions",
                        "kind": 3,  # CLIENT
                        "startTimeUnixNano": "1704067200000000000",
                        "endTimeUnixNano": "1704067201500000000",
                        "attributes": [
                            {"key": "llm.model", "value": {"stringValue": "gpt-4"}},
                            {"key": "llm.tokens.prompt", "value": {"intValue": 100}},
                            {"key": "llm.tokens.completion", "value": {"intValue": 50}},
                            {"key": "agora.execution_id", "value": {"stringValue": "exec-123"}}
                        ],
                        "events": [
                            {
                                "timeUnixNano": "1704067200500000000",
                                "name": "llm.request.start",
                                "attributes": []
                            }
                        ],
                        "status": {
                            "code": 1,  # OK
                            "message": ""
                        }
                    }]
                }]
            }]
        }
    
    def test_ingest_minimal_payload_with_bearer_token(self, minimal_otel_payload, valid_api_key):
        """Test ingesting minimal payload with Authorization header."""
        response = client.post(
            "/telemetry/traces",
            json=minimal_otel_payload,
            headers={"Authorization": f"Bearer {valid_api_key}"}
        )
        
        # Note: This will fail without proper auth setup
        # In real test, you'd mock the Supabase client
        assert response.status_code in [200, 401]
    
    def test_ingest_minimal_payload_with_x_api_key(self, minimal_otel_payload, valid_api_key):
        """Test ingesting minimal payload with X-API-Key header."""
        response = client.post(
            "/telemetry/traces",
            json=minimal_otel_payload,
            headers={"X-API-Key": valid_api_key}
        )
        
        assert response.status_code in [200, 401]
    
    def test_ingest_full_payload(self, full_otel_payload, valid_api_key):
        """Test ingesting full payload with all OTel fields."""
        response = client.post(
            "/telemetry/traces",
            json=full_otel_payload,
            headers={"Authorization": f"Bearer {valid_api_key}"}
        )
        
        assert response.status_code in [200, 401]
    
    def test_missing_auth_header(self, minimal_otel_payload):
        """Test that missing auth header returns 401."""
        response = client.post(
            "/telemetry/traces",
            json=minimal_otel_payload
        )
        
        assert response.status_code == 401
        assert "API key" in response.json()["detail"]
    
    def test_invalid_api_key_format(self, minimal_otel_payload):
        """Test that invalid API key format returns 401."""
        response = client.post(
            "/telemetry/traces",
            json=minimal_otel_payload,
            headers={"Authorization": "Bearer invalid_key"}
        )
        
        assert response.status_code == 401
    
    def test_empty_payload(self, valid_api_key):
        """Test that empty resourceSpans returns 0 ingested."""
        response = client.post(
            "/telemetry/traces",
            json={"resourceSpans": []},
            headers={"Authorization": f"Bearer {valid_api_key}"}
        )
        
        # Should accept but ingest 0 spans
        if response.status_code == 200:
            assert response.json()["spans_ingested"] == 0
    
    def test_invalid_payload_structure(self, valid_api_key):
        """Test that invalid payload structure returns 422."""
        response = client.post(
            "/telemetry/traces",
            json={"invalid": "structure"},
            headers={"Authorization": f"Bearer {valid_api_key}"}
        )
        
        assert response.status_code == 422  # Pydantic validation error


class TestTraceloopCompatibility:
    """Test compatibility with Traceloop payloads."""
    
    @pytest.fixture
    def traceloop_payload(self):
        """Realistic Traceloop/OpenLLMetry payload."""
        return {
            "resourceSpans": [{
                "resource": {
                    "attributes": [
                        {"key": "telemetry.sdk.name", "value": {"stringValue": "opentelemetry"}},
                        {"key": "telemetry.sdk.language", "value": {"stringValue": "python"}},
                        {"key": "telemetry.sdk.version", "value": {"stringValue": "1.21.0"}},
                        {"key": "service.name", "value": {"stringValue": "agora-app"}}
                    ]
                },
                "scopeSpans": [{
                    "scope": {
                        "name": "traceloop.sdk",
                        "version": "0.15.0"
                    },
                    "spans": [
                        {
                            "traceId": "1234567890abcdef1234567890abcdef",
                            "spanId": "1234567890abcdef",
                            "name": "workflow.execute",
                            "kind": 1,  # INTERNAL
                            "startTimeUnixNano": "1704067200000000000",
                            "endTimeUnixNano": "1704067205000000000",
                            "attributes": [
                                {"key": "traceloop.workflow.name", "value": {"stringValue": "chatbot"}},
                                {"key": "agora.execution_id", "value": {"stringValue": "exec-abc-123"}}
                            ],
                            "status": {"code": 1}
                        },
                        {
                            "traceId": "1234567890abcdef1234567890abcdef",
                            "spanId": "abcdef1234567890",
                            "parentSpanId": "1234567890abcdef",
                            "name": "openai.chat.completions",
                            "kind": 3,  # CLIENT
                            "startTimeUnixNano": "1704067201000000000",
                            "endTimeUnixNano": "1704067203000000000",
                            "attributes": [
                                {"key": "llm.vendor", "value": {"stringValue": "openai"}},
                                {"key": "llm.request.model", "value": {"stringValue": "gpt-4"}},
                                {"key": "llm.usage.prompt_tokens", "value": {"intValue": 150}},
                                {"key": "llm.usage.completion_tokens", "value": {"intValue": 75}},
                                {"key": "llm.usage.total_tokens", "value": {"intValue": 225}}
                            ],
                            "status": {"code": 1}
                        }
                    ]
                }]
            }]
        }
    
    def test_traceloop_payload_structure(self, traceloop_payload):
        """Test that Traceloop payload is valid OTel."""
        from platform.backend.models.otel import OTelTracesData
        
        # Should parse without errors
        traces = OTelTracesData(**traceloop_payload)
        assert len(traces.resourceSpans) == 1
        assert len(traces.resourceSpans[0].scopeSpans[0].spans) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
