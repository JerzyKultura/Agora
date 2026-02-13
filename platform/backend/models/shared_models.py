from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID

class OrganizationCreate(BaseModel):
    name: str

class OrganizationResponse(BaseModel):
    id: UUID
    name: str
    created_at: datetime
    updated_at: datetime

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: UUID
    email: str
    created_at: datetime

class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None

class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime

class WorkflowCreate(BaseModel):
    name: str
    description: Optional[str] = None
    type: str = "sequential"
    config: Optional[Dict[str, Any]] = {}

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    type: Optional[str] = None
    config: Optional[Dict[str, Any]] = None

class WorkflowResponse(BaseModel):
    id: UUID
    project_id: UUID
    name: str
    description: Optional[str]
    type: str
    config: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

class NodeCreate(BaseModel):
    name: str
    type: str
    code: Optional[str] = None
    config: Optional[Dict[str, Any]] = {}
    position_x: Optional[int] = 0
    position_y: Optional[int] = 0

class NodeUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    code: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None

class NodeResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    name: str
    type: str
    code: Optional[str]
    config: Dict[str, Any]
    position_x: int
    position_y: int
    created_at: datetime
    updated_at: datetime

class EdgeCreate(BaseModel):
    from_node_id: UUID
    to_node_id: UUID
    action: str

class EdgeResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    from_node_id: UUID
    to_node_id: UUID
    action: str
    created_at: datetime

class ExecutionCreate(BaseModel):
    workflow_id: UUID
    input_data: Optional[Dict[str, Any]] = None

class ExecutionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    error_message: Optional[str]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]

class NodeExecutionResponse(BaseModel):
    id: UUID
    execution_id: UUID
    node_id: UUID
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    prep_duration_ms: Optional[int]
    exec_duration_ms: Optional[int]
    post_duration_ms: Optional[int]
    prep_result: Optional[Dict[str, Any]]
    exec_result: Optional[Dict[str, Any]]
    post_result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int

class APIKeyCreate(BaseModel):
    name: str
    expires_at: Optional[datetime] = None

class APIKeyResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    key_prefix: str
    created_at: datetime
    expires_at: Optional[datetime]
    last_used_at: Optional[datetime]
    revoked_at: Optional[datetime]
