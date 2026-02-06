"""
Basic 3-Node Workflow
======================
Simple ETL pipeline: Fetch → Transform → Save

Run with: PYTHONPATH=. python3 examples/basic_workflow.py
"""

import asyncio
from agora import AsyncNode, AsyncFlow, init_agora

init_agora(app_name="Basic Workflow")


class FetchNode(AsyncNode):
    async def exec_async(self, prep_res):
        print("📥 Fetching data...")
        return {"items": [1, 2, 3, 4, 5]}
    
    async def post_async(self, shared, prep_res, exec_res):
        # Store result in shared state for next node
        shared.update(exec_res)
        # Return action string, not dict!
        return "default"


class TransformNode(AsyncNode):
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        print("🔄 Transforming data...")
        items = prep_res.get("items", [])
        return {"transformed": [x * 2 for x in items]}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"


class SaveNode(AsyncNode):
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        print("💾 Saving data...")
        data = prep_res.get("transformed", [])
        print(f"   Saved {len(data)} items: {data}")
        return "complete"


async def main():
    # Create nodes
    fetch = FetchNode("fetch")
    transform = TransformNode("transform")
    save = SaveNode("save")
    
    # Chain them: fetch → transform → save
    fetch.successors = {"default": transform}
    transform.successors = {"default": save}
    
    # Create flow
    flow = AsyncFlow("ETL Pipeline", start=fetch)
    
    # Run
    print("="*50)
    result = await flow.run_async({})
    print(f"✅ Done! Result: {result}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
