"""
Agora Simple Example - Perfect for Getting Started
===================================================
A minimal example showing the basic Agora workflow pattern.

This is a simplified version ideal for learning the fundamentals.
"""

import asyncio
from typing import Dict, Any
from agora.agora_tracer import init_agora, agora_node, TracedAsyncFlow

# Initialize Agora
init_agora(
    app_name="simple-demo",
    project_name="My First Agora Workflow",
    enable_cloud_upload=True
)

# ============================================================================
# WORKFLOW NODES - Each node is a step in your pipeline
# ============================================================================

@agora_node(name="FetchData")
async def fetch_data(shared: Dict[str, Any]) -> str:
    """Step 1: Fetch or receive input data"""
    input_text = shared.get("input", "Hello, Agora!")
    shared["data"] = input_text
    print(f"✓ Fetched: {input_text}")
    return "process"  # Route to next node


@agora_node(name="ProcessData")
async def process_data(shared: Dict[str, Any]) -> str:
    """Step 2: Transform the data"""
    data = shared["data"]
    processed = data.upper()  # Simple transformation
    shared["result"] = processed
    print(f"✓ Processed: {processed}")
    return "save"  # Route to next node


@agora_node(name="SaveResult")
async def save_result(shared: Dict[str, Any]) -> str:
    """Step 3: Save or output the result"""
    result = shared["result"]
    shared["final"] = f"Final result: {result}"
    print(f"✓ Saved: {result}")
    return "complete"  # End of workflow


# ============================================================================
# WORKFLOW SETUP
# ============================================================================

# Create the workflow
flow = TracedAsyncFlow("SimplePipeline")

# Define the starting point
flow.start(fetch_data)

# Connect the nodes (define the flow)
fetch_data - "process" >> process_data
process_data - "save" >> save_result

# ============================================================================
# RUN THE WORKFLOW
# ============================================================================

async def main():
    print("🚀 Running Simple Agora Workflow\n")
    
    # Run with input data
    result = await flow.run_async({"input": "hello world"})
    
    print(f"\n✅ {result['final']}")
    print("💾 Telemetry uploaded to Agora Cloud")

# For Google Colab
if __name__ == "__main__":
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        pass
    
    asyncio.run(main())
