from fastapi import APIRouter, HTTPException, Depends, Header
from typing import List, Optional
from uuid import UUID
from database import get_supabase
from supabase import Client
from models import (
    ProjectCreate, ProjectUpdate, ProjectResponse,
    WorkflowCreate, WorkflowUpdate, WorkflowResponse,
    NodeCreate, NodeUpdate, NodeResponse,
    EdgeCreate, EdgeResponse
)

router = APIRouter(prefix="/projects", tags=["Projects"])

async def get_current_user(authorization: Optional[str] = Header(None), supabase: Client = Depends(get_supabase)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid authorization header")

    token = authorization.replace("Bearer ", "")
    try:
        user = supabase.auth.get_user(token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid token")
        return user
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        user_org = supabase.table("user_organizations")\
            .select("organization_id")\
            .eq("user_id", user.user.id)\
            .maybeSingle()\
            .execute()

        if not user_org.data:
            raise HTTPException(status_code=403, detail="User not part of any organization")

        org_id = user_org.data["organization_id"]

        response = supabase.table("projects").insert({
            "organization_id": org_id,
            "name": project.name,
            "description": project.description
        }).execute()

        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        user_org = supabase.table("user_organizations")\
            .select("organization_id")\
            .eq("user_id", user.user.id)\
            .maybeSingle()\
            .execute()

        if not user_org.data:
            return []

        org_id = user_org.data["organization_id"]

        response = supabase.table("projects")\
            .select("*")\
            .eq("organization_id", org_id)\
            .order("created_at", desc=True)\
            .execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("projects")\
            .select("*")\
            .eq("id", str(project_id))\
            .maybeSingle()\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        return response.data
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: UUID, project: ProjectUpdate, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        update_data = {k: v for k, v in project.dict(exclude_unset=True).items() if v is not None}
        update_data["updated_at"] = "now()"

        response = supabase.table("projects")\
            .update(update_data)\
            .eq("id", str(project_id))\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="Project not found")

        return response.data[0]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.delete("/{project_id}")
async def delete_project(project_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("projects")\
            .delete()\
            .eq("id", str(project_id))\
            .execute()

        return {"message": "Project deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{project_id}/workflows", response_model=WorkflowResponse)
async def create_workflow(project_id: UUID, workflow: WorkflowCreate, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("workflows").insert({
            "project_id": str(project_id),
            "name": workflow.name,
            "description": workflow.description,
            "type": workflow.type,
            "config": workflow.config
        }).execute()

        return response.data[0]
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{project_id}/workflows", response_model=List[WorkflowResponse])
async def list_workflows(project_id: UUID, user = Depends(get_current_user), supabase: Client = Depends(get_supabase)):
    try:
        response = supabase.table("workflows")\
            .select("*")\
            .eq("project_id", str(project_id))\
            .order("created_at", desc=False)\
            .execute()

        return response.data
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
