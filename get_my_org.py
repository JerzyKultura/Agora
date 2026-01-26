#!/usr/bin/env python3
"""
Get your user's organization ID for the demo workflow
"""

import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

supabase_url = os.environ.get("VITE_SUPABASE_URL")
supabase_key = os.environ.get("VITE_SUPABASE_ANON_KEY")

client = create_client(supabase_url, supabase_key)

# Get your organization
user_org = client.table("organizations").select("*").eq("name", "anirudhanil2013@gmail.com's Organization").execute()

if user_org.data:
    org_id = user_org.data[0]['id']
    print(f"Your Organization ID: {org_id}")
    print()
    print("Add this to your .env file:")
    print(f'AGORA_ORG_ID="{org_id}"')
    print()
    
    # Check if there's a project in this org
    projects = client.table("projects").select("*").eq("organization_id", org_id).execute()
    
    if projects.data:
        print(f"Existing projects in your org: {len(projects.data)}")
        for p in projects.data:
            print(f"  - {p['name']} (ID: {p['id']})")
        print()
        print("You can use one of these project IDs, or the demo will create a new one.")
    else:
        print("No existing projects in your org - demo will create a new one.")
else:
    print("Could not find your organization")
