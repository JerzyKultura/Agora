#!/usr/bin/env python3
"""
Show the E-Commerce workflow execution details
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.environ.get("VITE_SUPABASE_URL")
supabase_key = os.environ.get("VITE_SUPABASE_ANON_KEY")

client = create_client(supabase_url, supabase_key)

print("=" * 70)
print("E-COMMERCE WORKFLOW DATA")
print("=" * 70)
print()

# Get the E-Commerce workflow
workflow = client.table("workflows").select("*").eq("name", "E-Commerce Order Processing").execute()

if workflow.data:
    wf = workflow.data[0]
    print(f"✅ Workflow Found: {wf['name']}")
    print(f"   ID: {wf['id']}")
    print(f"   Project ID: {wf['project_id']}")
    print()
    
    # Get executions
    executions = client.table("executions").select("*").eq("workflow_id", wf['id']).execute()
    print(f"📊 Executions: {len(executions.data)}")
    for ex in executions.data:
        print(f"   - ID: {ex['id']}")
        print(f"     Status: {ex['status']}")
        print(f"     Duration: {ex.get('duration_ms', 'N/A')}ms")
    print()
    
    # Get nodes
    nodes = client.table("nodes").select("*").eq("workflow_id", wf['id']).execute()
    print(f"🔵 Nodes: {len(nodes.data)}")
    for node in nodes.data:
        print(f"   - {node['name']}")
    print()
    
    # Get project info
    project = client.table("projects").select("*").eq("id", wf['project_id']).execute()
    if project.data:
        proj = project.data[0]
        print(f"📁 Project: {proj['name']}")
        print(f"   Organization ID: {proj['organization_id']}")
        print()
        
        # Check your user's organization
        user_org = client.table("organizations").select("*").eq("name", "halfasandwich3@gmail.com's Organization").execute()
        if user_org.data:
            print(f"👤 Your Organization ID: {user_org.data[0]['id']}")
            print()
            
            if proj['organization_id'] != user_org.data[0]['id']:
                print("⚠️  ISSUE FOUND:")
                print("   The workflow was created under a different organization!")
                print("   You need to either:")
                print("   1. Log in as the organization that owns this data, OR")
                print("   2. Re-run the demo with your logged-in user's organization")
                print()
    
    print("=" * 70)
    print("DIRECT LINKS")
    print("=" * 70)
    print(f"Project: http://localhost:5173/projects/{wf['project_id']}")
    if executions.data:
        print(f"Execution: http://localhost:5173/executions/{executions.data[0]['id']}")
    print()
else:
    print("❌ E-Commerce Order Processing workflow not found")
