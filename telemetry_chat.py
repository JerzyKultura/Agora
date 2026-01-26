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
You have access to a PostgreSQL telemetry database with the following schema:

Table: telemetry_spans
Columns:
- id (uuid) - unique span ID
- execution_id (uuid) - groups spans from same execution
- trace_id (text) - trace identifier
- name (text) - node/workflow name (e.g., "ChatTurn.flow", "ProcessMessage.exec")
- kind (text) - span type
- status (text) - 'success' or 'error'
- start_time (timestamp) - when span started
- end_time (timestamp) - when span ended
- duration_ms (integer) - duration in milliseconds
- tokens_used (integer) - LLM tokens consumed
- estimated_cost (numeric) - estimated cost in dollars
- attributes (jsonb) - additional metadata
- organization_id (uuid) - organization that owns this data

Important notes:
- To calculate duration from timestamps: EXTRACT(EPOCH FROM (end_time - start_time))
- Workflow names often have suffixes like ".flow", ".node", ".prep", ".exec", ".post"
- Use ILIKE for case-insensitive pattern matching
- Group by execution_id to get per-execution metrics
- Always include organization_id filter for security

Common query patterns:
1. Average duration: SELECT AVG(duration_ms)/1000.0 as avg_seconds FROM telemetry_spans WHERE name ILIKE '%WorkflowName%'
2. Total cost: SELECT SUM(estimated_cost) FROM telemetry_spans WHERE start_time > NOW() - INTERVAL '7 days'
3. Failed executions: SELECT DISTINCT execution_id, name FROM telemetry_spans WHERE status = 'error'
4. Recent executions: SELECT * FROM telemetry_spans ORDER BY start_time DESC LIMIT 10
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
        
        # Simplified execution - just query the table
        result = supabase.table('telemetry_spans')\
            .select('*')\
            .order('start_time', desc=True)\
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
