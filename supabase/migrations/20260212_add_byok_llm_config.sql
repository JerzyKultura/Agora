-- Migration: Add BYOK LLM Configuration to Organizations
-- Created: 2026-02-12
-- Description: Adds columns for storing encrypted user LLM API keys (BYOK)

-- Add LLM configuration columns
ALTER TABLE organizations
ADD COLUMN IF NOT EXISTS llm_provider TEXT CHECK (llm_provider IN ('gemini', 'openai')),
ADD COLUMN IF NOT EXISTS llm_api_key_encrypted TEXT,
ADD COLUMN IF NOT EXISTS llm_config_updated_at TIMESTAMPTZ;

-- Add comment for documentation
COMMENT ON COLUMN organizations.llm_provider IS 'LLM provider for context summarization (gemini or openai)';
COMMENT ON COLUMN organizations.llm_api_key_encrypted IS 'Encrypted API key for BYOK (Bring Your Own Key) - encrypted using Fernet';
COMMENT ON COLUMN organizations.llm_config_updated_at IS 'Timestamp when LLM configuration was last updated';

-- Create index for faster lookups
CREATE INDEX IF NOT EXISTS idx_organizations_llm_provider ON organizations(llm_provider) WHERE llm_provider IS NOT NULL;

-- Add trigger to update llm_config_updated_at
CREATE OR REPLACE FUNCTION update_llm_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.llm_provider IS DISTINCT FROM OLD.llm_provider 
       OR NEW.llm_api_key_encrypted IS DISTINCT FROM OLD.llm_api_key_encrypted THEN
        NEW.llm_config_updated_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_llm_config_timestamp
    BEFORE UPDATE ON organizations
    FOR EACH ROW
    EXECUTE FUNCTION update_llm_config_timestamp();
