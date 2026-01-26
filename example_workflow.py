"""
Example workflow with multiple steps to demonstrate animated visualization
"""
import asyncio
import os
from agora import agora_node, TracedAsyncFlow

@agora_node(name="DataPrep")
async def data_prep(shared):
    """Prepare data - fast step"""
    await asyncio.sleep(0.5)
    shared['data'] = "prepared data"
    return {"status": "prepared"}

@agora_node(name="ProcessData")
async def process_data(shared):
    """Process data - medium step"""
    await asyncio.sleep(1.5)
    data = shared.get('data', '')
    shared['processed'] = f"processed: {data}"
    return {"status": "processed", "items": 100}

@agora_node(name="EnrichData")
async def enrich_data(shared):
    """Enrich with external data - slow step"""
    await asyncio.sleep(2.0)
    processed = shared.get('processed', '')
    shared['enriched'] = f"enriched: {processed}"
    return {"status": "enriched", "quality": "high"}

@agora_node(name="ValidateData")
async def validate_data(shared):
    """Validate results - fast step"""
    await asyncio.sleep(0.3)
    enriched = shared.get('enriched', '')
    return {"status": "validated", "data": enriched}

@agora_node(name="SaveResults")
async def save_results(shared):
    """Save to database - medium step"""
    await asyncio.sleep(1.0)
    return {"status": "saved", "record_id": "12345"}

async def main():
    # Create workflow
    flow = TracedAsyncFlow("DataPipeline")
    
    # Build pipeline: prep -> process -> enrich -> validate -> save
    flow.start(data_prep)
    flow.chain(process_data)
    flow.chain(enrich_data)
    flow.chain(validate_data)
    flow.chain(save_results)
    
    # Execute
    print("🚀 Starting Data Pipeline workflow...")
    print("This will create a multi-step execution you can visualize!")
    
    result = await flow.run({})
    
    print(f"\n✅ Workflow completed!")
    print(f"Result: {result}")
    print(f"\n💡 Check the Monitoring page to see the animated visualization!")

if __name__ == "__main__":
    asyncio.run(main())
