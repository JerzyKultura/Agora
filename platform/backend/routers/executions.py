from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID, uuid4
from database import get_supabase
from supabase import Client
from models import ExecutionResponse, NodeExecutionResponse, TelemetryIngest
from routers.projects import get_current_user

router = APIRouter(prefix="/executions", tags=["Executions"])

@router.get("/", response_model=List[ExecutionResponse])
async def list_executions(
    workflow_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    try:
        query = supabase.table("executions").select("*")

        if workflow_id:
            query = query.eq("workflow_id", str(workflow_id))
        if status:
            query = query.eq("status", status)

        response = query.order("started_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{execution_id}", response_model=ExecutionResponse)
async def get_execution(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("executions")\
            .select("*")\
            .eq("id", str(execution_id))\
            .maybeSingle()\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Execution not found")

        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{execution_id}/nodes", response_model=List[NodeExecutionResponse])
async def get_execution_nodes(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("node_executions")\
            .select("*")\
            .eq("execution_id", str(execution_id))\
            .order("started_at")\
            .execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{execution_id}/timeline")
async def get_execution_timeline(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        execution_response = supabase.table("executions")\
            .select("*")\
            .eq("id", str(execution_id))\
            .maybeSingle()\
            .execute()

        if not execution_response.data:
            raise HTTPException(status_code=404, detail="Execution not found")

        nodes_response = supabase.table("node_executions")\
            .select("*, nodes(name, type)")\
            .eq("execution_id", str(execution_id))\
            .order("started_at")\
            .execute()

        timeline = []
        for node_exec in nodes_response.data:
            timeline.append({
                "id": node_exec["id"],
                "node_id": node_exec["node_id"],
                "node_name": node_exec["nodes"]["name"] if node_exec.get("nodes") else "Unknown",
                "node_type": node_exec["nodes"]["type"] if node_exec.get("nodes") else "Unknown",
                "status": node_exec["status"],
                "started_at": node_exec["started_at"],
                "completed_at": node_exec["completed_at"],
                "prep_duration_ms": node_exec["prep_duration_ms"],
                "exec_duration_ms": node_exec["exec_duration_ms"],
                "post_duration_ms": node_exec["post_duration_ms"],
                "retry_count": node_exec["retry_count"],
                "error_message": node_exec["error_message"]
            })

        return {
            "execution": execution_response.data,
            "timeline": timeline
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{execution_id}/shared-state")
async def get_shared_state_evolution(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("shared_state_snapshots")\
            .select("*")\
            .eq("execution_id", str(execution_id))\
            .order("sequence")\
            .execute()

        return {"snapshots": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{execution_id}/telemetry-spans")
async def get_telemetry_spans(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("telemetry_spans")\
            .select("*")\
            .eq("execution_id", str(execution_id))\
            .order("start_time")\
            .execute()

        return {"spans": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{execution_id}/telemetry-events")
async def get_telemetry_events(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("telemetry_events")\
            .select("*")\
            .eq("execution_id", str(execution_id))\
            .order("timestamp")\
            .execute()

        return {"events": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/ingest", response_model=ExecutionResponse)
async def ingest_telemetry(
    telemetry: TelemetryIngest,
    user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Ingest telemetry data from Agora framework execution.
    Creates execution record with all associated node executions, spans, events, and state snapshots.
    """
    try:
        # Create execution record
        execution_id = uuid4()
        execution_data = {
            "id": str(execution_id),
            "workflow_id": str(telemetry.workflow_id),
            "status": telemetry.status,
            "started_at": telemetry.started_at.isoformat(),
            "completed_at": telemetry.completed_at.isoformat() if telemetry.completed_at else None,
            "duration_ms": telemetry.duration_ms,
            "error_message": telemetry.error_message,
            "input_data": telemetry.input_data,
            "output_data": telemetry.output_data
        }

        execution_response = supabase.table("executions").insert(execution_data).execute()

        if not execution_response.data:
            raise HTTPException(status_code=500, detail="Failed to create execution record")

        # Insert node executions
        if telemetry.node_executions:
            node_executions_data = []
            for node_exec in telemetry.node_executions:
                node_exec_data = {
                    "id": str(uuid4()),
                    "execution_id": str(execution_id),
                    "node_id": str(node_exec.node_id),
                    "status": node_exec.status,
                    "started_at": node_exec.started_at.isoformat(),
                    "completed_at": node_exec.completed_at.isoformat() if node_exec.completed_at else None,
                    "prep_duration_ms": node_exec.prep_duration_ms,
                    "exec_duration_ms": node_exec.exec_duration_ms,
                    "post_duration_ms": node_exec.post_duration_ms,
                    "prep_result": node_exec.prep_result,
                    "exec_result": node_exec.exec_result,
                    "post_result": node_exec.post_result,
                    "error_message": node_exec.error_message,
                    "retry_count": node_exec.retry_count
                }
                node_executions_data.append(node_exec_data)

            if node_executions_data:
                supabase.table("node_executions").insert(node_executions_data).execute()

        # Insert telemetry spans
        if telemetry.telemetry_spans:
            spans_data = []
            for span in telemetry.telemetry_spans:
                span_data = {
                    "id": str(uuid4()),
                    "execution_id": str(execution_id),
                    "span_id": span.span_id,
                    "trace_id": span.trace_id,
                    "parent_span_id": span.parent_span_id,
                    "name": span.name,
                    "kind": span.kind,
                    "status": span.status,
                    "start_time": span.start_time.isoformat(),
                    "end_time": span.end_time.isoformat() if span.end_time else None,
                    "duration_ms": span.duration_ms,
                    "attributes": span.attributes,
                    "events": span.events
                }
                spans_data.append(span_data)

            if spans_data:
                supabase.table("telemetry_spans").insert(spans_data).execute()

        # Insert telemetry events
        if telemetry.telemetry_events:
            events_data = []
            for event in telemetry.telemetry_events:
                event_data = {
                    "id": str(uuid4()),
                    "execution_id": str(execution_id),
                    "event_type": event.event_type,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data
                }
                events_data.append(event_data)

            if events_data:
                supabase.table("telemetry_events").insert(events_data).execute()

        # Insert shared state snapshots
        if telemetry.shared_state_snapshots:
            snapshots_data = []
            for snapshot in telemetry.shared_state_snapshots:
                snapshot_data = {
                    "id": str(uuid4()),
                    "execution_id": str(execution_id),
                    "sequence": snapshot.sequence,
                    "state_json": snapshot.state_json
                }
                snapshots_data.append(snapshot_data)

            if snapshots_data:
                supabase.table("shared_state_snapshots").insert(snapshots_data).execute()

        return execution_response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to ingest telemetry: {str(e)}")
