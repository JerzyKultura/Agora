import os
import asyncio
from dotenv import load_dotenv
from supabase import create_client
from datetime import datetime, timezone
import time

load_dotenv()

SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Credentials not found")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

async def verify_trigger():
    print("🧪 Testing Enterprise SQL Trigger (Auto-Aggregation)...")
    
    # 1. Get/Create Project
    res = client.table("projects").select("id").limit(1).execute()
    if not res.data:
        print("❌ No projects found to test with.")
        return
    project_id = res.data[0]['id']

    # 2. Get/Create Workflow
    res = client.table("workflows").select("id").limit(1).execute()
    if res.data:
        workflow_id = res.data[0]['id']
    else:
        # Create one
        wf_res = client.table("workflows").insert({
            "project_id": project_id,
            "name": "Trigger Test Workflow",
            "type": "sequential",
            "config": {}
        }).execute()
        workflow_id = wf_res.data[0]['id']

    # 3. Create an Execution (Initiated with 0 cost)
    print("\n1. Creating Execution (Cost: 0)...")
    exec_data = {
        "workflow_id": workflow_id,
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "tokens_used": 0,
        "estimated_cost": 0.0
    }
    exec_res = client.table("executions").insert(exec_data).execute()
    execution_id = exec_res.data[0]['id']
    print(f"   Execution ID: {execution_id}")

    # 4. Insert a Span (The "Action")
    print("\n2. Inserting Telemetry Span (Cost: $0.05)...")
    span_data = {
        "execution_id": execution_id,
        "span_id": format(int(time.time() * 1000), '016x'), # Fake 16-char hex ID
        "trace_id": format(int(time.time() * 1000), '032x'), # Fake 32-char hex ID
        "name": "TestSpan",
        "start_time": datetime.now(timezone.utc).isoformat(),
        "end_time": datetime.now(timezone.utc).isoformat(),
        "attributes": {
            "tokens_used": 100,
            "estimated_cost": 0.05
        }
    }
    client.table("telemetry_spans").insert(span_data).execute()

    # 5. Verify Aggregation (The "Reaction")
    print("\n3. Waiting for Trigger (1s)...")
    time.sleep(1) # Give Postgres a split second (though standard triggers are usually immediate in transaction, PostgREST might return early)
    
    print("4. Checking Execution Record...")
    final_res = client.table("executions").select("*").eq("id", execution_id).execute()
    final_row = final_res.data[0]
    
    cost = final_row.get('estimated_cost')
    tokens = final_row.get('tokens_used')
    
    print(f"   Found Cost: ${cost}")
    print(f"   Found Tokens: {tokens}")
    
    if cost == 0.05 and tokens == 100:
        print("\n✅ SUCCESS! The Database is doing the math correctly.")
    else:
        print("\n❌ FAILURE! The Database did NOT update the execution.")
        print("   Did you apply the migration '20251228000001_add_aggregation_trigger.sql'?")

if __name__ == "__main__":
    asyncio.run(verify_trigger())
