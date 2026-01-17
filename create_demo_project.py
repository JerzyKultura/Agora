#!/usr/bin/env python3
"""
Create a project for the demo workflow using your authenticated session.
This bypasses RLS by creating the project through the proper authentication flow.
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.environ.get("VITE_SUPABASE_URL")
supabase_key = os.environ.get("VITE_SUPABASE_ANON_KEY")
org_id = os.environ.get("AGORA_ORG_ID")

client = create_client(supabase_url, supabase_key)

print("=" * 70)
print("CREATING E-COMMERCE PROJECT")
print("=" * 70)
print()

# Check if project already exists
existing = client.table("projects").select("*").eq("organization_id", org_id).eq("name", "E-Commerce Order Processing").execute()

if existing.data:
    project = existing.data[0]
    print(f"✅ Project already exists: {project['name']}")
    print(f"   ID: {project['id']}")
else:
    # Create the project
    try:
        result = client.table("projects").insert({
            "organization_id": org_id,
            "name": "E-Commerce Order Processing",
            "description": "Demo e-commerce workflow with order validation, inventory, and payment processing"
        }).execute()
        
        project = result.data[0]
        print(f"✅ Created project: {project['name']}")
        print(f"   ID: {project['id']}")
    except Exception as e:
        print(f"❌ Failed to create project: {e}")
        print()
        print("This is likely due to RLS policies.")
        print("You need to create the project through the frontend UI:")
        print("  1. Go to http://localhost:5173/projects")
        print("  2. Click 'New Project'")
        print("  3. Name: E-Commerce Order Processing")
        print("  4. Description: Demo e-commerce workflow")
        print()
        exit(1)

print()
print("=" * 70)
print("NEXT STEP")
print("=" * 70)
print()
print("Add this to your .env file:")
print(f'AGORA_PROJECT_ID="{project["id"]}"')
print()
print("Then run: python3 dashboard_demo.py")
print()
