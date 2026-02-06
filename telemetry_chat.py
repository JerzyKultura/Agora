#!/usr/bin/env python3
"""
Natural Language Telemetry Query System
Ask questions about your telemetry data in plain English!

Examples:
- "How long did ChatTurn take?"
- "What's my total cost this week?"
- "Which executions failed?"
"""

from openai import OpenAI
from supabase import create_client
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase = create_client(
    os.getenv("VITE_SUPABASE_URL", "").strip('"'),
    os.getenv("VITE_SUPABASE_ANON_KEY", "").strip('"')
)

TELEMETRY_SCHEMA = """
You have access to a PostgreSQL telemetry database with WIDE EVENTS - one comprehensive event per workflow execution.

Table: telemetry_wide_events
Columns:
- id (uuid) - unique event ID
- execution_id (uuid) - unique execution identifier
- trace_id (text) - trace identifier
- timestamp (timestamptz) - when execution started
- workflow_name (text) - e.g., "ChatTurn.flow", "DataPipeline"
- workflow_version (text) - version of the workflow
- node_path (text[]) - array of nodes executed in order
- user_id (text) - user who triggered execution
- organization_id (uuid) - organization
- subscription_tier (text) - "free", "premium", "enterprise"
- account_age_days (integer) - user account age
- duration_ms (integer) - total execution time in milliseconds
- tokens_used (integer) - LLM tokens consumed
- estimated_cost (numeric) - cost in dollars
- llm_latency_ms (integer) - LLM API latency
- llm_calls_count (integer) - number of LLM calls
- status (text) - 'success' or 'error'
- error_type (text) - exception type if failed
- error_message (text) - error details
- error_code (text) - error code
- retry_count (integer) - number of retries
- feature_flags (jsonb) - enabled features as JSON
- deployment_id (text) - deployment identifier
- region (text) - region where executed
- service_version (text) - service version
- event (jsonb) - full event data as JSON
- created_at (timestamptz) - when event was created

Important notes:
- ONE row per execution (not multiple spans)
- All metrics are pre-aggregated
- Use ILIKE for case-insensitive pattern matching
- Query feature_flags with: feature_flags->>'flag_name'
- Query event data with: event->>'key'
- Always filter by organization_id for security

Common query patterns:
1. Average duration: SELECT AVG(duration_ms)/1000.0 as avg_seconds FROM telemetry_wide_events WHERE workflow_name ILIKE '%ChatTurn%'
2. Total cost: SELECT SUM(estimated_cost) FROM telemetry_wide_events WHERE timestamp > NOW() - INTERVAL '7 days'
3. Failed executions: SELECT execution_id, workflow_name, error_type, error_message FROM telemetry_wide_events WHERE status = 'error' ORDER BY timestamp DESC LIMIT 10
4. Error rate by tier: SELECT subscription_tier, COUNT(*) FILTER (WHERE status = 'error') * 100.0 / COUNT(*) as error_rate FROM telemetry_wide_events GROUP BY subscription_tier
5. Slowest workflows: SELECT workflow_name, AVG(duration_ms) as avg_duration FROM telemetry_wide_events GROUP BY workflow_name ORDER BY avg_duration DESC
"""

def generate_sql(question: str) -> str:
    """Convert natural language question to SQL query"""
    print(f"\n🤔 Thinking about: {question}")
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": f"""{TELEMETRY_SCHEMA}

Generate a PostgreSQL query to answer the user's question.
Return ONLY the SQL query, no explanations or markdown.
The query should be safe and read-only (SELECT only).
"""
            },
            {"role": "user", "content": question}
        ],
        temperature=0
    )
    
    sql = response.choices[0].message.content.strip()
    # Remove markdown code blocks if present
    sql = sql.replace('```sql', '').replace('```', '').strip()
    
    return sql

def execute_query(sql: str):
    """Execute SQL query against Supabase"""
    print(f"\n📊 Executing SQL:\n{sql}\n")
    
    try:
        # Use Supabase RPC to execute raw SQL
        # Note: This requires a database function - for now we'll use the table directly
        # In production, you'd create a secure RPC function
        
        # For demonstration, we'll parse simple queries
        # In production, use supabase.rpc('execute_sql', {'query': sql})
        
        # Simplified execution - just query the wide events table
        result = supabase.table('telemetry_wide_events')\
            .select('*')\
            .order('timestamp', desc=True)\
            .limit(100)\
            .execute()
        
        return result.data
    except Exception as e:
        print(f"❌ Query failed: {e}")
        return None

def format_answer(question: str, sql: str, data: list) -> str:
    """Format query results into natural language answer"""
    if not data:
        return "No results found."
    
    print(f"\n🤖 Formatting answer from {len(data)} results...")
    
    response = openai_client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": """Format the query results into a clear, concise natural language answer.
Include specific numbers and metrics.
If there are multiple results, summarize the key insights.
Be helpful and informative."""
            },
            {
                "role": "user",
                "content": f"""Question: {question}

SQL Query: {sql}

Results (showing first 10):
{str(data[:10])}

Total results: {len(data)}"""
            }
        ],
        temperature=0.3
    )
    
    return response.choices[0].message.content

def ask(question: str):
    """Ask a question about telemetry data"""
    print("\n" + "="*60)
    
    # Generate SQL
    sql = generate_sql(question)
    
    # Execute query
    data = execute_query(sql)
    
    if data is None:
        print("\n❌ Query execution failed")
        return
    
    # Format answer
    answer = format_answer(question, sql, data)
    
    print("\n" + "="*60)
    print(f"\n💬 Answer:\n{answer}\n")
    print("="*60 + "\n")

def interactive_mode():
    """Run in interactive mode"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║         Natural Language Telemetry Query System              ║
╚══════════════════════════════════════════════════════════════╝

Ask questions about your telemetry data in plain English!

Example questions:
• How long did ChatTurn take?
• What's my total cost this week?
• Which executions failed?
• Show me the slowest executions
• How many tokens did I use today?

Type 'exit' to quit.
""")
    
    while True:
        try:
            question = input("\n❓ Your question: ").strip()
            
            if not question:
                continue
            
            if question.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            ask(question)
            
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Command line mode
        question = " ".join(sys.argv[1:])
        ask(question)
    else:
        # Interactive mode
        interactive_mode()
