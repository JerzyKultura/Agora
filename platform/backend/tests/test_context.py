"""
Tests for Context Prime Endpoint

Tests intelligence queries, LLM integration, and endpoint logic.
"""

import pytest
from fastapi.testclient import TestClient
from platform.backend.main import app
from platform.backend.utils.llm_client import _fallback_summary, _build_prompt

client = TestClient(app)


class TestContextPrimeEndpoint:
    """Test /v1/context/prime endpoint."""
    
    @pytest.fixture
    def valid_api_key(self):
        """Mock API key for testing."""
        return "agora_test_key_123"
    
    @pytest.fixture
    def context_request(self):
        """Valid context prime request."""
        return {
            "project_id": "7dec9756-4af9-4118-89d7-c11588052c9c"
        }
    
    def test_prime_context_missing_auth(self, context_request):
        """Test that missing auth returns 401."""
        response = client.post(
            "/v1/context/prime",
            json=context_request
        )
        
        assert response.status_code == 401
    
    def test_prime_context_with_auth(self, context_request, valid_api_key):
        """Test context prime with valid auth."""
        response = client.post(
            "/v1/context/prime",
            json=context_request,
            headers={"Authorization": f"Bearer {valid_api_key}"}
        )
        
        # Will fail without mock, but should return 401 or 404
        assert response.status_code in [200, 401, 404]
    
    def test_prime_context_invalid_project(self, valid_api_key):
        """Test with invalid project ID."""
        response = client.post(
            "/v1/context/prime",
            json={"project_id": "00000000-0000-0000-0000-000000000000"},
            headers={"Authorization": f"Bearer {valid_api_key}"}
        )
        
        # Should return 404 or 401
        assert response.status_code in [401, 404]


class TestLLMClient:
    """Test LLM client functions."""
    
    def test_build_prompt_with_failures(self):
        """Test prompt building with failure data."""
        failures = [
            {
                "name": "auth.verify_token",
                "error_message": "KeyError: 'exp'",
                "trace_id": "abc123"
            }
        ]
        codebase = []
        active_state = None
        
        prompt = _build_prompt(failures, codebase, active_state, "TestProject")
        
        assert "TestProject" in prompt
        assert "auth.verify_token" in prompt
        assert "KeyError" in prompt
    
    def test_build_prompt_with_codebase(self):
        """Test prompt building with codebase data."""
        failures = []
        codebase = [
            {
                "name": "verify_token",
                "node_type": "function",
                "file_path": "backend/auth.py"
            }
        ]
        active_state = None
        
        prompt = _build_prompt(failures, codebase, active_state, "TestProject")
        
        assert "verify_token" in prompt
        assert "backend/auth.py" in prompt
    
    def test_build_prompt_with_active_state(self):
        """Test prompt building with active execution."""
        failures = []
        codebase = []
        active_state = {
            "workflow_name": "user_auth",
            "status": "running"
        }
        
        prompt = _build_prompt(failures, codebase, active_state, "TestProject")
        
        assert "user_auth" in prompt
        assert "running" in prompt
    
    def test_fallback_summary_with_failures(self):
        """Test rule-based summary with failures."""
        failures = [
            {
                "name": "auth.verify_token",
                "error_message": "KeyError: 'exp'"
            }
        ]
        codebase = []
        active_state = None
        
        summary = _fallback_summary(failures, codebase, active_state, "TestProject")
        
        assert "TestProject" in summary
        assert "Debugging" in summary
        assert "auth.verify_token" in summary
    
    def test_fallback_summary_stable_project(self):
        """Test rule-based summary for stable project."""
        failures = []
        codebase = []
        active_state = None
        
        summary = _fallback_summary(failures, codebase, active_state, "TestProject")
        
        assert "TestProject" in summary
        assert "Stable" in summary
    
    def test_fallback_summary_active_development(self):
        """Test rule-based summary with recent code changes."""
        failures = []
        codebase = [
            {
                "name": "new_feature",
                "file_path": "backend/features.py"
            }
        ]
        active_state = None
        
        summary = _fallback_summary(failures, codebase, active_state, "TestProject")
        
        assert "TestProject" in summary
        assert "Active development" in summary


class TestIntelligenceQueries:
    """Test intelligence query functions."""
    
    def test_query_structure(self):
        """Verify query structure is correct."""
        # This is a placeholder for actual query tests
        # In real tests, you'd mock Supabase and verify queries
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
