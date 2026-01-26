/*
  # Add Organization Filtering to Telemetry
  
  This migration adds organization_id to telemetry_spans table to enable
  proper multi-tenant data isolation.
  
  ## Changes
  1. Add organization_id column to telemetry_spans
  2. Create index for query performance
  3. Backfill existing data with first organization
  4. Add Row Level Security policy
  
  ## Security
  Users can only see telemetry spans from their own organization.
*/

-- Step 1: Add organization_id column (nullable initially for backfill)
ALTER TABLE telemetry_spans 
ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id);

-- Step 2: Create index for performance
CREATE INDEX IF NOT EXISTS idx_telemetry_spans_org_id 
ON telemetry_spans(organization_id);

-- Step 3: Backfill existing data
-- Link all existing spans to the first organization
-- (You can customize this logic based on your needs)
DO $$
DECLARE
  first_org_id UUID;
BEGIN
  -- Get the first organization ID
  SELECT id INTO first_org_id FROM organizations ORDER BY created_at LIMIT 1;
  
  -- Update all NULL organization_ids
  IF first_org_id IS NOT NULL THEN
    UPDATE telemetry_spans
    SET organization_id = first_org_id
    WHERE organization_id IS NULL;
  END IF;
END $$;

-- Step 4: Make organization_id required going forward
ALTER TABLE telemetry_spans 
ALTER COLUMN organization_id SET NOT NULL;

-- Step 5: Add Row Level Security Policy
DROP POLICY IF EXISTS "Users see only their org's telemetry" ON telemetry_spans;

CREATE POLICY "Users see only their org's telemetry"
ON telemetry_spans FOR SELECT
TO authenticated
USING (
  EXISTS (
    SELECT 1 FROM user_organizations
    WHERE user_organizations.organization_id = telemetry_spans.organization_id
    AND user_organizations.user_id = (select auth.uid())
  )
);

-- Step 6: Also add INSERT policy for SDK uploads
DROP POLICY IF EXISTS "Users can insert telemetry for their org" ON telemetry_spans;

CREATE POLICY "Users can insert telemetry for their org"
ON telemetry_spans FOR INSERT
TO authenticated
WITH CHECK (
  EXISTS (
    SELECT 1 FROM user_organizations
    WHERE user_organizations.organization_id = telemetry_spans.organization_id
    AND user_organizations.user_id = (select auth.uid())
  )
);

-- Verification query (run this to check the migration worked)
-- SELECT 
--   COUNT(*) as total_spans,
--   COUNT(DISTINCT organization_id) as unique_orgs,
--   COUNT(*) FILTER (WHERE organization_id IS NULL) as null_orgs
-- FROM telemetry_spans;
