#!/usr/bin/env python3
"""
🔍 TELEMETRY EXPLORER - Interactive Demo
=========================================
This script helps you explore what's actually being captured by Agora's telemetry.

Run this to see:
1. What data is captured for each workflow execution
2. Token usage tracking in action
3. Vector DB query telemetry
4. Custom span creation
5. How to query and analyze the data

Usage:
    python explore_telemetry.py
"""

import asyncio
import os
import json
from datetime import datetime
from typing import Dict, Any

# Setup environment
os.environ.setdefault("OPENAI_API_KEY", "sk-your-key-here")
os.environ.setdefault("VITE_SUPABASE_URL", "https://your-project.supabase.co")
os.environ.setdefault("VITE_SUPABASE_ANON_KEY", "your-anon-key")

from agora.agora_tracer import init_agora, agora_node, TracedAsyncFlow
from opentelemetry import trace

# Initialize with telemetry enabled
init_agora(
    app_name="telemetry-explorer",
    project_name="Telemetry Demo",
    enable_cloud_upload=True,
    capture_io=True  # Capture inputs/outputs for debugging
)

tracer = trace.get_tracer(__name__)

print("\n" + "="*70)
print("🔍 AGORA TELEMETRY EXPLORER")
print("="*70)
print("\nThis demo will show you EXACTLY what telemetry data is captured.\n")


# ============================================================================
# DEMO 1: Basic Node Execution Telemetry
# ============================================================================

@agora_node(name="SimpleNode", capture_io=True)
async def simple_node(shared: Dict[str, Any]):
    """
    A simple node to show basic telemetry capture.
    
    What gets captured:
    - Node name
    - Start/end timestamps
    - Duration (prep, exec, post phases)
    - Input/output data (if capture_io=True)
    - Success/error status
    """
    print("\n📊 DEMO 1: Basic Node Execution")
    print("-" * 70)
    
    # Simulate some work
    await asyncio.sleep(0.5)
    
    result = f"Processed: {shared.get('input', 'no input')}"
    shared['result'] = result
    
    print(f"✅ Node executed successfully")
    print(f"   Input: {shared.get('input')}")
    print(f"   Output: {result}")
    
    return "llm_node"


# ============================================================================
# DEMO 2: LLM Call with Token Tracking
# ============================================================================

@agora_node(name="LLMNode", capture_io=True)
async def llm_node(shared: Dict[str, Any]):
    """
    LLM call with automatic token tracking.
    
    What gets captured:
    - Model name (gpt-4, gpt-3.5-turbo, etc.)
    - Tokens: prompt, completion, total
    - Estimated cost in USD
    - Temperature, max_tokens, etc.
    - Request/response content (if capture_io=True)
    """
    print("\n📊 DEMO 2: LLM Call with Token Tracking")
    print("-" * 70)
    
    # Check if we have a real API key
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if api_key == "sk-your-key-here" or not api_key:
        print("⚠️  No OpenAI API key found - using mock response")
        print("   Set OPENAI_API_KEY to see real token tracking")
        
        # Mock the telemetry data
        with tracer.start_as_current_span("llm.chat") as span:
            span.set_attribute("llm.model", "gpt-4")
            span.set_attribute("llm.temperature", "0.7")
            span.set_attribute("tokens.prompt", "50")
            span.set_attribute("tokens.completion", "100")
            span.set_attribute("tokens.total", "150")
            span.set_attribute("estimated_cost", "0.003")
            
            await asyncio.sleep(1)  # Simulate API call
            shared['llm_response'] = "This is a mock response (set OPENAI_API_KEY for real calls)"
            
        print("✅ Mock LLM call completed")
        print("   Model: gpt-4")
        print("   Tokens: 150 (50 prompt + 100 completion)")
        print("   Cost: $0.003")
    else:
        print("✅ Real OpenAI API key detected - making real call")
        
        from openai import AsyncOpenAI
        client = AsyncOpenAI()
        
        # This call is AUTOMATICALLY instrumented!
        # No manual tracking needed!
        response = await client.chat.completions.create(
            model="gpt-4o-mini",  # Cheaper for demo
            messages=[
                {"role": "user", "content": "Say 'Hello from Agora telemetry!' in exactly 5 words."}
            ],
            temperature=0.7,
            max_tokens=20
        )
        
        shared['llm_response'] = response.choices[0].message.content
        
        print("✅ Real LLM call completed")
        print(f"   Model: {response.model}")
        print(f"   Tokens: {response.usage.total_tokens} ({response.usage.prompt_tokens} prompt + {response.usage.completion_tokens} completion)")
        print(f"   Response: {shared['llm_response']}")
    
    return "vector_db_node"


# ============================================================================
# DEMO 3: Vector DB Query Telemetry
# ============================================================================

@agora_node(name="VectorDBNode", capture_io=True)
async def vector_db_node(shared: Dict[str, Any]):
    """
    Vector DB query with custom telemetry.
    
    What gets captured:
    - Query vector dimensions
    - Number of results
    - Top similarity score
    - Query latency
    - Collection name
    """
    print("\n📊 DEMO 3: Vector DB Query Telemetry")
    print("-" * 70)
    
    # Create a custom span for vector DB operation
    with tracer.start_as_current_span("vector_db.query") as span:
        # Add custom attributes
        span.set_attribute("vector_db.provider", "qdrant")
        span.set_attribute("vector_db.collection", "demo_collection")
        span.set_attribute("vector_db.limit", 5)
        span.set_attribute("query.dimension", 1536)
        
        # Simulate vector search
        await asyncio.sleep(0.3)
        
        # Mock results
        results = [
            {"text": "Result 1", "score": 0.95},
            {"text": "Result 2", "score": 0.87},
            {"text": "Result 3", "score": 0.72}
        ]
        
        # Track results
        span.set_attribute("results.count", len(results))
        span.set_attribute("results.top_score", results[0]['score'])
        
        shared['vector_results'] = results
        
    print("✅ Vector DB query completed")
    print(f"   Provider: Qdrant")
    print(f"   Collection: demo_collection")
    print(f"   Results: {len(results)} documents")
    print(f"   Top score: {results[0]['score']}")
    
    return "analytics_node"


# ============================================================================
# DEMO 4: Custom Metrics and Nested Spans
# ============================================================================

@agora_node(name="AnalyticsNode", capture_io=True)
async def analytics_node(shared: Dict[str, Any]):
    """
    Custom analytics with nested spans.
    
    What gets captured:
    - Parent-child span relationships
    - Custom business metrics
    - Multi-phase operations
    """
    print("\n📊 DEMO 4: Custom Metrics & Nested Spans")
    print("-" * 70)
    
    with tracer.start_as_current_span("analytics.process") as parent_span:
        parent_span.set_attribute("workflow.total_steps", 4)
        
        # Phase 1: Data validation
        with tracer.start_as_current_span("analytics.validate") as span:
            span.set_attribute("validation.input_size", len(str(shared)))
            span.set_attribute("validation.status", "passed")
            await asyncio.sleep(0.1)
            print("   ✓ Phase 1: Data validation")
        
        # Phase 2: Processing
        with tracer.start_as_current_span("analytics.compute") as span:
            span.set_attribute("compute.algorithm", "demo_algorithm")
            span.set_attribute("compute.iterations", 100)
            await asyncio.sleep(0.2)
            print("   ✓ Phase 2: Computation")
        
        # Phase 3: Results
        with tracer.start_as_current_span("analytics.finalize") as span:
            span.set_attribute("results.quality_score", 0.95)
            span.set_attribute("results.confidence", 0.88)
            await asyncio.sleep(0.1)
            print("   ✓ Phase 3: Finalization")
    
    print("✅ Analytics completed with nested telemetry")
    
    return None  # End of workflow


# ============================================================================
# DEMO 5: Query and Analyze Telemetry Data
# ============================================================================

async def analyze_telemetry():
    """
    Query the telemetry data that was just captured.
    """
    print("\n" + "="*70)
    print("📈 ANALYZING CAPTURED TELEMETRY")
    print("="*70)
    
    # Check if we can connect to Supabase
    supabase_url = os.environ.get("VITE_SUPABASE_URL", "")
    if supabase_url == "https://your-project.supabase.co" or not supabase_url:
        print("\n⚠️  Supabase not configured - showing what WOULD be captured:")
        print("\n" + "-"*70)
        print("TELEMETRY DATA STRUCTURE:")
        print("-"*70)
        
        example_data = {
            "executions": {
                "id": "uuid-123",
                "workflow_id": "workflow-uuid",
                "status": "success",
                "started_at": datetime.now().isoformat(),
                "duration_ms": 2500,
                "input_data": {"input": "test data"},
                "output_data": {"result": "processed"}
            },
            "node_executions": [
                {
                    "node_id": "SimpleNode",
                    "status": "success",
                    "prep_duration_ms": 5,
                    "exec_duration_ms": 500,
                    "post_duration_ms": 3
                },
                {
                    "node_id": "LLMNode",
                    "status": "success",
                    "exec_duration_ms": 1200
                }
            ],
            "telemetry_spans": [
                {
                    "name": "llm.chat",
                    "attributes": {
                        "llm.model": "gpt-4o-mini",
                        "tokens.prompt": 50,
                        "tokens.completion": 100,
                        "tokens.total": 150,
                        "estimated_cost": 0.003
                    }
                },
                {
                    "name": "vector_db.query",
                    "attributes": {
                        "vector_db.provider": "qdrant",
                        "results.count": 3,
                        "results.top_score": 0.95
                    }
                }
            ]
        }
        
        print(json.dumps(example_data, indent=2))
        
        print("\n" + "-"*70)
        print("TO SEE REAL DATA:")
        print("-"*70)
        print("1. Set your Supabase credentials:")
        print("   export VITE_SUPABASE_URL='https://your-project.supabase.co'")
        print("   export VITE_SUPABASE_ANON_KEY='your-anon-key'")
        print("\n2. Run this script again")
        print("\n3. View in Supabase dashboard:")
        print("   - Table: executions (workflow runs)")
        print("   - Table: node_executions (individual nodes)")
        print("   - Table: telemetry_spans (detailed metrics)")
        print("\n4. Or view in Agora frontend:")
        print("   http://localhost:5173/monitoring")
        
    else:
        print("\n✅ Supabase configured - querying real data...")
        
        try:
            from supabase import create_client
            
            client = create_client(
                os.environ['VITE_SUPABASE_URL'],
                os.environ['VITE_SUPABASE_ANON_KEY']
            )
            
            # Query recent executions
            result = client.table('executions').select('*').order('started_at', desc=True).limit(5).execute()
            
            print(f"\n📊 Recent Executions: {len(result.data)}")
            for exec in result.data:
                print(f"   - {exec['id']}: {exec['status']} ({exec.get('duration_ms', 0)}ms)")
            
            # Query telemetry spans with token data
            result = client.table('telemetry_spans').select('*').limit(10).execute()
            
            print(f"\n📊 Recent Telemetry Spans: {len(result.data)}")
            for span in result.data:
                attrs = span.get('attributes', {})
                if 'llm.usage.total_tokens' in attrs or 'tokens.total' in attrs:
                    tokens = attrs.get('tokens.total') or attrs.get('llm.usage.total_tokens')
                    cost = attrs.get('estimated_cost', 0)
                    print(f"   - {span['name']}: {tokens} tokens, ${cost}")
                    
        except Exception as e:
            print(f"❌ Error querying Supabase: {e}")
            print("   Make sure your credentials are correct")


# ============================================================================
# MAIN WORKFLOW
# ============================================================================

async def main():
    """
    Run the telemetry exploration demo.
    """
    print("\n🚀 Starting Telemetry Exploration Workflow...\n")
    
    # Create workflow
    flow = TracedAsyncFlow("TelemetryExplorer")
    flow.start(simple_node)
    
    # Define workflow graph
    simple_node - "llm_node" >> llm_node
    llm_node - "vector_db_node" >> vector_db_node
    vector_db_node - "analytics_node" >> analytics_node
    
    # Execute workflow
    shared = {
        "input": "Hello, Agora!",
        "user_id": "demo_user_123"
    }
    
    await flow.run_async(shared)
    
    print("\n" + "="*70)
    print("✅ WORKFLOW COMPLETED")
    print("="*70)
    print(f"\nFinal Result: {shared.get('result')}")
    print(f"LLM Response: {shared.get('llm_response')}")
    print(f"Vector Results: {len(shared.get('vector_results', []))} documents")
    
    # Analyze the telemetry
    await analyze_telemetry()
    
    print("\n" + "="*70)
    print("🎓 WHAT YOU LEARNED")
    print("="*70)
    print("""
1. ✅ Node execution is automatically tracked (timing, status, retries)
2. ✅ LLM calls capture tokens and costs automatically
3. ✅ Custom spans let you track anything (vector DB, APIs, etc.)
4. ✅ Nested spans show parent-child relationships
5. ✅ All data goes to Supabase for querying and analytics

NEXT STEPS:
- Check your Supabase dashboard to see the data
- Visit http://localhost:5173/monitoring for visual analytics
- Try modifying this script to track your own operations
- Add custom attributes to spans for your specific use case
    """)


if __name__ == "__main__":
    asyncio.run(main())
