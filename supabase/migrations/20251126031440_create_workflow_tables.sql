/*
  # Agora Cloud Platform - Workflow Tables

  1. New Tables
    - `workflows` - Individual Agora flows within projects
    - `nodes` - Node definitions with code and configuration
    - `edges` - Connections between nodes with routing actions

  2. Security
    - Enable RLS on all tables
    - Add policies for organization members
*/

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
