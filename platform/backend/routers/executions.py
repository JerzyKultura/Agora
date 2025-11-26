from fastapi import APIRouter, HTTPException, Depends, Query, Header
from typing import List, Optional
from uuid import UUID, uuid4
from database import get_supabase_admin
from supabase import Client
from models import ExecutionResponse, NodeExecutionResponse, TelemetryIngest
from routers.projects import get_current_user

router = APIRouter(prefix="/executions", tags=["Executions"])

# ============================================================================
# API KEY AUTHENTICATION HELPER
# ============================================================================

async def get_org_from_api_key(
    x_api_key: Optional[str] = Header(None),
    supabase: Client = Depends(get_supabase_admin)
) -> str:
    """Authenticate via API key and return organization ID."""
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing X-API-Key header")
    
    # Import here to avoid circular dependency
    from routers.api_keys import authenticate_api_key
    
    auth_data = await authenticate_api_key(x_api_key, supabase)
    return auth_data["organization_id"]


# ============================================================================
# STANDARD ENDPOINTS (JWT Auth)
# ============================================================================

@router.get("/", response_model=List[ExecutionResponse])
async def list_executions(
    workflow_id: Optional[UUID] = None,
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    offset: int = 0,
    user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase_admin)
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
async def get_execution(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase_admin)):
    try:
        response = supabase.table("executions")\
            .select("*")\
            .eq("id", str(execution_id))\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Execution not found")

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{execution_id}/nodes", response_model=List[NodeExecutionResponse])
async def get_execution_nodes(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase_admin)):
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
async def get_execution_timeline(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase_admin)):
    try:
        execution_response = supabase.table("executions")\
            .select("*")\
            .eq("id", str(execution_id))\
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
            "execution": execution_response.data[0],
            "timeline": timeline
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{execution_id}/shared-state")
async def get_shared_state_evolution(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase_admin)):
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
async def get_telemetry_spans(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase_admin)):
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
async def get_telemetry_events(execution_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase_admin)):
    try:
        response = supabase.table("telemetry_events")\
            .select("*")\
            .eq("execution_id", str(execution_id))\
            .order("timestamp")\
            .execute()

        return {"events": response.data}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# TELEMETRY INGESTION WITH AUTO-DISCOVERY (API Key Auth)
# ============================================================================

@router.post("/ingest", response_model=ExecutionResponse)
async def ingest_telemetry(
    telemetry: TelemetryIngest,
    org_id: str = Depends(get_org_from_api_key),
    supabase: Client = Depends(get_supabase_admin)
):
    """
    Ingest telemetry data from Agora framework execution.
    Uses API key authentication and auto-discovers workflows/nodes.
    
    Auto-Discovery:
    1. If workflow_id is a name (not UUID), create workflow automatically
    2. Auto-create nodes if they don't exist
    3. Create execution record with all telemetry
    """
    try:
        # ====================================================================
        # STEP 1: Auto-Discover or Create Workflow
        # ====================================================================
        workflow_id = str(telemetry.workflow_id)
        
        # Check if workflow_id is actually a name (not a valid UUID)
        try:
            UUID(workflow_id)
            # It's a valid UUID, use it as-is
        except ValueError:
            # It's a workflow name, auto-discover/create
            workflow_name = workflow_id
            
            # Check if workflow exists by name
            existing_workflow = supabase.table("workflows")\
                .select("id, project_id")\
                .eq("name", workflow_name)\
                .execute()
            
            if existing_workflow.data:
                # Use existing workflow
                workflow_id = existing_workflow.data[0]["id"]
                project_id = existing_workflow.data[0]["project_id"]
            else:
                # Create new project for this org
                project_response = supabase.table("projects").insert({
                    "organization_id": org_id,
                    "name": f"Auto-Created: {workflow_name}",
                    "description": "Automatically created from telemetry ingestion"
                }).execute()
                
                if not project_response.data:
                    raise HTTPException(status_code=500, detail="Failed to create project")
                
                project_id = project_response.data[0]["id"]
                
                # Create new workflow
                workflow_response = supabase.table("workflows").insert({
                    "project_id": project_id,
                    "name": workflow_name,
                    "description": "Automatically created from telemetry ingestion",
                    "type": "sequential"
                }).execute()
                
                if not workflow_response.data:
                    raise HTTPException(status_code=500, detail="Failed to create workflow")
                
                workflow_id = workflow_response.data[0]["id"]
                
                print(f"✅ Auto-created workflow: {workflow_name} ({workflow_id})")
        
        # ====================================================================
        # STEP 2: Auto-Create Nodes
        # ====================================================================
        node_id_mapping = {}  # node_name -> node_id
        
        for node_exec in telemetry.node_executions:
            node_name = node_exec.node_name
            node_type = node_exec.node_type
            
            # Check if node exists
            existing_node = supabase.table("nodes")\
                .select("id")\
                .eq("workflow_id", workflow_id)\
                .eq("name", node_name)\
                .execute()
            
            if existing_node.data:
                # Use existing node
                node_id_mapping[node_name] = existing_node.data[0]["id"]
            else:
                # Create new node
                node_response = supabase.table("nodes").insert({
                    "workflow_id": workflow_id,
                    "name": node_name,
                    "type": node_type,
                    "code": "# Auto-generated from telemetry\n# Edit this code in the UI",
                    "config": {}
                }).execute()
                
                if node_response.data:
                    node_id_mapping[node_name] = node_response.data[0]["id"]
                    print(f"✅ Auto-created node: {node_name}")
        
        # ====================================================================
        # STEP 3: Create Execution Record
        # ====================================================================
        execution_id = uuid4()
        execution_data = {
            "id": str(execution_id),
            "workflow_id": workflow_id,
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

        # ====================================================================
        # STEP 4: Insert Node Executions
        # ====================================================================
        if telemetry.node_executions:
            node_executions_data = []
            for node_exec in telemetry.node_executions:
                # Use mapped node_id or placeholder
                mapped_node_id = node_id_mapping.get(
                    node_exec.node_name,
                    str(node_exec.node_id)  # Fallback to provided ID
                )
                
                node_exec_data = {
                    "id": str(uuid4()),
                    "execution_id": str(execution_id),
                    "node_id": mapped_node_id,
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

        # ====================================================================
        # STEP 5: Insert Telemetry Spans
        # ====================================================================
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

        # ====================================================================
        # STEP 6: Insert Telemetry Events
        # ====================================================================
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

        # ====================================================================
        # STEP 7: Insert Shared State Snapshots
        # ====================================================================
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

        print(f"✅ Telemetry ingested successfully: {execution_id}")
        
        return execution_response.data[0]

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to ingest telemetry: {str(e)}")
