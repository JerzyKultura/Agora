from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from database import get_supabase
from supabase import Client
from models import APIKeyCreate, APIKeyResponse
from routers.projects import get_current_user
import secrets
import hashlib

router = APIRouter(prefix="/api-keys", tags=["API Keys"])

def generate_api_key() -> tuple[str, str, str]:
    """
    Generate a new API key.
    
    Returns:
        tuple: (full_key, key_hash, key_prefix)
        - full_key: The actual key to show user (only shown once)
        - key_hash: SHA256 hash to store in database
        - key_prefix: First 8 chars for identification
    """
    # Generate secure random key
    full_key = f"agora_key_{secrets.token_urlsafe(32)}"
    
    # Hash for storage
    key_hash = hashlib.sha256(full_key.encode()).hexdigest()
    
    # Prefix for display
    key_prefix = full_key[:16]
    
    return full_key, key_hash, key_prefix


@router.post("/", response_model=dict)
async def create_api_key(
    key_data: APIKeyCreate,
    user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """
    Create a new API key for the user's organization.
    The full key is only returned once - user must save it!
    """
    try:
        # Get user's organization
        user_org_response = supabase.table("user_organizations")\
            .select("organization_id")\
            .eq("user_id", user.user.id)\
            .execute()

        if not user_org_response.data:
            raise HTTPException(status_code=403, detail="User not part of any organization")

        org_id = user_org_response.data[0]["organization_id"]

        # Generate API key
        full_key, key_hash, key_prefix = generate_api_key()

        # Calculate expiry if provided
        expires_at = None
        if key_data.expires_at:
            expires_at = key_data.expires_at.isoformat()

        # Insert into database
        response = supabase.table("api_keys").insert({
            "organization_id": org_id,
            "name": key_data.name,
            "key_hash": key_hash,
            "key_prefix": key_prefix,
            "expires_at": expires_at
        }).execute()

        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create API key")

        # Return full key (only time it's shown!)
        return {
            "id": response.data[0]["id"],
            "name": key_data.name,
            "key": full_key,  # ← Only shown once!
            "key_prefix": key_prefix,
            "expires_at": expires_at,
            "created_at": response.data[0]["created_at"],
            "warning": "⚠️ Save this key now! It won't be shown again."
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=List[APIKeyResponse])
async def list_api_keys(
    user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """List all API keys for the user's organization."""
    try:
        # Get user's organization
        user_org_response = supabase.table("user_organizations")\
            .select("organization_id")\
            .eq("user_id", user.user.id)\
            .execute()

        if not user_org_response.data:
            return []

        org_id = user_org_response.data[0]["organization_id"]

        # Get all API keys
        response = supabase.table("api_keys")\
            .select("id, organization_id, name, key_prefix, created_at, expires_at, last_used_at, revoked_at")\
            .eq("organization_id", org_id)\
            .order("created_at", desc=True)\
            .execute()

        return response.data

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{key_id}")
async def revoke_api_key(
    key_id: UUID,
    user = Depends(get_current_user),
    supabase: Client = Depends(get_supabase)
):
    """Revoke an API key."""
    try:
        # Get user's organization
        user_org_response = supabase.table("user_organizations")\
            .select("organization_id")\
            .eq("user_id", user.user.id)\
            .execute()

        if not user_org_response.data:
            raise HTTPException(status_code=403, detail="User not part of any organization")

        org_id = user_org_response.data[0]["organization_id"]

        # Revoke the key (soft delete)
        response = supabase.table("api_keys")\
            .update({"revoked_at": datetime.utcnow().isoformat()})\
            .eq("id", str(key_id))\
            .eq("organization_id", org_id)\
            .execute()

        if not response.data:
            raise HTTPException(status_code=404, detail="API key not found")

        return {"message": "API key revoked successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# AUTHENTICATION HELPER - Used by other routes
# ============================================================================

async def authenticate_api_key(
    api_key: str,
    supabase: Client
) -> dict:
    """
    Authenticate an API key and return organization info.
    
    Args:
        api_key: The API key from request header
        supabase: Supabase client
    
    Returns:
        dict: {"organization_id": "...", "key_id": "..."}
    
    Raises:
        HTTPException: If key is invalid/revoked/expired
    """
    # Hash the provided key
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Look up key in database
    response = supabase.table("api_keys")\
        .select("id, organization_id, expires_at, revoked_at")\
        .eq("key_hash", key_hash)\
        .execute()
    
    if not response.data:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    key_data = response.data[0]
    
    # Check if revoked
    if key_data.get("revoked_at"):
        raise HTTPException(status_code=401, detail="API key has been revoked")
    
    # Check if expired
    if key_data.get("expires_at"):
        expires_at = datetime.fromisoformat(key_data["expires_at"].replace("Z", "+00:00"))
        if datetime.utcnow() > expires_at:
            raise HTTPException(status_code=401, detail="API key has expired")
    
    # Update last_used_at
    supabase.table("api_keys")\
        .update({"last_used_at": datetime.utcnow().isoformat()})\
        .eq("id", key_data["id"])\
        .execute()
    
    return {
        "organization_id": key_data["organization_id"],
        "key_id": key_data["id"]
    }