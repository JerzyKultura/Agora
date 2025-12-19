#!/usr/bin/env env python3
"""
Simple Agora Workflow Demo

This demonstrates how to use the @agora_node decorator with direct Supabase upload
to send telemetry to your deployed Agora Cloud platform.

Setup:
1. Get your Supabase credentials from your project's .env file
2. Set the environment variables:
   export VITE_SUPABASE_URL="https://your-project.supabase.co"
   export VITE_SUPABASE_ANON_KEY="eyJhbGci..."
3. Run this script: python demo_workflow.py
"""

import asyncio
import os
from dotenv import load_dotenv

# Load env vars from .env file
load_dotenv()

from agora.agora_tracer import (
    TracedAsyncFlow,
    init_agora,
    agora_node,
)

# Check for Supabase configuration
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️  Supabase credentials not found!")
    print("Set them with:")
    print("  export VITE_SUPABASE_URL='https://your-project.supabase.co'")
    print("  export VITE_SUPABASE_ANON_KEY='your-anon-key'")
    print("\nRunning in local mode (no cloud sync)...\n")
    enable_upload = False
else:
    print(f"✅ Cloud upload enabled to Supabase\n")
    print(f"URL: {SUPABASE_URL}\n")
    enable_upload = True

# Initialize Agora telemetry
init_agora(
    app_name="demo_workflow",
    export_to_console=True,
    export_to_file="demo_traces.jsonl",
    enable_cloud_upload=enable_upload,
    project_name="Demo Project"
)


@agora_node(name="Start")
async def start_node(shared):
    """Initialize the workflow"""
    print("🚀 Starting demo workflow...")
    shared["counter"] = 0
    shared["results"] = []
    return "process"


@agora_node(name="ProcessData")
async def process_data(shared):
    """Process some data"""
    shared["counter"] += 1
    result = f"Processed item #{shared['counter']}"
    shared["results"].append(result)

    print(f"  ✓ {result}")

    await asyncio.sleep(0.5)

    if shared["counter"] < 5:
        return "process"
    return "analyze"


@agora_node(name="AnalyzeResults")
async def analyze_results(shared):
    """Analyze the processed data"""
    print("\n📊 Analyzing results...")
    print(f"  Total items processed: {shared['counter']}")
    print(f"  Results: {len(shared['results'])} items")

    shared["analysis"] = {
        "total": shared["counter"],
        "status": "success"
    }

    await asyncio.sleep(0.3)
    return "finish"


@agora_node(name="Finish")
async def finish_node(shared):
    """Complete the workflow"""
    print("\n✅ Workflow completed successfully!")
    print(f"  Final count: {shared['counter']}")
    print(f"  Analysis: {shared['analysis']}")
    return None


async def run_demo():
    """Run the demo workflow"""

    print("="*60)
    print("AGORA WORKFLOW DEMO")
    print("="*60)
    print()

    flow = TracedAsyncFlow("DemoWorkflow")
    flow.start(start_node)

    start_node - "process" >> process_data
    process_data - "process" >> process_data
    process_data - "analyze" >> analyze_results
    analyze_results - "finish" >> finish_node

    shared = {}
    await flow.run_async(shared)

    print()
    print("="*60)
    print("WORKFLOW DIAGRAM")
    print("="*60)
    print()
    print(flow.to_mermaid())
    print()

    if SUPABASE_URL and SUPABASE_KEY:
        print("="*60)
        print("✓ Telemetry sent to Supabase!")
        print("View your workflow execution in your platform's Monitoring page")
        print("="*60)
    else:
        print("="*60)
        print("ℹ️  Local telemetry saved to: demo_traces.jsonl")
        print("Set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY to sync with cloud")
        print("="*60)


if __name__ == "__main__":
    asyncio.run(run_demo())
