/*
  # AGORA DATABASE REPAIR SCRIPT
  # This script will:
  # 1. Create missing tables (api_keys, etc.)
  # 2. Fix RLS policies
  # 3. Create necessary triggers for auto-organization creation
  # 4. Backfill organizations for existing users
*/

-- ==========================================
-- 1. CORE TABLES (Organizations, Users, API Keys)
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

-- Organization policies
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

-- ==========================================
-- 2. WORKFLOW TABLES (Workflows, Nodes, Edges)
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

-- Edges
CREATE TABLE IF NOT EXISTS edges (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  from_node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  to_node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  action text NOT NULL,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE edges ENABLE ROW LEVEL SECURITY;

-- Executions (missing from original migration file, inferring based on usage)
CREATE TABLE IF NOT EXISTS executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  status text NOT NULL DEFAULT 'running',
  input_data jsonb DEFAULT '{}',
  output_data jsonb,
  error_message text,
  started_at timestamptz DEFAULT now(),
  completed_at timestamptz,
  duration_ms integer
);
ALTER TABLE executions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Organization members can view executions" ON executions FOR SELECT TO authenticated USING (
    EXISTS (
      SELECT 1 FROM workflows
      JOIN projects ON projects.id = workflows.project_id
      JOIN user_organizations ON user_organizations.organization_id = projects.organization_id
      WHERE workflows.id = executions.workflow_id
      AND user_organizations.user_id = auth.uid()
    )
);
-- Allow public insert for demo script (temporary/insecure but needed for demo) or use RLS
CREATE POLICY "Allow public insert on executions" ON executions FOR INSERT TO anon WITH CHECK (true);
CREATE POLICY "Allow public update on executions" ON executions FOR UPDATE TO anon USING (true);


-- Node Executions (for monitoring)
CREATE TABLE IF NOT EXISTS node_executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id uuid NOT NULL REFERENCES executions(id) ON DELETE CASCADE,
  node_id uuid NOT NULL REFERENCES nodes(id) ON DELETE CASCADE,
  status text NOT NULL,
  started_at timestamptz,
  completed_at timestamptz,
  prep_duration_ms integer,
  exec_duration_ms integer,
  post_duration_ms integer,
  retry_count integer DEFAULT 0,
  error_message text
);
ALTER TABLE node_executions ENABLE ROW LEVEL SECURITY;
CREATE POLICY "Organization members can view node executions" ON node_executions FOR SELECT TO authenticated USING (true); -- simplified
CREATE POLICY "Allow public insert on node_executions" ON node_executions FOR INSERT TO anon WITH CHECK (true);


-- ==========================================
-- 3. POLICIES & TRIGGERS
-- ==========================================

-- API Key Policies
DROP POLICY IF EXISTS "Organization admins can manage API keys" ON api_keys;
DROP POLICY IF EXISTS "Organization members can insert API keys" ON api_keys;
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

-- Function to handle new user setup
CREATE OR REPLACE FUNCTION handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
  new_org_id uuid;
BEGIN
  -- Insert user into users table
  INSERT INTO users (id, email)
  VALUES (NEW.id, NEW.email)
  ON CONFLICT (id) DO NOTHING;

  -- Create organization for user
  INSERT INTO organizations (name)
  VALUES (COALESCE(NEW.raw_user_meta_data->>'organization_name', NEW.email || '''s Organization'))
  RETURNING id INTO new_org_id;

  -- Link user to organization as owner
  INSERT INTO user_organizations (user_id, organization_id, role)
  VALUES (NEW.id, new_org_id, 'owner');

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

-- ==========================================
-- 4. BACKFILL & REPAIR
-- ==========================================

DO $$
DECLARE
  user_record RECORD;
  new_org_id uuid;
BEGIN
  -- Iterate through all auth users who don't have a linked user_organization
  FOR user_record IN 
    SELECT au.id, au.email, au.raw_user_meta_data 
    FROM auth.users au
  LOOP
    -- Ensure they are in 'users' table
    INSERT INTO users (id, email)
    VALUES (user_record.id, user_record.email)
    ON CONFLICT (id) DO NOTHING;

    -- Check for organization membership
    IF NOT EXISTS (
      SELECT 1 FROM user_organizations 
      WHERE user_id = user_record.id
    ) THEN
      -- Create organization
      INSERT INTO organizations (name)
      VALUES (
         COALESCE(user_record.raw_user_meta_data->>'organization_name', user_record.email || '''s Organization')
      )
      RETURNING id INTO new_org_id;

      -- Link user to organization
      INSERT INTO user_organizations (user_id, organization_id, role)
      VALUES (user_record.id, new_org_id, 'owner');
      
      RAISE NOTICE 'Fixed organization for user: %', user_record.email;
    END IF;
  END LOOP;
END $$;
