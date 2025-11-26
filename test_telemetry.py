#!/usr/bin/env python3
"""
Quick test to verify telemetry upload to Supabase
Run this to see data appear in your dashboard!
"""

import os
import asyncio
from datetime import datetime

# Load from .env file
try:
    with open('.env', 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                if '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value
except FileNotFoundError:
    print("⚠️  .env file not found")

print("=" * 60)
print("AGORA TELEMETRY TEST")
print("=" * 60)

# Check environment variables
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("\n❌ Missing Supabase credentials!")
    print("   VITE_SUPABASE_URL:", "✓" if SUPABASE_URL else "✗")
    print("   VITE_SUPABASE_ANON_KEY:", "✓" if SUPABASE_KEY else "✗")
    exit(1)

print(f"\n✅ Supabase URL: {SUPABASE_URL}")
print(f"✅ Anon Key: {SUPABASE_KEY[:20]}...")

# Check if libraries are installed
try:
    from agora.agora_tracer import init_traceloop, agora_node, TracedAsyncFlow
    print("✅ Agora tracer available")
except ImportError as e:
    print(f"❌ Failed to import agora: {e}")
    print("\nInstall with: pip install traceloop-sdk supabase")
    exit(1)

try:
    from supabase import create_client
    print("✅ supabase-py available")
except ImportError:
    print("❌ supabase-py not installed")
    print("\nInstall with: pip install supabase")
    exit(1)

# Test database connection
print("\n" + "=" * 60)
print("TESTING DATABASE CONNECTION")
print("=" * 60)

try:
    client = create_client(SUPABASE_URL, SUPABASE_KEY)
    result = client.table("organizations").select("*").limit(1).execute()
    print(f"✅ Connected to Supabase! Found {len(result.data)} organizations")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    exit(1)

# Initialize traceloop
print("\n" + "=" * 60)
print("INITIALIZING TELEMETRY")
print("=" * 60)

os.environ["TRACELOOP_API_KEY"] = "test_key"

init_traceloop(
    app_name="telemetry_test",
    export_to_console=False,
    enable_cloud_upload=True,
    project_name="Telemetry Test"
)

# Create test workflow
print("\n" + "=" * 60)
print("RUNNING TEST WORKFLOW")
print("=" * 60)

@agora_node(name="Start")
async def start_node(shared):
    """Start node"""
    print("  ▶ Start node running...")
    shared["counter"] = 0
    await asyncio.sleep(0.2)
    return "process"

@agora_node(name="Process")
async def process_node(shared):
    """Process node"""
    shared["counter"] += 1
    print(f"  ▶ Process node running... (count: {shared['counter']})")
    await asyncio.sleep(0.3)

    if shared["counter"] < 3:
        return "process"
    return "finish"

@agora_node(name="Finish")
async def finish_node(shared):
    """Finish node"""
    print(f"  ▶ Finish node running... (final count: {shared['counter']})")
    shared["result"] = f"Completed {shared['counter']} iterations"
    await asyncio.sleep(0.2)
    return "END"

async def main():
    """Run the test workflow"""

    # Create flow
    flow = TracedAsyncFlow("TelemetryTest")

    # Add nodes
    flow.add_node(start_node)
    flow.add_node(process_node)
    flow.add_node(finish_node)

    # Add edges
    flow.add_edge(start_node, process_node, "process")
    flow.add_edge(process_node, process_node, "process")
    flow.add_edge(process_node, finish_node, "finish")

    # Run!
    print("\n🚀 Starting workflow execution...")
    start_time = datetime.now()

    result = await flow.start({"test_time": start_time.isoformat()})

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print(f"\n✅ Workflow completed in {duration:.2f}s")
    print(f"   Result: {result.get('result', 'No result')}")

    return result

# Run the test
if __name__ == "__main__":
    print("\nStarting test workflow...\n")
    result = asyncio.run(main())

    print("\n" + "=" * 60)
    print("TEST COMPLETE!")
    print("=" * 60)
    print("\n📊 Check your dashboard at /monitoring to see the execution!")
    print("   The data should appear within 5 seconds (auto-refresh)")
    print("\n🔍 Or check Supabase directly:")
    print(f"   {SUPABASE_URL.replace('https://', 'https://app.supabase.com/project/')}/editor")
    print("\n✅ Look in these tables:")
    print("   - projects")
    print("   - workflows")
    print("   - executions")
    print("   - node_executions")
    print("   - telemetry_spans")
