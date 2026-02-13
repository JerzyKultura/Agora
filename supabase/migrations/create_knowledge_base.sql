-- Universal Code Ingestor - Supabase Schema
-- 
-- Creates the agora_knowledge_base table with vector search support
--
-- Prerequisites:
-- 1. Enable pgvector extension: CREATE EXTENSION IF NOT EXISTS vector;
-- 2. Ensure uuid-ossp is enabled: CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create the main knowledge base table
CREATE TABLE IF NOT EXISTS agora_knowledge_base (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Unique identifier (hash of file_path + function_name + language)
    node_hash TEXT UNIQUE NOT NULL,
    
    -- Function identification
    function_name TEXT NOT NULL,
    signature TEXT,
    file_path TEXT NOT NULL,
    line_start INTEGER,
    line_end INTEGER,
    language TEXT DEFAULT 'python',
    
    -- Source code and documentation
    source_code TEXT NOT NULL,
    docstring TEXT,
    intent_summary TEXT,  -- Generated for undocumented functions
    
    -- Type information
    parameters JSONB,  -- Array of {name, type_hint, default, is_required}
    return_type TEXT,
    
    -- Dependencies (function calls within this function)
    dependencies JSONB,  -- Array of strings (full call paths like "db.users.get")
    
    -- Semantic search
    embedding VECTOR(384),  -- sentence-transformers/all-MiniLM-L6-v2
    
    -- Telemetry (preserved on updates)
    usage_count INTEGER DEFAULT 0,
    success_rate FLOAT DEFAULT 0.5,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Additional metadata
    metadata JSONB DEFAULT '{}'::jsonb
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_knowledge_base_node_hash 
    ON agora_knowledge_base (node_hash);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_function_name 
    ON agora_knowledge_base (function_name);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_file_path 
    ON agora_knowledge_base (file_path);

CREATE INDEX IF NOT EXISTS idx_knowledge_base_language 
    ON agora_knowledge_base (language);

-- Vector similarity search index (IVFFlat for fast approximate search)
CREATE INDEX IF NOT EXISTS idx_knowledge_base_embedding 
    ON agora_knowledge_base 
    USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- Create RPC function for semantic search
-- 
-- Note: The <=> operator calculates cosine distance (0 = identical, 2 = opposite)
-- We convert to similarity with: 1 - distance (1 = identical, -1 = opposite)
-- 
-- Tuning match_threshold:
-- - 0.7 (default): Good balance, filters out unrelated results
-- - 0.8: Stricter, use if getting low-quality results
-- - 0.6: More permissive, use for exploratory search
CREATE OR REPLACE FUNCTION search_knowledge_base(
    query_embedding VECTOR(384),
    match_threshold FLOAT DEFAULT 0.7,
    match_count INT DEFAULT 10
)
RETURNS TABLE (
    id UUID,
    node_hash TEXT,
    function_name TEXT,
    signature TEXT,
    source_code TEXT,
    docstring TEXT,
    intent_summary TEXT,
    file_path TEXT,
    line_start INTEGER,
    line_end INTEGER,
    language TEXT,
    parameters JSONB,
    return_type TEXT,
    dependencies JSONB,
    embedding VECTOR(384),
    usage_count INTEGER,
    success_rate FLOAT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    metadata JSONB,
    similarity FLOAT
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        kb.id,
        kb.node_hash,
        kb.function_name,
        kb.signature,
        kb.source_code,
        kb.docstring,
        kb.intent_summary,
        kb.file_path,
        kb.line_start,
        kb.line_end,
        kb.language,
        kb.parameters,
        kb.return_type,
        kb.dependencies,
        kb.embedding,
        kb.usage_count,
        kb.success_rate,
        kb.created_at,
        kb.updated_at,
        kb.metadata,
        1 - (kb.embedding <=> query_embedding) AS similarity
    FROM agora_knowledge_base kb
    WHERE 1 - (kb.embedding <=> query_embedding) > match_threshold
    ORDER BY kb.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to auto-update updated_at
CREATE TRIGGER update_knowledge_base_updated_at
    BEFORE UPDATE ON agora_knowledge_base
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions (adjust role name as needed)
-- GRANT ALL ON agora_knowledge_base TO authenticated;
-- GRANT ALL ON agora_knowledge_base TO service_role;

COMMENT ON TABLE agora_knowledge_base IS 'Universal code knowledge base with semantic search capabilities';
COMMENT ON COLUMN agora_knowledge_base.node_hash IS 'Unique hash: sha256(file_path + function_name + language)';
COMMENT ON COLUMN agora_knowledge_base.embedding IS '384-dim vector from sentence-transformers/all-MiniLM-L6-v2';
COMMENT ON COLUMN agora_knowledge_base.dependencies IS 'Full call paths of functions called within this function (e.g., ["db.users.get", "validate_email"])';
COMMENT ON COLUMN agora_knowledge_base.intent_summary IS 'Auto-generated summary for undocumented functions';
