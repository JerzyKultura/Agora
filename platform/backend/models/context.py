"""
Context Prime Data Models

Pydantic models for the Context Prime endpoint.
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime


class ContextPrimeRequest(BaseModel):
    """Request to generate context summary for a project."""
    project_id: UUID
    organization_id: Optional[UUID] = None  # Extracted from auth if not provided


class RecentFailure(BaseModel):
    """Recent error from telemetry spans."""
    model_config = {"extra": "allow"}  # Allow extra fields for forward compatibility
    
    name: str
    error_message: Optional[str] = None
    trace_id: str
    timestamp: datetime
    attributes: Optional[Dict[str, Any]] = {}


class CodebaseNode(BaseModel):
    """Recently updated function or class from codebase."""
    model_config = {"extra": "allow"}  # Allow extra fields for forward compatibility
    
    name: str
    node_type: str
    signature: Optional[str] = None
    file_path: str
    updated_at: datetime


class ActiveState(BaseModel):
    """Current execution state."""
    model_config = {"extra": "allow"}  # Allow extra fields for forward compatibility
    
    execution_id: Optional[UUID] = None
    status: Optional[str] = None
    workflow_name: Optional[str] = None
    snapshot_data: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None


class ContextMetadata(BaseModel):
    """Metadata about fetched intelligence."""
    recent_failures: List[RecentFailure] = []
    codebase_snapshot: List[CodebaseNode] = []
    active_state: Optional[ActiveState] = None


class ContextPrimeResponse(BaseModel):
    """Response from context prime endpoint."""
    project_id: UUID
    organization_id: UUID
    context_summary: str
    metadata: ContextMetadata
    generated_at: datetime
    llm_provider: Optional[str] = None  # "gemini", "openai", or "fallback"
