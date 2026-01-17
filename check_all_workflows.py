#!/usr/bin/env python3
"""
Check the latest workflow execution and see which organization it belongs to
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.environ.get("VITE_SUPABASE_URL")
supabase_key = os.environ.get("VITE_SUPABASE_ANON_KEY")

client = create_client(supabase_url, supabase_key)

print("=" * 70)
print("CHECKING ALL E-COMMERCE WORKFLOW DATA")
print("=" * 70)
print()

# Get ALL E-Commerce workflows
workflows = client.table("workflows").select("*").eq("name", "E-Commerce Order Processing").execute()

print(f"📊 Found {len(workflows.data)} E-Commerce workflows:")
print()

for wf in workflows.data:
    print(f"Workflow ID: {wf['id']}")
    print(f"  Project ID: {wf['project_id']}")
    
    # Get project info
    project = client.table("projects").select("*").eq("id", wf['project_id']).execute()
    if project.data:
        proj = project.data[0]
        print(f"  Project Name: {proj['name']}")
        print(f"  Organization ID: {proj['organization_id']}")
        
        # Get executions for this workflow
        executions = client.table("executions").select("id, status, started_at").eq("workflow_id", wf['id']).order("started_at", desc=True).limit(3).execute()
        print(f"  Recent Executions: {len(executions.data)}")
        for ex in executions.data:
            print(f"    - {ex['id']} ({ex['status']}) at {ex.get('started_at', 'N/A')}")
    print()

print("=" * 70)
print("YOUR ORGANIZATION")
print("=" * 70)
your_org_id = os.environ.get("AGORA_ORG_ID")
print(f"ID: {your_org_id}")
print()

# Check if any projects exist in your org
your_projects = client.table("projects").select("*").eq("organization_id", your_org_id).execute()
print(f"Projects in your org: {len(your_projects.data)}")
for p in your_projects.data:
    print(f"  - {p['name']} (ID: {p['id']})")
print()
