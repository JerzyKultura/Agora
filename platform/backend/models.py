from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any, Union
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

# Telemetry Ingestion Models
class NodeExecutionIngest(BaseModel):
    node_id: UUID
    node_name: str
    node_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    prep_duration_ms: Optional[int] = None
    exec_duration_ms: Optional[int] = None
    post_duration_ms: Optional[int] = None
    prep_result: Optional[Dict[str, Any]] = None
    exec_result: Optional[Dict[str, Any]] = None
    post_result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0

class TelemetrySpanIngest(BaseModel):
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    name: str
    kind: Optional[str] = None
    status: Optional[str] = None
    start_time: datetime
    end_time: Optional[datetime] = None
    duration_ms: Optional[int] = None
    attributes: Optional[Dict[str, Any]] = {}
    events: Optional[List[Dict[str, Any]]] = []

class TelemetryEventIngest(BaseModel):
    event_type: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = {}

class SharedStateSnapshotIngest(BaseModel):
    sequence: int
    state_json: Dict[str, Any]
    node_name: Optional[str] = None

class TelemetryIngest(BaseModel):
    workflow_id: Union[UUID, str]  # Accept UUID or workflow name
    session_id: str
    status: str = "running"
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    node_executions: List[NodeExecutionIngest] = []
    telemetry_spans: List[TelemetrySpanIngest] = []
    telemetry_events: List[TelemetryEventIngest] = []
    shared_state_snapshots: List[SharedStateSnapshotIngest] = []
