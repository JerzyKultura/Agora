"""
Decorator Example - Super Simple
=================================
Shows how easy it is to build workflows with the @agora_node decorator.

Run: PYTHONPATH=. python3 examples/decorator_example.py
"""

import asyncio
from agora.agora_tracer import agora_node, TracedAsyncFlow, init_agora

init_agora(app_name="Decorator Example")


# Define nodes with decorator - SO EASY!
@agora_node(name="FetchData")
async def fetch_data(shared):
    """Fetch some data"""
    print("📥 Fetching data...")
    await asyncio.sleep(0.2)
    shared['items'] = [1, 2, 3, 4, 5]
    return "default"  # Return routing action


@agora_node(name="Transform")
async def transform(shared):
    """Transform the data"""
    print("🔄 Transforming...")
    items = shared.get('items', [])
    shared['result'] = [x * 2 for x in items]
    return "default"  # Return routing action


@agora_node(name="Save")
async def save(shared):
    """Save the results"""
    print("💾 Saving...")
    result = shared.get('result', [])
    print(f"   Saved: {result}")
    return "default"  # Return routing action


async def main():
    print("="*50)
    print("🚀 Decorator Example - 3 Node Flow")
    print("="*50)
    print()
    
    # Create flow and chain nodes
    flow = TracedAsyncFlow("Simple ETL")
    
    # Set up the chain: fetch -> transform -> save
    fetch_data.successors = {"default": transform}
    transform.successors = {"default": save}
    
    # Set start node
    flow.start_node = fetch_data
    
    # Run
    result = await flow.run_async({})
    
    print()
    print("="*50)
    print("✅ Done!")
    print(f"   Result: {result}")
    print("="*50)
    print()
    print("📊 Check dashboard: http://localhost:5173/monitoring")
    print("   You'll see the 3-node flow visualized!")


if __name__ == "__main__":
    asyncio.run(main())
