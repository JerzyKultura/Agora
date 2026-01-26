#!/usr/bin/env python3
"""
📊 TELEMETRY DATA INSPECTOR
============================
This script shows you the ACTUAL data structure captured by Agora.
Run this after executing your chatbot to see real telemetry data.

Usage:
    python3 inspect_telemetry_data.py
"""

import os
import json
from supabase import create_client
from datetime import datetime, timedelta

# Configuration
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or SUPABASE_URL == "https://your-project.supabase.co":
    print("❌ Please set your Supabase credentials:")
    print("   export VITE_SUPABASE_URL='https://your-project.supabase.co'")
    print("   export VITE_SUPABASE_ANON_KEY='your-anon-key'")
    exit(1)

client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("\n" + "="*80)
print("📊 TELEMETRY DATA INSPECTOR")
print("="*80)
print("\nThis shows you the ACTUAL data structure captured by Agora.\n")


def print_json(data, title=""):
    """Pretty print JSON data."""
    if title:
        print(f"\n{title}")
        print("-" * 80)
    print(json.dumps(data, indent=2, default=str))


def inspect_execution_data():
    """Show the structure of execution data."""
    print("\n" + "="*80)
    print("1️⃣  EXECUTION DATA (Workflow Level)")
    print("="*80)
    
    try:
        result = client.table('executions').select(
            '*'
        ).order('started_at', desc=True).limit(1).execute()
        
        if not result.data:
            print("   No executions found. Run a workflow first!")
            return None
        
        exec_data = result.data[0]
        
        print("\n📋 Fields Captured:")
        print(f"   - id: {exec_data['id']}")
        print(f"   - workflow_id: {exec_data['workflow_id']}")
        print(f"   - status: {exec_data['status']}")
        print(f"   - started_at: {exec_data['started_at']}")
        print(f"   - completed_at: {exec_data.get('completed_at', 'N/A')}")
        print(f"   - duration_ms: {exec_data.get('duration_ms', 'N/A')}")
        print(f"   - error_message: {exec_data.get('error_message', 'None')}")
        
        if exec_data.get('input_data'):
            print(f"\n📥 Input Data:")
            print_json(exec_data['input_data'])
        
        if exec_data.get('output_data'):
            print(f"\n📤 Output Data:")
            print_json(exec_data['output_data'])
        
        return exec_data['id']
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def inspect_node_execution_data(execution_id):
    """Show the structure of node execution data."""
    print("\n" + "="*80)
    print("2️⃣  NODE EXECUTION DATA (Node Level)")
    print("="*80)
    
    try:
        result = client.table('node_executions').select(
            '*'
        ).eq('execution_id', execution_id).execute()
        
        if not result.data:
            print("   No node executions found.")
            return
        
        for i, node_exec in enumerate(result.data, 1):
            print(f"\n📍 Node {i}:")
            print(f"   - node_id: {node_exec['node_id']}")
            print(f"   - status: {node_exec['status']}")
            print(f"   - started_at: {node_exec['started_at']}")
            print(f"   - completed_at: {node_exec.get('completed_at', 'N/A')}")
            
            print(f"\n   ⏱️  Phase Timings:")
            print(f"      - prep_duration_ms: {node_exec.get('prep_duration_ms', 'N/A')}")
            print(f"      - exec_duration_ms: {node_exec.get('exec_duration_ms', 'N/A')}")
            print(f"      - post_duration_ms: {node_exec.get('post_duration_ms', 'N/A')}")
            
            if node_exec.get('error_message'):
                print(f"\n   ❌ Error: {node_exec['error_message']}")
            
            if node_exec.get('retry_count', 0) > 0:
                print(f"\n   🔄 Retries: {node_exec['retry_count']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def inspect_telemetry_spans(execution_id):
    """Show the structure of telemetry spans - THE DETAILED METRICS!"""
    print("\n" + "="*80)
    print("3️⃣  TELEMETRY SPANS (Detailed Metrics)")
    print("="*80)
    print("\n⭐ This is where ALL the detailed metrics live!\n")
    
    try:
        result = client.table('telemetry_spans').select(
            '*'
        ).eq('execution_id', execution_id).execute()
        
        if not result.data:
            print("   No telemetry spans found.")
            return
        
        # Group spans by type
        llm_spans = []
        custom_spans = []
        agora_spans = []
        
        for span in result.data:
            attrs = span.get('attributes', {})
            
            if 'llm.provider' in attrs or 'tokens.total' in attrs:
                llm_spans.append(span)
            elif 'agora.node' in attrs:
                agora_spans.append(span)
            else:
                custom_spans.append(span)
        
        # Show LLM spans
        if llm_spans:
            print("🤖 LLM SPANS (Automatic Token Tracking)")
            print("-" * 80)
            
            for i, span in enumerate(llm_spans, 1):
                attrs = span['attributes']
                
                print(f"\n   LLM Call {i}:")
                print(f"   - Span Name: {span['name']}")
                print(f"   - Duration: {span.get('duration_ms', 'N/A')}ms")
                
                print(f"\n   📊 LLM Attributes:")
                
                # Provider info
                if 'llm.provider' in attrs:
                    print(f"      Provider: {attrs['llm.provider']}")
                if 'llm.model' in attrs:
                    print(f"      Model: {attrs['llm.model']}")
                if 'llm.temperature' in attrs:
                    print(f"      Temperature: {attrs['llm.temperature']}")
                
                # Token metrics
                print(f"\n   💰 Token Metrics:")
                if 'tokens.prompt' in attrs:
                    print(f"      Prompt Tokens: {attrs['tokens.prompt']}")
                if 'tokens.completion' in attrs:
                    print(f"      Completion Tokens: {attrs['tokens.completion']}")
                if 'tokens.total' in attrs:
                    print(f"      Total Tokens: {attrs['tokens.total']}")
                if 'estimated_cost' in attrs:
                    print(f"      Estimated Cost: ${attrs['estimated_cost']}")
                
                # Performance
                if 'llm.api.latency_ms' in attrs:
                    print(f"\n   ⚡ Performance:")
                    print(f"      API Latency: {attrs['llm.api.latency_ms']}ms")
                
                # Content preview
                if 'prompt.preview' in attrs:
                    print(f"\n   📝 Content Preview:")
                    print(f"      Prompt: {attrs['prompt.preview'][:100]}...")
                if 'response.preview' in attrs:
                    print(f"      Response: {attrs['response.preview'][:100]}...")
                
                # Show ALL attributes
                print(f"\n   📋 ALL Attributes ({len(attrs)} total):")
                for key in sorted(attrs.keys()):
                    value = attrs[key]
                    if len(str(value)) > 50:
                        value = str(value)[:50] + "..."
                    print(f"      {key}: {value}")
        
        # Show custom spans
        if custom_spans:
            print("\n\n🔧 CUSTOM SPANS (Your Custom Tracking)")
            print("-" * 80)
            
            for i, span in enumerate(custom_spans, 1):
                attrs = span['attributes']
                
                print(f"\n   Custom Span {i}:")
                print(f"   - Name: {span['name']}")
                print(f"   - Duration: {span.get('duration_ms', 'N/A')}ms")
                
                # Detect span type
                if 'vector_db.provider' in attrs:
                    print(f"\n   🔍 Vector DB Attributes:")
                    print(f"      Provider: {attrs.get('vector_db.provider')}")
                    print(f"      Collection: {attrs.get('vector_db.collection')}")
                    print(f"      Results Count: {attrs.get('results.count')}")
                    print(f"      Top Score: {attrs.get('results.top_score')}")
                
                elif 'memory.provider' in attrs:
                    print(f"\n   🧠 Memory Attributes:")
                    print(f"      Provider: {attrs.get('memory.provider')}")
                    print(f"      User ID: {attrs.get('memory.user_id')}")
                    print(f"      Results Count: {attrs.get('memory.results_count')}")
                
                else:
                    print(f"\n   📋 All Attributes:")
                    for key, value in attrs.items():
                        print(f"      {key}: {value}")
        
        # Show Agora internal spans
        if agora_spans:
            print("\n\n⚙️  AGORA INTERNAL SPANS (Framework Tracking)")
            print("-" * 80)
            print(f"   Found {len(agora_spans)} internal spans")
            print(f"   (These track prep/exec/post phases)")
        
        # Summary
        print("\n\n📊 SUMMARY")
        print("-" * 80)
        print(f"   Total Spans: {len(result.data)}")
        print(f"   - LLM Spans: {len(llm_spans)}")
        print(f"   - Custom Spans: {len(custom_spans)}")
        print(f"   - Agora Internal: {len(agora_spans)}")
        
        # Calculate totals
        total_tokens = 0
        total_cost = 0
        
        for span in llm_spans:
            attrs = span['attributes']
            tokens = attrs.get('tokens.total')
            cost = attrs.get('estimated_cost')
            
            if tokens:
                total_tokens += int(tokens)
            if cost:
                total_cost += float(cost)
        
        if total_tokens > 0:
            print(f"\n   💰 LLM Usage:")
            print(f"      Total Tokens: {total_tokens:,}")
            print(f"      Total Cost: ${total_cost:.4f}")
        
    except Exception as e:
        print(f"❌ Error: {e}")


def show_attribute_examples():
    """Show examples of all possible attributes."""
    print("\n" + "="*80)
    print("4️⃣  EXAMPLE ATTRIBUTES (What You Can Track)")
    print("="*80)
    
    examples = {
        "LLM Attributes (Automatic)": {
            "llm.provider": "openai",
            "llm.model": "gpt-4",
            "llm.temperature": "0.7",
            "tokens.prompt": "800",
            "tokens.completion": "450",
            "tokens.total": "1250",
            "estimated_cost": "0.025"
        },
        "Vector DB Attributes (Custom)": {
            "vector_db.provider": "qdrant",
            "vector_db.collection": "chat_history",
            "query.dimension": "1536",
            "results.count": "5",
            "results.top_score": "0.95"
        },
        "Memory Attributes (Custom)": {
            "memory.provider": "mem0",
            "memory.user_id": "user_123",
            "memory.results_count": "3"
        },
        "API Attributes (Custom)": {
            "http.method": "POST",
            "http.status_code": "200",
            "api.latency_ms": "123"
        },
        "Business Metrics (Custom)": {
            "business.user_tier": "premium",
            "business.feature_flag": "new_ui",
            "quality.score": "0.95"
        }
    }
    
    for category, attrs in examples.items():
        print(f"\n{category}:")
        print_json(attrs)


def main():
    """Run the inspector."""
    
    # 1. Inspect execution data
    execution_id = inspect_execution_data()
    
    if not execution_id:
        print("\n⚠️  No execution data found.")
        print("   Run a workflow first:")
        print("   python3 real_chatbot_demo.py")
        return
    
    # 2. Inspect node executions
    inspect_node_execution_data(execution_id)
    
    # 3. Inspect telemetry spans (THE IMPORTANT PART!)
    inspect_telemetry_spans(execution_id)
    
    # 4. Show examples
    show_attribute_examples()
    
    print("\n" + "="*80)
    print("✅ INSPECTION COMPLETE")
    print("="*80)
    print("""
🎓 KEY TAKEAWAYS:

1. Tokens are just ONE attribute among many!
2. The `telemetry_spans.attributes` field contains ALL metrics
3. You can add custom attributes for anything you want to track
4. LLM metrics (tokens, cost) are captured automatically
5. Custom spans let you track vector DB, memory, APIs, etc.

📊 To see this data visually:
   - Supabase Dashboard: https://app.supabase.com
   - Agora Frontend: http://localhost:5173/monitoring
   - SQL Queries: See the documentation

🔍 To track custom metrics:
   from opentelemetry import trace
   
   with tracer.start_as_current_span("my_operation") as span:
       span.set_attribute("my_metric", "my_value")
    """)


if __name__ == "__main__":
    main()
