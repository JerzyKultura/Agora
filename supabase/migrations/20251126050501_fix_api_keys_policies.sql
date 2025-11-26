/*
  # Fix API Keys Policies and Auto-Organization Creation

  1. Changes
    - Add separate INSERT policy for API keys (the FOR ALL was too restrictive)
    - Create trigger to auto-create organization for new users
    - Create trigger to auto-add user to their organization

  2. Security
    - Users can insert API keys into their own organization
    - Users can delete API keys from their organization
    - Auto-created organization is owned by the user
*/

-- Drop the overly restrictive "FOR ALL" policy
DROP POLICY IF EXISTS "Organization admins can manage API keys" ON api_keys;

-- Create separate policies for INSERT, UPDATE, DELETE
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

CREATE POLICY "Organization admins can update API keys"
  ON api_keys FOR UPDATE
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

CREATE POLICY "Organization admins can delete API keys"
  ON api_keys FOR DELETE
  TO authenticated
  USING (
    EXISTS (
      SELECT 1 FROM user_organizations
      WHERE user_organizations.organization_id = api_keys.organization_id
      AND user_organizations.user_id = auth.uid()
      AND user_organizations.role IN ('owner', 'admin')
    )
  );

-- Function to create organization and link user on signup
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
  VALUES (COALESCE(NEW.raw_user_meta_data->>'full_name', NEW.email) || '''s Organization')
  RETURNING id INTO new_org_id;

  -- Link user to organization as owner
  INSERT INTO user_organizations (user_id, organization_id, role)
  VALUES (NEW.id, new_org_id, 'owner');

  RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Trigger to call the function on auth.users insert
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW
  EXECUTE FUNCTION handle_new_user();

-- Backfill for existing users (create org if they don't have one)
DO $$
DECLARE
  user_record RECORD;
  new_org_id uuid;
BEGIN
  FOR user_record IN 
    SELECT au.id, au.email 
    FROM auth.users au
    LEFT JOIN users u ON u.id = au.id
    WHERE u.id IS NULL
  LOOP
    -- Insert into users table
    INSERT INTO users (id, email)
    VALUES (user_record.id, user_record.email)
    ON CONFLICT (id) DO NOTHING;

    -- Check if user has an organization
    IF NOT EXISTS (
      SELECT 1 FROM user_organizations 
      WHERE user_id = user_record.id
    ) THEN
      -- Create organization
      INSERT INTO organizations (name)
      VALUES (user_record.email || '''s Organization')
      RETURNING id INTO new_org_id;

      -- Link user to organization
      INSERT INTO user_organizations (user_id, organization_id, role)
      VALUES (user_record.id, new_org_id, 'owner');
    END IF;
  END LOOP;
END $$;
