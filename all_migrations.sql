/*
  AGORA CLOUD PLATFORM - FULL DATABASE SETUP (IDEMPOTENT)
  This script consolidates all migrations and is safe to run multiple times.
  It drops existing policies before recreating them to avoid "already exists" errors.
*/

-- ==========================================
-- 1. CORE TABLES 
-- ==========================================

-- Organizations
CREATE TABLE IF NOT EXISTS organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  name text NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;

-- Users (extends auth.users)
CREATE TABLE IF NOT EXISTS users (
  id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
  email text UNIQUE NOT NULL,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE users ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  TO authenticated
  USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- User Organizations (many-to-many)
CREATE TABLE IF NOT EXISTS user_organizations (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  role text NOT NULL CHECK (role IN ('owner', 'admin', 'member')) DEFAULT 'member',
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, organization_id)
);

ALTER TABLE user_organizations ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users can view their organization memberships" ON user_organizations;
CREATE POLICY "Users can view their organization memberships"
  ON user_organizations FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Now add organization policies that reference user_organizations
DROP POLICY IF EXISTS "Users can view their organizations" ON organizations;
CREATE POLICY "Users can view their organizations"
  ON organizations FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = organizations.id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- API Keys
CREATE TABLE IF NOT EXISTS api_keys (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  key_hash text NOT NULL UNIQUE,
  key_prefix text NOT NULL,
  last_used_at timestamptz,
  expires_at timestamptz,
  created_at timestamptz DEFAULT now(),
  revoked_at timestamptz
);

ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view API keys" ON api_keys;
CREATE POLICY "Organization members can view API keys"
  ON api_keys FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Organization admins can manage API keys" ON api_keys;
CREATE POLICY "Organization admins can manage API keys"
  ON api_keys FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = auth.uid()
      AND user_organizations.role IN ('owner', 'admin')
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = auth.uid()
      AND user_organizations.role IN ('owner', 'admin')
    )
  );

-- Projects
CREATE TABLE IF NOT EXISTS projects (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  organization_id uuid NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE projects ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view projects" ON projects;
CREATE POLICY "Organization members can view projects"
  ON projects FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = projects.organization_id
      AND user_organizations.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Organization members can manage projects" ON projects;
CREATE POLICY "Organization members can manage projects"
  ON projects FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = projects.organization_id
      AND user_organizations.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = projects.organization_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_user_organizations_user_id ON user_organizations(user_id);
CREATE INDEX IF NOT EXISTS idx_user_organizations_org_id ON user_organizations(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_org_id ON api_keys(organization_id);
CREATE INDEX IF NOT EXISTS idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX IF NOT EXISTS idx_projects_org_id ON projects(organization_id);


-- ==========================================
-- 2. WORKFLOW TABLES 
-- ==========================================

-- Workflows
CREATE TABLE IF NOT EXISTS workflows (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id uuid NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  name text NOT NULL,
  description text,
  type text NOT NULL CHECK (type IN ('sequential', 'dag', 'parallel')) DEFAULT 'sequential',
  config jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE workflows ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view workflows" ON workflows;
CREATE POLICY "Organization members can view workflows"
  ON workflows FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE projects.id = workflows.project_id
      AND user_organizations.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Organization members can manage workflows" ON workflows;
CREATE POLICY "Organization members can manage workflows"
  ON workflows FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE projects.id = workflows.project_id
      AND user_organizations.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM projects
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE projects.id = workflows.project_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Nodes
CREATE TABLE IF NOT EXISTS nodes (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  name text NOT NULL,
  type text NOT NULL,
  code text,
  config jsonb DEFAULT '{}',
  position_x integer DEFAULT 0,
  position_y integer DEFAULT 0,
  created_at timestamptz DEFAULT now(),
  updated_at timestamptz DEFAULT now()
);

ALTER TABLE nodes ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view nodes" ON nodes;
CREATE POLICY "Organization members can view nodes"
  ON nodes FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = nodes.workflow_id
      AND user_organizations.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Organization members can manage nodes" ON nodes;
CREATE POLICY "Organization members can manage nodes"
  ON nodes FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = nodes.workflow_id
      AND user_organizations.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = nodes.workflow_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Edges (connections between nodes)
CREATE TABLE IF NOT EXISTS edges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  from_node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  to_node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  action text NOT NULL,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE edges ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view edges" ON edges;
CREATE POLICY "Organization members can view edges"
  ON edges FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = edges.workflow_id
      AND user_organizations.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Organization members can manage edges" ON edges;
CREATE POLICY "Organization members can manage edges"
  ON edges FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = edges.workflow_id
      AND user_organizations.user_id = auth.uid()
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = edges.workflow_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_workflows_project_id ON workflows(project_id);
CREATE INDEX IF NOT EXISTS idx_nodes_workflow_id ON nodes(workflow_id);
CREATE INDEX IF NOT EXISTS idx_edges_workflow_id ON edges(workflow_id);
CREATE INDEX IF NOT EXISTS idx_edges_from_node ON edges(from_node_id);
CREATE INDEX IF NOT EXISTS idx_edges_to_node ON edges(to_node_id);


-- ==========================================
-- 3. TELEMETRY TABLES 
-- ==========================================

-- Executions (workflow runs)
CREATE TABLE IF NOT EXISTS executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  status text NOT NULL CHECK (status IN ('running', 'success', 'error', 'timeout')) DEFAULT 'running',
  started_at timestamptz DEFAULT now(),
  completed_at timestamptz,
  duration_ms numeric,
  error_message text,
  input_data jsonb,
  output_data jsonb,
  tokens_used integer,
  estimated_cost numeric,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE executions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view executions" ON executions;
CREATE POLICY "Organization members can view executions"
  ON executions FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = executions.workflow_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Node Executions (individual node runs)
CREATE TABLE IF NOT EXISTS node_executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  status text NOT NULL CHECK (status IN ('running', 'success', 'error', 'skipped')) DEFAULT 'running',
  started_at timestamptz DEFAULT now(),
  completed_at timestamptz,
  prep_duration_ms numeric,
  exec_duration_ms numeric,
  post_duration_ms numeric,
  prep_result jsonb,
  exec_result jsonb,
  post_result jsonb,
  error_message text,
  retry_count integer DEFAULT 0,
  tokens_used integer,
  estimated_cost numeric,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE node_executions ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view node executions" ON node_executions;
CREATE POLICY "Organization members can view node executions"
  ON node_executions FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM executions
      JOIN workflows ON workflows.id = executions.workflow_id
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE executions.id = node_executions.execution_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Shared State Snapshots
CREATE TABLE IF NOT EXISTS shared_state_snapshots (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  node_execution_id uuid REFERENCES node_executions(id) ON DELETE CASCADE,
  sequence integer NOT NULL,
  state_json jsonb NOT NULL,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE shared_state_snapshots ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view state snapshots" ON shared_state_snapshots;
CREATE POLICY "Organization members can view state snapshots"
  ON shared_state_snapshots FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM executions
      JOIN workflows ON workflows.id = executions.workflow_id
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE executions.id = shared_state_snapshots.execution_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Telemetry Spans (OpenTelemetry format)
CREATE TABLE IF NOT EXISTS telemetry_spans (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid REFERENCES executions(id) ON DELETE CASCADE,
  node_execution_id uuid REFERENCES node_executions(id) ON DELETE CASCADE,
  span_id text NOT NULL,
  trace_id text NOT NULL,
  parent_span_id text,
  name text NOT NULL,
  kind text,
  status text,
  start_time timestamptz NOT NULL,
  end_time timestamptz,
  duration_ms numeric,
  attributes jsonb DEFAULT '{}',
  events jsonb DEFAULT '[]',
  tokens_used integer,
  estimated_cost numeric,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE telemetry_spans ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view telemetry spans" ON telemetry_spans;
CREATE POLICY "Organization members can view telemetry spans"
  ON telemetry_spans FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM executions
      JOIN workflows ON workflows.id = executions.workflow_id
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE executions.id = telemetry_spans.execution_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Telemetry Events (raw event stream)
CREATE TABLE IF NOT EXISTS telemetry_events (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid REFERENCES executions(id) ON DELETE CASCADE,
  node_execution_id uuid REFERENCES node_executions(id) ON DELETE CASCADE,
  event_type text NOT NULL,
  timestamp timestamptz DEFAULT now(),
  data jsonb DEFAULT '{}',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE telemetry_events ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Organization members can view telemetry events" ON telemetry_events;
CREATE POLICY "Organization members can view telemetry events"
  ON telemetry_events FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM executions
      JOIN workflows ON workflows.id = executions.workflow_id
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE executions.id = telemetry_events.execution_id
      AND user_organizations.user_id = auth.uid()
    )
  );

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_executions_workflow_id ON executions(workflow_id);
CREATE INDEX IF NOT EXISTS idx_executions_status ON executions(status);
CREATE INDEX IF NOT EXISTS idx_executions_started_at ON executions(started_at DESC);
CREATE INDEX IF NOT EXISTS idx_node_executions_execution_id ON node_executions(execution_id);
CREATE INDEX IF NOT EXISTS idx_node_executions_node_id ON node_executions(node_id);
CREATE INDEX IF NOT EXISTS idx_state_snapshots_execution_id ON shared_state_snapshots(execution_id);
CREATE INDEX IF NOT EXISTS idx_state_snapshots_sequence ON shared_state_snapshots(execution_id, sequence);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_execution_id ON telemetry_spans(execution_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_trace_id ON telemetry_spans(trace_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_execution_id ON telemetry_events(execution_id);
CREATE INDEX IF NOT EXISTS idx_telemetry_events_timestamp ON telemetry_events(timestamp DESC);


-- ==========================================
-- 4. FIX API KEYS & AUTH TRIGGERS 
-- ==========================================

-- Drop the overly restrictive "FOR ALL" policy
DROP POLICY IF EXISTS "Organization admins can manage API keys" ON api_keys;

-- Create separate policies for INSERT, UPDATE, DELETE
DROP POLICY IF EXISTS "Organization members can insert API keys" ON api_keys;
CREATE POLICY "Organization members can insert API keys"
  ON api_keys FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = auth.uid()
    )
  );

DROP POLICY IF EXISTS "Organization admins can update API keys" ON api_keys;
CREATE POLICY "Organization admins can update API keys"
  ON api_keys FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = auth.uid()
      AND user_organizations.role IN ('owner', 'admin')
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = auth.uid()
      AND user_organizations.role IN ('owner', 'admin')
    )
  );

DROP POLICY IF EXISTS "Organization admins can delete API keys" ON api_keys;
CREATE POLICY "Organization admins can delete API keys"
  ON api_keys FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = auth.uid()
      AND user_organizations.role IN ('owner', 'admin')
    )
  );

-- Function to create organization and link user on signup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  new_org_id uuid;
BEGIN
  -- Insert user into users table
  INSERT INTO users (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;

  -- Ensure columns exist even if tables were already created
ALTER TABLE executions ADD COLUMN IF NOT EXISTS tokens_used integer;
ALTER TABLE executions ADD COLUMN IF NOT EXISTS estimated_cost numeric;

ALTER TABLE node_executions ADD COLUMN IF NOT EXISTS tokens_used integer;
ALTER TABLE node_executions ADD COLUMN IF NOT EXISTS estimated_cost numeric;

ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS tokens_used integer;
ALTER TABLE telemetry_spans ADD COLUMN IF NOT EXISTS estimated_cost numeric;
  -- Create organization for user
  INSERT INTO organizations (name)
  VALUES (COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email) || '''s Organization')
  RETURNING id INTO new_org_id;

  -- Link user to organization as owner
  INSERT INTO user_organizations (user_id, organization_id, role)
  VALUES (NEW.id, new_org_id, 'owner');

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call the function on auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

-- Backfill for existing users (create org if they don't have one)
DO $$
DECLARE
  user_record RECORD;
  new_org_id uuid;
BEGIN
  FOR user_record IN 
    SELECT au.id, au.email 
    FROM auth.users au
    LEFT JOIN users u ON u.id = au.id
    WHERE u.id IS NULL
  LOOP
    -- Insert into users table
    INSERT INTO users (id, email)
    VALUES (user_record.id, user_record.email)
    ON CONFLICT (id) DO NOTHING;

    -- Check if user has an organization
    IF NOT EXISTS (
      SELECT 1 FROM user_organizations 
      WHERE user_id = user_record.id
    ) THEN
      -- Create organization
      INSERT INTO organizations (name)
      VALUES (user_record.email || '''s Organization')
      RETURNING id INTO new_org_id;

      -- Link user to organization
      INSERT INTO user_organizations (user_id, organization_id, role)
      VALUES (user_record.id, new_org_id, 'owner');
    END IF;
  END LOOP;
END $$;


-- ==========================================
-- 5. SECURITY & PERFORMANCE (Using Optimized Patterns)
-- ==========================================

-- Add Missing Foreign Key Indexes
CREATE INDEX IF NOT EXISTS idx_shared_state_snapshots_node_execution_id 
  ON shared_state_snapshots(node_execution_id);

CREATE INDEX IF NOT EXISTS idx_telemetry_events_node_execution_id 
  ON telemetry_events(node_execution_id);

CREATE INDEX IF NOT EXISTS idx_telemetry_spans_node_execution_id 
  ON telemetry_spans(node_execution_id);

-- Optimize RLS Policies - Use (select auth.uid())
-- This is a more performant pattern for Supabase

-- Users table
DROP POLICY IF EXISTS "Users can view own profile" ON users;
CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  TO authenticated
  USING ((select auth.uid()) = id);

DROP POLICY IF EXISTS "Users can update own profile" ON users;
CREATE POLICY "Users can update own profile"
  ON users FOR UPDATE
  TO authenticated
  USING ((select auth.uid()) = id)
  WITH CHECK ((select auth.uid()) = id);

-- User Organizations table
DROP POLICY IF EXISTS "Users can view their organization memberships" ON user_organizations;
CREATE POLICY "Users can view their organization memberships"
  ON user_organizations FOR SELECT
  TO authenticated
  USING (user_id = (select auth.uid()));

-- Organizations table
DROP POLICY IF EXISTS "Users can view their organizations" ON organizations;
CREATE POLICY "Users can view their organizations"
  ON organizations FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = organizations.id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- API Keys table
DROP POLICY IF EXISTS "Organization members can view API keys" ON api_keys;
CREATE POLICY "Organization members can view API keys"
  ON api_keys FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

DROP POLICY IF EXISTS "Organization members can insert API keys" ON api_keys;
CREATE POLICY "Organization members can insert API keys"
  ON api_keys FOR INSERT
  TO authenticated
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

DROP POLICY IF EXISTS "Organization admins can update API keys" ON api_keys;
CREATE POLICY "Organization admins can update API keys"
  ON api_keys FOR UPDATE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = (select auth.uid())
      AND user_organizations.role IN ('owner', 'admin')
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = (select auth.uid())
      AND user_organizations.role IN ('owner', 'admin')
    )
  );

DROP POLICY IF EXISTS "Organization admins can delete API keys" ON api_keys;
CREATE POLICY "Organization admins can delete API keys"
  ON api_keys FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = (select auth.uid())
      AND user_organizations.role IN ('owner', 'admin')
    )
  );

-- Projects
DROP POLICY IF EXISTS "Organization members can view projects" ON projects;
DROP POLICY IF EXISTS "Organization members can manage projects" ON projects;
CREATE POLICY "Organization members can manage projects"
  ON projects FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = projects.organization_id
      AND user_organizations.user_id = (select auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = projects.organization_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Workflows
DROP POLICY IF EXISTS "Organization members can view workflows" ON workflows;
DROP POLICY IF EXISTS "Organization members can manage workflows" ON workflows;
CREATE POLICY "Organization members can manage workflows"
  ON workflows FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM projects
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE projects.id = workflows.project_id
      AND user_organizations.user_id = (select auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM projects
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE projects.id = workflows.project_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Nodes
DROP POLICY IF EXISTS "Organization members can view nodes" ON nodes;
DROP POLICY IF EXISTS "Organization members can manage nodes" ON nodes;
CREATE POLICY "Organization members can manage nodes"
  ON nodes FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = nodes.workflow_id
      AND user_organizations.user_id = (select auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = nodes.workflow_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Edges
DROP POLICY IF EXISTS "Organization members can view edges" ON edges;
DROP POLICY IF EXISTS "Organization members can manage edges" ON edges;
CREATE POLICY "Organization members can manage edges"
  ON edges FOR ALL
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = edges.workflow_id
      AND user_organizations.user_id = (select auth.uid())
    )
  )
  WITH CHECK (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = edges.workflow_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Update Read-Only Policies with Optimized Pattern
-- Executions
DROP POLICY IF EXISTS "Organization members can view executions" ON executions;
CREATE POLICY "Organization members can view executions"
  ON executions FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = executions.workflow_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Node Executions
DROP POLICY IF EXISTS "Organization members can view node executions" ON node_executions;
CREATE POLICY "Organization members can view node executions"
  ON node_executions FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM executions
      JOIN workflows ON workflows.id = executions.workflow_id
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE executions.id = node_executions.execution_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Shared State Snapshots
DROP POLICY IF EXISTS "Organization members can view state snapshots" ON shared_state_snapshots;
CREATE POLICY "Organization members can view state snapshots"
  ON shared_state_snapshots FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM executions
      JOIN workflows ON workflows.id = executions.workflow_id
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE executions.id = shared_state_snapshots.execution_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Telemetry Spans
DROP POLICY IF EXISTS "Organization members can view telemetry spans" ON telemetry_spans;
CREATE POLICY "Organization members can view telemetry spans"
  ON telemetry_spans FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM executions
      JOIN workflows ON workflows.id = executions.workflow_id
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE executions.id = telemetry_spans.execution_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Telemetry Events
DROP POLICY IF EXISTS "Organization members can view telemetry events" ON telemetry_events;
CREATE POLICY "Organization members can view telemetry events"
  ON telemetry_events FOR SELECT
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM executions
      JOIN workflows ON workflows.id = executions.workflow_id
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE executions.id = telemetry_events.execution_id
      AND user_organizations.user_id = (select auth.uid())
    )
  );

-- Fix Function Search Path & Security
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  new_org_id uuid;
BEGIN
  -- Insert user into users table
  INSERT INTO public.users (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;

  -- Create organization for user
  INSERT INTO public.organizations (name)
  VALUES (COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email) || '''s Organization')
  RETURNING id INTO new_org_id;

  -- Link user to organization as owner
  INSERT INTO public.user_organizations (user_id, organization_id, role)
  VALUES (NEW.id, new_org_id, 'owner');

  RETURN NEW;
END;
$$;


-- ==========================================
-- 6. DEMO MODE (Public Ingestion for Development)
-- ==========================================
-- These policies allow the Python demo script (using the ANON key) to write data.
-- ⚠️ WARNING: Remove these before going to production.

-- Projects: Allow anyone to view projects (to find the ID)
DROP POLICY IF EXISTS "Allow anon to view projects" ON projects;
DROP POLICY IF EXISTS "Public can view projects" ON projects;
CREATE POLICY "Public can view projects" ON projects FOR SELECT TO public USING (true);

-- Workflows: Allow anyone to manage workflows
DROP POLICY IF EXISTS "Allow anon to view workflows" ON workflows;
DROP POLICY IF EXISTS "Allow anon to insert workflows" ON workflows;
DROP POLICY IF EXISTS "Public can manage workflows" ON workflows;
CREATE POLICY "Public can manage workflows" ON workflows FOR ALL TO public USING (true) WITH CHECK (true);

-- Nodes: Allow anyone to manage nodes
DROP POLICY IF EXISTS "Allow anon to view nodes" ON nodes;
DROP POLICY IF EXISTS "Allow anon to insert nodes" ON nodes;
DROP POLICY IF EXISTS "Public can manage nodes" ON nodes;
CREATE POLICY "Public can manage nodes" ON nodes FOR ALL TO public USING (true) WITH CHECK (true);

-- Edges: Allow anyone to manage edges
DROP POLICY IF EXISTS "Public can manage edges" ON edges;
CREATE POLICY "Public can manage edges" ON edges FOR ALL TO public USING (true) WITH CHECK (true);

-- Executions: Allow anyone to manage executions
DROP POLICY IF EXISTS "Allow public insert on executions" ON executions;
DROP POLICY IF EXISTS "Allow public update on executions" ON executions;
DROP POLICY IF EXISTS "Allow public select on executions" ON executions;
DROP POLICY IF EXISTS "Public can manage executions" ON executions;
CREATE POLICY "Public can manage executions" ON executions FOR ALL TO public USING (true) WITH CHECK (true);

-- Node Executions: Allow anyone to manage node executions
DROP POLICY IF EXISTS "Allow public insert on node_executions" ON node_executions;
DROP POLICY IF EXISTS "Allow public select on node_executions" ON node_executions;
DROP POLICY IF EXISTS "Public can manage node_executions" ON node_executions;
CREATE POLICY "Public can manage node_executions" ON node_executions FOR ALL TO public USING (true) WITH CHECK (true);

-- Telemetry Spans: Allow anyone to manage telemetry spans
DROP POLICY IF EXISTS "Public can manage telemetry_spans" ON telemetry_spans;
CREATE POLICY "Public can manage telemetry_spans" ON telemetry_spans FOR ALL TO public USING (true) WITH CHECK (true);

-- Shared State Snapshots: Allow anyone to manage shared state snapshots
DROP POLICY IF EXISTS "Public can manage shared_state_snapshots" ON shared_state_snapshots;
CREATE POLICY "Public can manage shared_state_snapshots" ON shared_state_snapshots FOR ALL TO public USING (true) WITH CHECK (true);

-- Telemetry Events: Allow anyone to manage telemetry events
DROP POLICY IF EXISTS "Public can manage telemetry_events" ON telemetry_events;
CREATE POLICY "Public can manage telemetry_events" ON telemetry_events FOR ALL TO public USING (true) WITH CHECK (true);
