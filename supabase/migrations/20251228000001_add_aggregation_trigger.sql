/*
  # Enterprise Hardening: Automated Cost Aggregation
  
  1. Purpose:
     - Move aggregation logic from Python (client) to Postgres (server).
     - Ensure `tokens_used` and `estimated_cost` are ALWAYS accurate, even if the Python script crashes.
  
  2. Components:
     - Function: `update_execution_totals()`
       - Calculates sums from `telemetry_spans`
       - Updates `executions`
     - Trigger: `on_telemetry_span_change`
       - Fires on INSERT/UPDATE/DELETE of spans
*/

-- 1. Create the Aggregation Function
CREATE OR REPLACE FUNCTION update_execution_totals()
RETURNS TRIGGER AS $$
DECLARE
    total_tokens integer;
    total_cost double precision;
BEGIN
    -- Calculate totals for the specific execution_id involved in the change
    -- We use COALESCE to safely handle nulls and casts to ensure type safety
    SELECT 
        COALESCE(SUM(
            COALESCE((attributes->>'tokens_used')::integer, 0) +
            COALESCE((attributes->>'tokens.total')::integer, 0) + 
            COALESCE((attributes->>'llm.usage.total_tokens')::integer, 0)
        ), 0),
        COALESCE(SUM(
            COALESCE((attributes->>'estimated_cost')::float, 0) + 
            COALESCE((attributes->>'cost')::float, 0)
        ), 0.0)
    INTO 
        total_tokens, 
        total_cost
    FROM 
        telemetry_spans
    WHERE 
        execution_id = NEW.execution_id;

    -- Update the parent execution record
    UPDATE executions
    SET 
        tokens_used = total_tokens,
        estimated_cost = total_cost
    WHERE 
        id = NEW.execution_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 2. Create the Trigger
DROP TRIGGER IF EXISTS on_telemetry_span_change ON telemetry_spans;

CREATE TRIGGER on_telemetry_span_change
AFTER INSERT OR UPDATE OR DELETE ON telemetry_spans
FOR EACH ROW
EXECUTE FUNCTION update_execution_totals();
