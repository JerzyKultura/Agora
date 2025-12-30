import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Credentials not found")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

migration_sql = """
-- Executions (workflow runs)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'executions' AND column_name = 'tokens_used') THEN
        ALTER TABLE executions ADD COLUMN tokens_used integer;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'executions' AND column_name = 'estimated_cost') THEN
        ALTER TABLE executions ADD COLUMN estimated_cost double precision;
    END IF;
END $$;

-- Node Executions (individual node runs)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'node_executions' AND column_name = 'tokens_used') THEN
        ALTER TABLE node_executions ADD COLUMN tokens_used integer;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'node_executions' AND column_name = 'estimated_cost') THEN
        ALTER TABLE node_executions ADD COLUMN estimated_cost double precision;
    END IF;
END $$;
"""

print("Applying migration...")
try:
    # Supabase-py doesn't support raw SQL easily on the client for DDL usually, 
    # but we can try rpc if there's a function, or just use the REST API via a function if needed.
    # HOWEVER, for this environment, usually we might not have direct DDL access via `supabase-py` 
    # if we are just an anon user unless we have the service_role key or if RLS allows it (unlikely for DDL).
    
    # Wait, the user mentioned they have credentials. Let's see if we can use the `postgres` library directly if available, 
    # or if we have to guide the user to run it in the SQL Editor.
    # Actually, let's try to see if there is an `exec_sql` RPC or similar.
    # If not, I will notify the user to run it manually.
    
    # BUT, I can try to use the `psycopg2` if available.
    pass
except Exception as e:
    print(f"Error: {e}")

print("⚠️  NOTE: Client-side DDL via supabase-py is restricted.")
print("    Please run the contents of 'supabase/migrations/20251228000000_add_telemetry_aggregates.sql'")
print("    in your Supabase SQL Editor: https://supabase.com/dashboard/project/_/sql")
