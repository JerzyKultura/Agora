/*
  # Agora Cloud Platform - Core Tables

  1. New Tables
    - `organizations` - Organization metadata
    - `users` - User profiles (extends auth.users)
    - `user_organizations` - Many-to-many user-organization relationship
    - `api_keys` - API keys for authentication
    - `projects` - Workflow project containers

  2. Security
    - Enable RLS on all tables
    - Add policies for authenticated users
*/

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

CREATE POLICY "Users can view own profile"
  ON users FOR SELECT
  TO authenticated
  USING (auth.uid() = id);

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

CREATE POLICY "Users can view their organization memberships"
  ON user_organizations FOR SELECT
  TO authenticated
  USING (user_id = auth.uid());

-- Now add organization policies that reference user_organizations
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
