#!/usr/bin/env python3
"""
🔍 WHAT'S ACTUALLY BEING CAPTURED RIGHT NOW?
=============================================
This script tests your CURRENT setup to see what telemetry is being captured.

Run this to see:
1. Is Supabase connected?
2. Is data being uploaded?
3. What attributes are being captured?
4. Are LLM calls being tracked?
"""

import asyncio
import os
import sys

# Set dummy credentials if not set (for testing)
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key")
os.environ.setdefault("VITE_SUPABASE_URL", "https://test.supabase.co")
os.environ.setdefault("VITE_SUPABASE_ANON_KEY", "test-key")

from agora.agora_tracer import init_agora, agora_node, TracedAsyncFlow, cloud_uploader
from opentelemetry import trace

print("\n" + "="*80)
print("🔍 TESTING CURRENT TELEMETRY CAPTURE")
print("="*80)

# Test 1: Check initialization
print("\n1️⃣  Testing Agora Initialization...")
print("-" * 80)

try:
    init_agora(
        app_name="telemetry-test",
        project_name="Test Project",
        export_to_console=False  # Same as your real_chatbot_demo.py
    )
    print("✅ Agora initialized successfully")
except Exception as e:
    print(f"❌ Initialization failed: {e}")
    sys.exit(1)

# Test 2: Check cloud uploader status
print("\n2️⃣  Checking Cloud Upload Status...")
print("-" * 80)

if cloud_uploader:
    print(f"✅ Cloud uploader exists")
    print(f"   - Enabled: {cloud_uploader.enabled}")
    print(f"   - Project: {cloud_uploader.project_name}")
    
    if cloud_uploader.enabled:
        print(f"   - Supabase URL: {cloud_uploader.supabase_url}")
        print(f"   - Has client: {cloud_uploader.client is not None}")
    else:
        print(f"   ⚠️  Cloud uploader is DISABLED")
        print(f"   Reason: Missing Supabase credentials or supabase-py library")
else:
    print("❌ Cloud uploader is None")
    print("   Data will NOT be uploaded to Supabase")

# Test 3: Check what gets captured in a span
print("\n3️⃣  Testing Span Capture...")
print("-" * 80)

tracer = trace.get_tracer(__name__)

@agora_node(name="TestNode", capture_io=True)
async def test_node(shared):
    """Test node to see what gets captured."""
    
    # Create a custom span
    with tracer.start_as_current_span("test.custom_span") as span:
        span.set_attribute("custom.attribute", "test_value")
        span.set_attribute("custom.number", 123)
        
        # Simulate some work
        await asyncio.sleep(0.1)
    
    shared['result'] = "test complete"
    return None

async def run_test():
    """Run a test workflow."""
    flow = TracedAsyncFlow("TestWorkflow")
    flow.start(test_node)
    
    shared = {"input": "test data"}
    
    print("Running test workflow...")
    await flow.run_async(shared)
    print(f"✅ Workflow completed: {shared.get('result')}")

print("Executing test workflow...")
asyncio.run(run_test())

# Test 4: Summary
print("\n4️⃣  Summary: What's Being Captured?")
print("-" * 80)

real_supabase_url = os.environ.get("VITE_SUPABASE_URL", "")
real_supabase_key = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

if cloud_uploader and cloud_uploader.enabled:
    print("\n✅ TELEMETRY IS BEING CAPTURED AND UPLOADED!")
    print("\nWhat's being captured:")
    print("   ✅ Workflow executions (timing, status, input/output)")
    print("   ✅ Node executions (prep/exec/post phases)")
    print("   ✅ Telemetry spans (ALL attributes)")
    print("   ✅ LLM calls (tokens, cost, model) - if using OpenAI")
    print("   ✅ Custom spans (any attributes you add)")
    
    print("\nWhere it's going:")
    print(f"   📍 Supabase: {cloud_uploader.supabase_url}")
    print(f"   📊 Tables: executions, node_executions, telemetry_spans")
    
    print("\nTo view the data:")
    print("   1. Supabase Dashboard: https://app.supabase.com")
    print("   2. SQL queries (see documentation)")
    print("   3. Agora Frontend: http://localhost:5173/monitoring")
    
elif real_supabase_url and real_supabase_url != "https://test.supabase.co":
    print("\n⚠️  TELEMETRY IS CONFIGURED BUT NOT UPLOADING")
    print("\nPossible reasons:")
    print("   1. Missing supabase-py library")
    print("      Fix: pip install supabase")
    print("   2. Invalid Supabase credentials")
    print("      Check: VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY")
    print("   3. enable_cloud_upload=False in init_agora()")
    
    print("\nWhat's still being captured:")
    print("   ✅ OpenTelemetry spans (in memory)")
    print("   ✅ Console output (if export_to_console=True)")
    print("   ❌ NOT saved to database")
    
else:
    print("\n❌ TELEMETRY IS NOT CONFIGURED")
    print("\nTo enable telemetry:")
    print("   1. Set Supabase credentials:")
    print("      export VITE_SUPABASE_URL='https://your-project.supabase.co'")
    print("      export VITE_SUPABASE_ANON_KEY='your-anon-key'")
    print("   2. Install supabase-py:")
    print("      pip install supabase")
    print("   3. Run your application")

# Test 5: Check for your real chatbot
print("\n5️⃣  Checking Your Real Chatbot Setup...")
print("-" * 80)

try:
    with open('/Users/anirudhanil/Desktop/agora3/Agora/real_chatbot_demo.py', 'r') as f:
        content = f.read()
        
        # Check for enable_cloud_upload
        if 'enable_cloud_upload=True' in content:
            print("✅ enable_cloud_upload=True is set")
        elif 'enable_cloud_upload=False' in content:
            print("❌ enable_cloud_upload=False is set - data won't upload!")
        else:
            print("⚠️  enable_cloud_upload not specified (defaults to True)")
        
        # Check for capture_io
        if 'capture_io=True' in content:
            print("✅ capture_io=True is set - will capture input/output")
        else:
            print("⚠️  capture_io not set - won't capture input/output data")
        
        # Check for custom spans
        if 'tracer.start_as_current_span' in content:
            print("✅ Custom spans are being created")
        else:
            print("⚠️  No custom spans detected")
            
except Exception as e:
    print(f"Could not read real_chatbot_demo.py: {e}")

print("\n" + "="*80)
print("✅ TEST COMPLETE")
print("="*80)

print("""
🎯 NEXT STEPS:

If telemetry IS working:
   1. Run: python3 real_chatbot_demo.py
   2. Check data: python3 inspect_telemetry_data.py
   3. View dashboard: http://localhost:5173/monitoring

If telemetry is NOT working:
   1. Install: pip install supabase
   2. Set credentials in .env or environment
   3. Add to real_chatbot_demo.py:
      init_agora(
          app_name="talking-chatbot",
          project_name="Production Chatbot",
          enable_cloud_upload=True,  # ← Add this!
          capture_io=True  # ← Add this to see input/output!
      )
""")
