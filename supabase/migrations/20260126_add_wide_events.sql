-- Migration: Add Wide Events Table
-- Description: Create telemetry_wide_events table for comprehensive execution events
-- Following Boris Tane's logging best practices

-- Create wide events table
CREATE TABLE IF NOT EXISTS telemetry_wide_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  execution_id UUID UNIQUE NOT NULL,
  trace_id TEXT,
  timestamp TIMESTAMPTZ NOT NULL,
  
  -- Workflow context
  workflow_name TEXT,
  workflow_version TEXT,
  node_path TEXT[],
  
  -- User/Organization context (high-cardinality fields)
  user_id TEXT,
  organization_id UUID,
  subscription_tier TEXT,
  account_age_days INTEGER,
  
  -- Performance metrics
  duration_ms INTEGER,
  tokens_used INTEGER,
  estimated_cost NUMERIC(10, 6),
  llm_latency_ms INTEGER,
  llm_calls_count INTEGER,
  
  -- Outcome
  status TEXT CHECK (status IN ('success', 'error')),
  error_type TEXT,
  error_message TEXT,
  error_code TEXT,
  retry_count INTEGER DEFAULT 0,
  
  -- Context (JSONB for flexibility)
  feature_flags JSONB,
  deployment_id TEXT,
  region TEXT,
  service_version TEXT,
  
  -- Full event (store everything for future queries)
  event JSONB,
  
  -- Timestamps
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for high-cardinality queries
CREATE INDEX IF NOT EXISTS idx_wide_events_execution ON telemetry_wide_events(execution_id);
CREATE INDEX IF NOT EXISTS idx_wide_events_user ON telemetry_wide_events(user_id) WHERE user_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_wide_events_org ON telemetry_wide_events(organization_id);
CREATE INDEX IF NOT EXISTS idx_wide_events_workflow ON telemetry_wide_events(workflow_name);
CREATE INDEX IF NOT EXISTS idx_wide_events_status ON telemetry_wide_events(status);
CREATE INDEX IF NOT EXISTS idx_wide_events_timestamp ON telemetry_wide_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_wide_events_error_type ON telemetry_wide_events(error_type) WHERE error_type IS NOT NULL;

-- GIN index for JSONB queries (feature flags, full event)
CREATE INDEX IF NOT EXISTS idx_wide_events_feature_flags ON telemetry_wide_events USING GIN (feature_flags);
CREATE INDEX IF NOT EXISTS idx_wide_events_event ON telemetry_wide_events USING GIN (event);

-- Enable Row Level Security
ALTER TABLE telemetry_wide_events ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see events from their organization
CREATE POLICY "Users can view their organization's wide events"
  ON telemetry_wide_events
  FOR SELECT
  USING (
    organization_id IN (
      SELECT organization_id 
      FROM user_organizations 
      WHERE user_id = auth.uid()
    )
  );

-- Policy: Service role can insert wide events
CREATE POLICY "Service role can insert wide events"
  ON telemetry_wide_events
  FOR INSERT
  WITH CHECK (true);

-- Comment on table
COMMENT ON TABLE telemetry_wide_events IS 'Wide events: one comprehensive event per execution with all business context';
COMMENT ON COLUMN telemetry_wide_events.node_path IS 'Array of node names executed in order';
COMMENT ON COLUMN telemetry_wide_events.feature_flags IS 'JSONB object of enabled feature flags';
COMMENT ON COLUMN telemetry_wide_events.event IS 'Full event data as JSONB for future queries';
