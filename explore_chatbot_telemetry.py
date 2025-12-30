#!/usr/bin/env python3
"""
🔍 REAL CHATBOT TELEMETRY EXPLORER
===================================
Explore telemetry data from your actual chatbot with Mem0 + Qdrant.

This shows you:
1. What's being tracked in your real_chatbot_demo.py
2. How to query token usage
3. How to find expensive operations
4. How to debug performance issues

Usage:
    # First, run your chatbot to generate some data:
    python real_chatbot_demo.py
    
    # Then explore the telemetry:
    python explore_chatbot_telemetry.py
"""

import os
import json
from datetime import datetime, timedelta
from supabase import create_client

# ============================================================================
# CONFIGURATION
# ============================================================================

SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or SUPABASE_URL == "https://your-project.supabase.co":
    print("❌ Please set your Supabase credentials:")
    print("   export VITE_SUPABASE_URL='https://your-project.supabase.co'")
    print("   export VITE_SUPABASE_ANON_KEY='your-anon-key'")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*80)
print("🔍 CHATBOT TELEMETRY EXPLORER")
print("="*80)


# ============================================================================
# QUERY 1: Recent Workflow Executions
# ============================================================================

def show_recent_executions(limit=10):
    """Show recent workflow executions."""
    print(f"\n📊 RECENT WORKFLOW EXECUTIONS (last {limit})")
    print("-"*80)
    
    try:
        result = client.table('executions').select(
            'id, workflow_id, status, started_at, completed_at, duration_ms, workflows(name)'
        ).order('started_at', desc=True).limit(limit).execute()
        
        if not result.data:
            print("   No executions found. Run real_chatbot_demo.py first!")
            return
        
        for i, exec in enumerate(result.data, 1):
            workflow_name = exec.get('workflows', {}).get('name', 'Unknown')
            status = exec['status']
            duration = exec.get('duration_ms', 0)
            started = exec['started_at']
            
            status_emoji = "✅" if status == "success" else "❌"
            
            print(f"{i}. {status_emoji} {workflow_name}")
            print(f"   ID: {exec['id']}")
            print(f"   Status: {status}")
            print(f"   Duration: {duration}ms ({duration/1000:.2f}s)")
            print(f"   Started: {started}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# QUERY 2: Token Usage Analysis
# ============================================================================

def show_token_usage(days=7):
    """Show token usage over the last N days."""
    print(f"\n💰 TOKEN USAGE (last {days} days)")
    print("-"*80)
    
    try:
        # Query telemetry spans with token data
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        result = client.table('telemetry_spans').select(
            'id, name, attributes, start_time, duration_ms, executions(workflows(name))'
        ).gte('start_time', start_date).execute()
        
        if not result.data:
            print("   No telemetry data found.")
            return
        
        # Analyze token usage
        total_tokens = 0
        total_cost = 0
        llm_calls = []
        
        for span in result.data:
            attrs = span.get('attributes', {})
            
            # Check for token data
            tokens = (attrs.get('llm.usage.total_tokens') or 
                     attrs.get('tokens.total') or 
                     attrs.get('traceloop.usage.total_tokens'))
            
            cost = (attrs.get('estimated_cost') or 
                   attrs.get('traceloop.cost.usd') or 
                   attrs.get('llm.usage.cost'))
            
            if tokens:
                tokens = int(tokens)
                total_tokens += tokens
                
                if cost:
                    cost = float(cost)
                    total_cost += cost
                
                llm_calls.append({
                    'name': span['name'],
                    'tokens': tokens,
                    'cost': cost or 0,
                    'duration_ms': span.get('duration_ms', 0),
                    'model': attrs.get('llm.model', 'unknown'),
                    'workflow': span.get('executions', {}).get('workflows', {}).get('name', 'Unknown')
                })
        
        print(f"Total LLM Calls: {len(llm_calls)}")
        print(f"Total Tokens: {total_tokens:,}")
        print(f"Total Cost: ${total_cost:.4f}")
        print(f"Average Tokens/Call: {total_tokens/len(llm_calls):.0f}" if llm_calls else "N/A")
        
        if llm_calls:
            print(f"\n📈 Top 5 Most Expensive Calls:")
            llm_calls.sort(key=lambda x: x['cost'], reverse=True)
            for i, call in enumerate(llm_calls[:5], 1):
                print(f"{i}. {call['name']}")
                print(f"   Workflow: {call['workflow']}")
                print(f"   Model: {call['model']}")
                print(f"   Tokens: {call['tokens']:,}")
                print(f"   Cost: ${call['cost']:.4f}")
                print(f"   Duration: {call['duration_ms']}ms")
                print()
                
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# QUERY 3: Performance Bottlenecks
# ============================================================================

def show_performance_analysis():
    """Find slow operations."""
    print(f"\n⚡ PERFORMANCE ANALYSIS")
    print("-"*80)
    
    try:
        # Get all node executions
        result = client.table('node_executions').select(
            'id, node_id, exec_duration_ms, nodes(name), executions(workflows(name))'
        ).order('exec_duration_ms', desc=True).limit(10).execute()
        
        if not result.data:
            print("   No node execution data found.")
            return
        
        print("🐌 Slowest Node Executions:")
        for i, node_exec in enumerate(result.data, 1):
            node_name = node_exec.get('nodes', {}).get('name', 'Unknown')
            workflow_name = node_exec.get('executions', {}).get('workflows', {}).get('name', 'Unknown')
            duration = node_exec.get('exec_duration_ms', 0)
            
            print(f"{i}. {node_name} ({workflow_name})")
            print(f"   Duration: {duration}ms ({duration/1000:.2f}s)")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# QUERY 4: Custom Span Analysis (Vector DB, Mem0, etc.)
# ============================================================================

def show_custom_spans():
    """Show custom telemetry spans (vector DB, memory, etc.)."""
    print(f"\n🔧 CUSTOM TELEMETRY SPANS")
    print("-"*80)
    
    try:
        result = client.table('telemetry_spans').select(
            'id, name, attributes, duration_ms, start_time'
        ).order('start_time', desc=True).limit(20).execute()
        
        if not result.data:
            print("   No telemetry spans found.")
            return
        
        # Group by span type
        span_types = {}
        for span in result.data:
            name = span['name']
            if name not in span_types:
                span_types[name] = []
            span_types[name].append(span)
        
        print(f"Found {len(span_types)} different span types:\n")
        
        for span_type, spans in span_types.items():
            avg_duration = sum(s.get('duration_ms', 0) for s in spans) / len(spans)
            
            print(f"📍 {span_type}")
            print(f"   Count: {len(spans)}")
            print(f"   Avg Duration: {avg_duration:.0f}ms")
            
            # Show interesting attributes
            if spans[0].get('attributes'):
                attrs = spans[0]['attributes']
                interesting = {}
                
                for key, value in attrs.items():
                    if any(keyword in key.lower() for keyword in ['model', 'provider', 'count', 'score', 'tokens']):
                        interesting[key] = value
                
                if interesting:
                    print(f"   Attributes: {json.dumps(interesting, indent=6)}")
            
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# QUERY 5: Workflow Success Rate
# ============================================================================

def show_success_rate(days=7):
    """Show workflow success rate."""
    print(f"\n📊 WORKFLOW SUCCESS RATE (last {days} days)")
    print("-"*80)
    
    try:
        start_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        result = client.table('executions').select(
            'id, status, workflows(name)'
        ).gte('started_at', start_date).execute()
        
        if not result.data:
            print("   No execution data found.")
            return
        
        # Calculate success rate by workflow
        workflow_stats = {}
        
        for exec in result.data:
            workflow_name = exec.get('workflows', {}).get('name', 'Unknown')
            status = exec['status']
            
            if workflow_name not in workflow_stats:
                workflow_stats[workflow_name] = {'success': 0, 'error': 0, 'total': 0}
            
            workflow_stats[workflow_name]['total'] += 1
            if status == 'success':
                workflow_stats[workflow_name]['success'] += 1
            elif status == 'error':
                workflow_stats[workflow_name]['error'] += 1
        
        for workflow, stats in workflow_stats.items():
            success_rate = (stats['success'] / stats['total'] * 100) if stats['total'] > 0 else 0
            
            print(f"📈 {workflow}")
            print(f"   Total Runs: {stats['total']}")
            print(f"   Success: {stats['success']} ({success_rate:.1f}%)")
            print(f"   Errors: {stats['error']}")
            print()
            
    except Exception as e:
        print(f"❌ Error: {e}")


# ============================================================================
# MAIN
# ============================================================================

def main():
    """Run all telemetry queries."""
    
    # 1. Recent executions
    show_recent_executions(limit=5)
    
    # 2. Token usage
    show_token_usage(days=7)
    
    # 3. Performance analysis
    show_performance_analysis()
    
    # 4. Custom spans
    show_custom_spans()
    
    # 5. Success rate
    show_success_rate(days=7)
    
    print("\n" + "="*80)
    print("✅ TELEMETRY EXPLORATION COMPLETE")
    print("="*80)
    print("""
💡 TIPS:
1. Run real_chatbot_demo.py multiple times to generate more data
2. Check the Agora dashboard at http://localhost:5173/monitoring
3. Query Supabase directly for custom analysis
4. Add custom spans to track your specific operations

📚 USEFUL SQL QUERIES:

-- Total tokens by workflow:
SELECT 
    w.name,
    SUM((ts.attributes->>'tokens.total')::int) as total_tokens
FROM telemetry_spans ts
JOIN executions e ON e.id = ts.execution_id
JOIN workflows w ON w.id = e.workflow_id
WHERE ts.attributes ? 'tokens.total'
GROUP BY w.name;

-- Average execution time by workflow:
SELECT 
    w.name,
    AVG(e.duration_ms) as avg_duration_ms
FROM executions e
JOIN workflows w ON w.id = e.workflow_id
GROUP BY w.name;
    """)


if __name__ == "__main__":
    main()
