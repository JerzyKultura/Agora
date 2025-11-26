from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from uuid import UUID
from database import get_supabase
from supabase import Client
from models import ExecutionResponse, NodeExecutionResponse
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
