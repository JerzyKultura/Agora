/*
  # Agora Cloud Platform - Telemetry and Execution Tables

  1. New Tables
    - `executions` - Top-level workflow execution records
    - `node_executions` - Individual node runs with phase timings
    - `telemetry_spans` - OpenTelemetry span data with hierarchy
    - `shared_state_snapshots` - Shared dict state at each node
    - `telemetry_events` - Raw event stream from AuditLogger

  2. Security
    - Enable RLS on all tables
    - Add policies for organization members
*/

-- Executions (workflow runs)
CREATE TABLE IF NOT EXISTS executions (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  workflow_id uuid NOT NULL REFERENCES workflows(id) ON DELETE CASCADE,
  status text NOT NULL CHECK (status IN ('running', 'success', 'error', 'timeout')) DEFAULT 'running',
  started_at timestamptz DEFAULT now(),
  completed_at timestamptz,
  duration_ms integer,
  error_message text,
  input_data jsonb,
  output_data jsonb,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE executions ENABLE ROW LEVEL SECURITY;

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
  prep_duration_ms integer,
  exec_duration_ms integer,
  post_duration_ms integer,
  prep_result jsonb,
  exec_result jsonb,
  post_result jsonb,
  error_message text,
  retry_count integer DEFAULT 0,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE node_executions ENABLE ROW LEVEL SECURITY;

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
  duration_ms integer,
  attributes jsonb DEFAULT '{}',
  events jsonb DEFAULT '[]',
  created_at timestamptz DEFAULT now()
);

ALTER TABLE telemetry_spans ENABLE ROW LEVEL SECURITY;

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
