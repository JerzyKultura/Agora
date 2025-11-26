from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from database import get_supabase
from supabase import Client
from pydantic import BaseModel
import hashlib

router = APIRouter(prefix="/telemetry", tags=["Telemetry"])

class TelemetryBatch(BaseModel):
    execution_id: Optional[UUID] = None
    workflow_name: Optional[str] = None
    project_name: Optional[str] = None
    events: List[Dict[str, Any]]
    spans: Optional[List[Dict[str, Any]]] = []
    node_executions: Optional[List[Dict[str, Any]]] = []
    shared_state_snapshots: Optional[List[Dict[str, Any]]] = []

class ExecutionStart(BaseModel):
    workflow_name: str
    project_name: Optional[str] = None
    input_data: Optional[Dict[str, Any]] = None

class ExecutionComplete(BaseModel):
    status: str
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class NodeExecutionData(BaseModel):
    node_name: str
    node_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    prep_duration_ms: Optional[int] = None
    exec_duration_ms: Optional[int] = None
    post_duration_ms: Optional[int] = None
    error_message: Optional[str] = None
    retry_count: int = 0

class TelemetrySpan(BaseModel):
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

class TelemetryEvent(BaseModel):
    event_type: str
    timestamp: datetime
    data: Optional[Dict[str, Any]] = {}

async def verify_api_key(x_api_key: str = Header(...), supabase: Client = Depends(get_supabase)) -> Dict[str, Any]:
    if not x_api_key or not x_api_key.startswith("agora_"):
        raise HTTPException(status_code=401, detail="Invalid API key format")

    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()

    response = supabase.table("api_keys")\
        .select("*, organizations!inner(id, name)")\
        .eq("key_hash", key_hash)\
        .is_("revoked_at", "null")\
        .maybeSingle()\
        .execute()

    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")

    api_key_data = response.data

    if api_key_data.get("expires_at"):
        from datetime import datetime
        expires_at = datetime.fromisoformat(api_key_data["expires_at"].replace("Z", "+00:00"))
        if expires_at < datetime.now(expires_at.tzinfo):
            raise HTTPException(status_code=401, detail="API key expired")

    supabase.table("api_keys")\
        .update({"last_used_at": datetime.utcnow().isoformat()})\
        .eq("id", str(api_key_data["id"]))\
        .execute()

    return {
        "organization_id": api_key_data["organization_id"],
        "organization_name": api_key_data["organizations"]["name"]
    }

@router.post("/executions/start")
async def start_execution(
    data: ExecutionStart,
    auth: Dict[str, Any] = Depends(verify_api_key),
    supabase: Client = Depends(get_supabase)
):
    try:
        org_id = auth["organization_id"]

        project = None
        if data.project_name:
            proj_response = supabase.table("projects")\
                .select("id")\
                .eq("organization_id", str(org_id))\
                .eq("name", data.project_name)\
                .maybeSingle()\
                .execute()
            project = proj_response.data

        if not project:
            new_proj = supabase.table("projects").insert({
                "organization_id": str(org_id),
                "name": data.project_name or "Default Project",
                "description": "Auto-created from telemetry"
            }).execute()
            project = new_proj.data[0]

        workflow_response = supabase.table("workflows")\
            .select("id")\
            .eq("project_id", str(project["id"]))\
            .eq("name", data.workflow_name)\
            .maybeSingle()\
            .execute()
        workflow = workflow_response.data

        if not workflow:
            new_workflow = supabase.table("workflows").insert({
                "project_id": str(project["id"]),
                "name": data.workflow_name,
                "type": "sequential",
                "config": {}
            }).execute()
            workflow = new_workflow.data[0]

        execution = supabase.table("executions").insert({
            "workflow_id": str(workflow["id"]),
            "status": "running",
            "input_data": data.input_data or {}
        }).execute()

        return {
            "execution_id": execution.data[0]["id"],
            "workflow_id": workflow["id"],
            "project_id": project["id"]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/executions/{execution_id}/complete")
async def complete_execution(
    execution_id: UUID,
    data: ExecutionComplete,
    auth: Dict[str, Any] = Depends(verify_api_key),
    supabase: Client = Depends(get_supabase)
):
    try:
        exec_response = supabase.table("executions")\
            .select("*, workflows!inner(projects!inner(organization_id))")\
            .eq("id", str(execution_id))\
            .maybeSingle()\
            .execute()

        if not exec_response.data:
            raise HTTPException(status_code=404, detail="Execution not found")

        execution = exec_response.data
        if str(execution["workflows"]["projects"]["organization_id"]) != str(auth["organization_id"]):
            raise HTTPException(status_code=403, detail="Access denied")

        started_at = datetime.fromisoformat(execution["started_at"].replace("Z", "+00:00"))
        completed_at = datetime.utcnow()
        duration_ms = int((completed_at - started_at.replace(tzinfo=None)).total_seconds() * 1000)

        supabase.table("executions").update({
            "status": data.status,
            "completed_at": completed_at.isoformat(),
            "duration_ms": duration_ms,
            "output_data": data.output_data,
            "error_message": data.error_message
        }).eq("id", str(execution_id)).execute()

        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/executions/{execution_id}/nodes")
async def add_node_execution(
    execution_id: UUID,
    data: NodeExecutionData,
    auth: Dict[str, Any] = Depends(verify_api_key),
    supabase: Client = Depends(get_supabase)
):
    try:
        exec_response = supabase.table("executions")\
            .select("workflows!inner(id, project_id, projects!inner(organization_id))")\
            .eq("id", str(execution_id))\
            .maybeSingle()\
            .execute()

        if not exec_response.data:
            raise HTTPException(status_code=404, detail="Execution not found")

        execution = exec_response.data
        if str(execution["workflows"]["projects"]["organization_id"]) != str(auth["organization_id"]):
            raise HTTPException(status_code=403, detail="Access denied")

        workflow_id = execution["workflows"]["id"]

        node_response = supabase.table("nodes")\
            .select("id")\
            .eq("workflow_id", str(workflow_id))\
            .eq("name", data.node_name)\
            .maybeSingle()\
            .execute()
        node = node_response.data

        if not node:
            new_node = supabase.table("nodes").insert({
                "workflow_id": str(workflow_id),
                "name": data.node_name,
                "type": data.node_type,
                "config": {}
            }).execute()
            node = new_node.data[0]

        node_exec = supabase.table("node_executions").insert({
            "execution_id": str(execution_id),
            "node_id": str(node["id"]),
            "status": data.status,
            "started_at": data.started_at.isoformat(),
            "completed_at": data.completed_at.isoformat() if data.completed_at else None,
            "prep_duration_ms": data.prep_duration_ms,
            "exec_duration_ms": data.exec_duration_ms,
            "post_duration_ms": data.post_duration_ms,
            "error_message": data.error_message,
            "retry_count": data.retry_count
        }).execute()

        return {"node_execution_id": node_exec.data[0]["id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/executions/{execution_id}/spans")
async def add_telemetry_span(
    execution_id: UUID,
    data: TelemetrySpan,
    auth: Dict[str, Any] = Depends(verify_api_key),
    supabase: Client = Depends(get_supabase)
):
    try:
        exec_response = supabase.table("executions")\
            .select("workflows!inner(projects!inner(organization_id))")\
            .eq("id", str(execution_id))\
            .maybeSingle()\
            .execute()

        if not exec_response.data:
            raise HTTPException(status_code=404, detail="Execution not found")

        execution = exec_response.data
        if str(execution["workflows"]["projects"]["organization_id"]) != str(auth["organization_id"]):
            raise HTTPException(status_code=403, detail="Access denied")

        span = supabase.table("telemetry_spans").insert({
            "execution_id": str(execution_id),
            "span_id": data.span_id,
            "trace_id": data.trace_id,
            "parent_span_id": data.parent_span_id,
            "name": data.name,
            "kind": data.kind,
            "status": data.status,
            "start_time": data.start_time.isoformat(),
            "end_time": data.end_time.isoformat() if data.end_time else None,
            "duration_ms": data.duration_ms,
            "attributes": data.attributes or {},
            "events": data.events or []
        }).execute()

        return {"span_id": span.data[0]["id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/executions/{execution_id}/events")
async def add_telemetry_event(
    execution_id: UUID,
    data: TelemetryEvent,
    auth: Dict[str, Any] = Depends(verify_api_key),
    supabase: Client = Depends(get_supabase)
):
    try:
        exec_response = supabase.table("executions")\
            .select("workflows!inner(projects!inner(organization_id))")\
            .eq("id", str(execution_id))\
            .maybeSingle()\
            .execute()

        if not exec_response.data:
            raise HTTPException(status_code=404, detail="Execution not found")

        execution = exec_response.data
        if str(execution["workflows"]["projects"]["organization_id"]) != str(auth["organization_id"]):
            raise HTTPException(status_code=403, detail="Access denied")

        event = supabase.table("telemetry_events").insert({
            "execution_id": str(execution_id),
            "event_type": data.event_type,
            "timestamp": data.timestamp.isoformat(),
            "data": data.data or {}
        }).execute()

        return {"event_id": event.data[0]["id"]}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/batch")
async def batch_ingest(
    batch: TelemetryBatch,
    auth: Dict[str, Any] = Depends(verify_api_key),
    supabase: Client = Depends(get_supabase)
):
    try:
        execution_id = batch.execution_id

        if not execution_id and batch.workflow_name:
            start_data = ExecutionStart(
                workflow_name=batch.workflow_name,
                project_name=batch.project_name
            )
            result = await start_execution(start_data, auth, supabase)
            execution_id = result["execution_id"]

        if not execution_id:
            raise HTTPException(status_code=400, detail="execution_id or workflow_name required")

        results = {
            "execution_id": str(execution_id),
            "events_ingested": 0,
            "spans_ingested": 0,
            "node_executions_ingested": 0
        }

        for node_exec in batch.node_executions or []:
            try:
                node_data = NodeExecutionData(**node_exec)
                await add_node_execution(execution_id, node_data, auth, supabase)
                results["node_executions_ingested"] += 1
            except Exception:
                pass

        for span in batch.spans or []:
            try:
                span_data = TelemetrySpan(**span)
                await add_telemetry_span(execution_id, span_data, auth, supabase)
                results["spans_ingested"] += 1
            except Exception:
                pass

        for event in batch.events:
            try:
                event_data = TelemetryEvent(**event)
                await add_telemetry_event(execution_id, event_data, auth, supabase)
                results["events_ingested"] += 1
            except Exception:
                pass

        return results
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
