/*
  Context Cache Table
  
  Caches Context Prime responses with 5-minute TTL to reduce:
  - Database queries
  - LLM API calls
  - Embedding API calls
  
  Includes golden scores in metadata for transparency.
*/

CREATE TABLE IF NOT EXISTS context_cache (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  project_id UUID NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
  organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
  context_summary TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}',
  llm_provider TEXT,
  generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  expires_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  
  UNIQUE(project_id)
);

CREATE INDEX IF NOT EXISTS idx_context_cache_project_id ON context_cache(project_id);
CREATE INDEX IF NOT EXISTS idx_context_cache_org_id ON context_cache(organization_id);
CREATE INDEX IF NOT EXISTS idx_context_cache_expires_at ON context_cache(expires_at);

COMMENT ON TABLE context_cache IS 'Caches Context Prime responses with 5-minute TTL';
COMMENT ON COLUMN context_cache.metadata IS 'Contains failure_scores, code_change_scores, and other golden score data';
COMMENT ON COLUMN context_cache.expires_at IS 'Cache entry expires after this timestamp (5 minutes from generation)';
