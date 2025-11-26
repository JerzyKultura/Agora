from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from database import get_supabase, get_supabase_admin
from supabase import Client

router = APIRouter(prefix="/auth", tags=["Authentication"])

class SignUpRequest(BaseModel):
    email: EmailStr
    password: str
    organization_name: str

class SignInRequest(BaseModel):
    email: EmailStr
    password: str

class AuthResponse(BaseModel):
    access_token: str
    refresh_token: str
    user: dict

@router.post("/signup", response_model=AuthResponse)
async def sign_up(request: SignUpRequest, supabase: Client = Depends(get_supabase_admin)):
    try:
        auth_response = supabase.auth.sign_up({
            "email": request.email,
            "password": request.password
        })

        if not auth_response.user:
            raise HTTPException(status_code=400, detail="Failed to create user")

        user_id = auth_response.user.id

        org_response = supabase.table("organizations").insert({
            "name": request.organization_name
        }).execute()

        if not org_response.data:
            raise HTTPException(status_code=400, detail="Failed to create organization")

        org_id = org_response.data[0]["id"]

        supabase.table("users").insert({
            "id": user_id,
            "email": request.email
        }).execute()

        supabase.table("user_organizations").insert({
            "user_id": user_id,
            "organization_id": org_id,
            "role": "owner"
        }).execute()

        return AuthResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user={
                "id": user_id,
                "email": request.email,
                "organization_id": org_id
            }
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/signin", response_model=AuthResponse)
async def sign_in(request: SignInRequest, supabase: Client = Depends(get_supabase)):
    try:
        auth_response = supabase.auth.sign_in_with_password({
            "email": request.email,
            "password": request.password
        })

        if not auth_response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Fixed: Replace .maybeSingle() with .execute() and proper data handling
        user_org_response = supabase.table("user_organizations")\
            .select("organization_id")\
            .eq("user_id", auth_response.user.id)\
            .execute()

        org_id = user_org_response.data[0]["organization_id"] if user_org_response.data else None

        return AuthResponse(
            access_token=auth_response.session.access_token,
            refresh_token=auth_response.session.refresh_token,
            user={
                "id": auth_response.user.id,
                "email": request.email,
                "organization_id": org_id
            }
        )

    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid credentials")

@router.post("/signout")
async def sign_out(supabase: Client = Depends(get_supabase)):
    try:
        supabase.auth.sign_out()
        return {"message": "Signed out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    