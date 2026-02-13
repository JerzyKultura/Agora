/*
  Node Success Rate Function
  
  Calculates actual success rate for a node based on telemetry data.
  Used by golden score algorithm to prioritize reliable nodes.
  
  NOTE: This function is created but NOT currently used by the Context Prime endpoint.
  It's here for future enhancement when you want to calculate real success rates
  instead of using hardcoded values (0.0 for failures, 0.5 for code changes).
*/

CREATE OR REPLACE FUNCTION get_node_success_rate(
    p_org_id UUID,
    p_node_name TEXT
) RETURNS TABLE(success_rate FLOAT) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        CASE 
            WHEN COUNT(*) = 0 THEN 0.5
            ELSE COUNT(*) FILTER (WHERE status != 'ERROR')::FLOAT / COUNT(*)::FLOAT
        END AS success_rate
    FROM telemetry_spans
    WHERE organization_id = p_org_id 
      AND name = p_node_name
      AND start_time > NOW() - INTERVAL '24 hours';
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_node_success_rate IS 'Calculates 24-hour success rate for a node (0.5 default if no data)';
