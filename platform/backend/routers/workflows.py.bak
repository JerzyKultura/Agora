from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from uuid import UUID
from database import get_supabase
from supabase import Client
from models import (
    WorkflowResponse, WorkflowUpdate,
    NodeCreate, NodeUpdate, NodeResponse,
    EdgeCreate, EdgeResponse
)
from routers.projects import get_current_user

router = APIRouter(prefix="/workflows", tags=["Workflows"])

@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("workflows")\
            .select("*")\
            .eq("id", str(workflow_id))\
            .maybeSingle()\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{workflow_id}", response_model=WorkflowResponse)
async def update_workflow(workflow_id: UUID, workflow: WorkflowUpdate, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        update_data = {k: v for k, v in workflow.dict(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = "now()"

        response = supabase.table("workflows")\
            .update(update_data)\
            .eq("id", str(workflow_id))\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("workflows")\
            .delete()\
            .eq("id", str(workflow_id))\
            .execute()

        return {"message": "Workflow deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{workflow_id}/nodes", response_model=NodeResponse)
async def create_node(workflow_id: UUID, node: NodeCreate, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("nodes").insert({
            "workflow_id": str(workflow_id),
            "name": node.name,
            "type": node.type,
            "code": node.code,
            "config": node.config,
            "position_x": node.position_x,
            "position_y": node.position_y
        }).execute()

        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{workflow_id}/nodes", response_model=List[NodeResponse])
async def list_nodes(workflow_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("nodes")\
            .select("*")\
            .eq("workflow_id", str(workflow_id))\
            .execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{workflow_id}/nodes/{node_id}", response_model=NodeResponse)
async def get_node(workflow_id: UUID, node_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("nodes")\
            .select("*")\
            .eq("id", str(node_id))\
            .eq("workflow_id", str(workflow_id))\
            .maybeSingle()\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Node not found")

        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{workflow_id}/nodes/{node_id}", response_model=NodeResponse)
async def update_node(workflow_id: UUID, node_id: UUID, node: NodeUpdate, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        update_data = {k: v for k, v in node.dict(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = "now()"

        response = supabase.table("nodes")\
            .update(update_data)\
            .eq("id", str(node_id))\
            .eq("workflow_id", str(workflow_id))\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Node not found")

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{workflow_id}/nodes/{node_id}")
async def delete_node(workflow_id: UUID, node_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("nodes")\
            .delete()\
            .eq("id", str(node_id))\
            .eq("workflow_id", str(workflow_id))\
            .execute()

        return {"message": "Node deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{workflow_id}/edges", response_model=EdgeResponse)
async def create_edge(workflow_id: UUID, edge: EdgeCreate, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("edges").insert({
            "workflow_id": str(workflow_id),
            "from_node_id": str(edge.from_node_id),
            "to_node_id": str(edge.to_node_id),
            "action": edge.action
        }).execute()

        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{workflow_id}/edges", response_model=List[EdgeResponse])
async def list_edges(workflow_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("edges")\
            .select("*")\
            .eq("workflow_id", str(workflow_id))\
            .execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{workflow_id}/edges/{edge_id}")
async def delete_edge(workflow_id: UUID, edge_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("edges")\
            .delete()\
            .eq("id", str(edge_id))\
            .eq("workflow_id", str(workflow_id))\
            .execute()

        return {"message": "Edge deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{workflow_id}/graph")
async def get_workflow_graph(workflow_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        nodes_response = supabase.table("nodes")\
            .select("*")\
            .eq("workflow_id", str(workflow_id))\
            .execute()

        edges_response = supabase.table("edges")\
            .select("*")\
            .eq("workflow_id", str(workflow_id))\
            .execute()

        return {
            "nodes": nodes_response.data,
            "edges": edges_response.data
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
