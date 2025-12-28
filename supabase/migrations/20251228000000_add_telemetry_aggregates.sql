/*
  # Add Telemetry Aggregates

  1. Changes
    - Add `tokens_used` (integer) to `executions` table
    - Add `estimated_cost` (double precision) to `executions` table
    - Add `tokens_used` (integer) to `node_executions` table
    - Add `estimated_cost` (double precision) to `node_executions` table
  
  2. Purpose
    - Allow extracting token/cost metrics from `telemetry_spans` into the main execution record
    - Enable simpler querying for costs without joining spans
    - Support the SupabaseUploader's direct insertion of these values
*/

-- Executions (workflow runs)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'executions' AND column_name = 'tokens_used') THEN
        ALTER TABLE executions ADD COLUMN tokens_used integer;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'executions' AND column_name = 'estimated_cost') THEN
        ALTER TABLE executions ADD COLUMN estimated_cost double precision;
    END IF;
END $$;

-- Node Executions (individual node runs)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'node_executions' AND column_name = 'tokens_used') THEN
        ALTER TABLE node_executions ADD COLUMN tokens_used integer;
    END IF;

    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'node_executions' AND column_name = 'estimated_cost') THEN
        ALTER TABLE node_executions ADD COLUMN estimated_cost double precision;
    END IF;
END $$;
