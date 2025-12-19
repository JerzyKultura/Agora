/*
  # ENABLE DEMO MODE (Allow Anonymous Telemetry Ingestion)
  
  This script relaxes Row Level Security (RLS) policies to allow 
  scripts running with the Anon Key (like demo_workflow.py) to:
  1. Find your Project.
  2. Upload Workflows, Nodes, and Executions to it.
  
  WARNING: This makes your project structure publicly writable by anyone with your Anon Key.
  Use this for development/demo purposes only. 
  For production, use Service Role Keys or authenticated API Keys.
*/

-- 1. Allow Anon to VIew Projects (to verify ID)
CREATE POLICY "Allow anon to view projects"
ON projects FOR SELECT
TO anon
USING (true);

-- 2. Allow Anon to Manage Workflows (Insert/Update)
CREATE POLICY "Allow anon to insert workflows"
ON workflows FOR INSERT
TO anon
WITH CHECK (true);

CREATE POLICY "Allow anon to update workflows"
ON workflows FOR UPDATE
TO anon
USING (true);

CREATE POLICY "Allow anon to select workflows"
ON workflows FOR SELECT
TO anon
USING (true);

-- 3. Allow Anon to Manage Nodes
CREATE POLICY "Allow anon to insert nodes"
ON nodes FOR INSERT
TO anon
WITH CHECK (true);

CREATE POLICY "Allow anon to update nodes"
ON nodes FOR UPDATE
TO anon
USING (true);

CREATE POLICY "Allow anon to select nodes"
ON nodes FOR SELECT
TO anon
USING (true);

-- 4. Allow Anon to Manage Edges
CREATE POLICY "Allow anon to insert edges"
ON edges FOR INSERT
TO anon
WITH CHECK (true);

CREATE POLICY "Allow anon to select edges"
ON edges FOR SELECT
TO anon
USING (true);

-- 5. Executions & Node Executions (Ensure they are open)
DROP POLICY IF EXISTS "Allow public insert on executions" ON executions;
CREATE POLICY "Allow public insert on executions" ON executions FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "Allow public update on executions" ON executions;
CREATE POLICY "Allow public update on executions" ON executions FOR UPDATE TO anon USING (true);

DROP POLICY IF EXISTS "Allow public select on executions" ON executions;
CREATE POLICY "Allow public select on executions" ON executions FOR SELECT TO anon USING (true);

DROP POLICY IF EXISTS "Allow public insert on node_executions" ON node_executions;
CREATE POLICY "Allow public insert on node_executions" ON node_executions FOR INSERT TO anon WITH CHECK (true);

DROP POLICY IF EXISTS "Allow public select on node_executions" ON node_executions;
CREATE POLICY "Allow public select on node_executions" ON node_executions FOR SELECT TO anon USING (true);
