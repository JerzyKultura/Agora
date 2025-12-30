import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime

load_dotenv()

SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Credentials not found")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def verify_schema():
    print("🔍 Verifying Database Schema...")
    
    # 1. Create a dummy workflow
    try:
        wf_res = client.table("workflows").insert({
            "project_id": (await get_test_project_id()),
            "name": "Schema Verification Workflow",
            "type": "sequential",  # <--- FIXED: Valid type
            "config": {}
        }).execute()
        workflow_id = wf_res.data[0]['id']
    except Exception as e:
        print(f"❌ Failed to create test workflow: {e}")
        return

    # 2. Try to insert execution with NEW columns
    print("\nTesting 'tokens_used' and 'estimated_cost' columns...")
    try:
        data = {
            "workflow_id": workflow_id,
            "status": "success",
            "started_at": datetime.now().isoformat(),
            "tokens_used": 1234,           # <--- NEW COLUMN
            "estimated_cost": 0.0567       # <--- NEW COLUMN
        }
        
        res = client.table("executions").insert(data).execute()
        
        # 3. Verify values match
        inserted = res.data[0]
        if inserted.get('tokens_used') == 1234 and inserted.get('estimated_cost') == 0.0567:
            print("✅ SUCCESS! New columns are writable and readable.")
            print(f"   - tokens_used: {inserted['tokens_used']}")
            print(f"   - estimated_cost: {inserted['estimated_cost']}")
        else:
            print("❌ FAILURE! Columns might be missing or values dropped.")
            print(f"   - Got: {inserted}")
            
    except Exception as e:
        print(f"❌ Error inserting data: {e}")
        print("   Did you run the migration successfully?")

async def get_test_project_id():
    # Helper to get any valid project ID
    res = client.table("projects").select("id").limit(1).execute()
    if res.data:
        return res.data[0]['id']
    # Fallback: create one
    org_res = client.table("organizations").select("id").limit(1).execute()
    if not org_res.data:
        org_res = client.table("organizations").insert({"name": "Test Org"}).execute()
    org_id = org_res.data[0]['id']
    
    proj_res = client.table("projects").insert({
        "organization_id": org_id,
        "name": "Test Project"
    }).execute()
    return proj_res.data[0]['id']

if __name__ == "__main__":
    asyncio.run(verify_schema())
