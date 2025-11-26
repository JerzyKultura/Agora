/*
  # Fix Security and Performance Issues

  ## 1. Add Missing Foreign Key Indexes
  
  The following tables have foreign keys without covering indexes:
  - `shared_state_snapshots.node_execution_id`
  - `telemetry_events.node_execution_id`
  - `telemetry_spans.node_execution_id`

  ## 2. Optimize RLS Policies
  
  All RLS policies updated to use `(select auth.uid())` instead of `auth.uid()`
  to avoid re-evaluation for each row, improving query performance at scale.

  ## 3. Remove Duplicate Permissive Policies
  
  Consolidate multiple SELECT policies into single policies for:
  - `edges`
  - `nodes`
  - `projects`
  - `workflows`

  ## 4. Fix Function Search Path
  
  Set immutable search_path for `handle_new_user()` function to prevent
  security issues from mutable search paths.

  ## 5. Note on Unused Indexes
  
  Unused indexes are kept as they will be used once the application is in production.
  They are essential for query performance when data volume increases.
*/

-- ============================================================================
-- PART 1: Add Missing Foreign Key Indexes
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_shared_state_snapshots_node_execution_id 
  ON shared_state_snapshots(node_execution_id);

CREATE INDEX IF NOT EXISTS idx_telemetry_events_node_execution_id 
  ON telemetry_events(node_execution_id);

CREATE INDEX IF NOT EXISTS idx_telemetry_spans_node_execution_id 
  ON telemetry_spans(node_execution_id);

-- ============================================================================
-- PART 2: Optimize RLS Policies - Use (select auth.uid())
-- ============================================================================

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

-- ============================================================================
-- PART 3: Remove Duplicate Permissive Policies
-- ============================================================================

-- Projects: Remove duplicate SELECT policy
DROP POLICY IF EXISTS "Organization members can view projects" ON projects;

-- Keep only the "manage" policy which includes SELECT
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

-- Workflows: Remove duplicate SELECT policy
DROP POLICY IF EXISTS "Organization members can view workflows" ON workflows;

-- Keep only the "manage" policy
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

-- Nodes: Remove duplicate SELECT policy
DROP POLICY IF EXISTS "Organization members can view nodes" ON nodes;

-- Keep only the "manage" policy
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

-- Edges: Remove duplicate SELECT policy
DROP POLICY IF EXISTS "Organization members can view edges" ON edges;

-- Keep only the "manage" policy
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

-- ============================================================================
-- PART 4: Update Read-Only Policies with Optimized Pattern
-- ============================================================================

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

-- ============================================================================
-- PART 5: Fix Function Search Path
-- ============================================================================

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