"""
Simple Agora Workflow Demo - Completes Properly
Not a chat app - just runs once and exits
"""
from agora import init_agora, AsyncFlow, AsyncNode
from agora.wide_events import set_business_context
from openai import OpenAI
import os
import asyncio

class FetchData(AsyncNode):
    async def exec_async(self, prep_res):
        # Simulate data fetching
        return {"data": ["item1", "item2", "item3"]}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['items'] = exec_res['data']
        return "default"


class ProcessWithAI(AsyncNode):
    async def prep_async(self, shared):
        return shared.get('items', [])
    
    async def exec_async(self, prep_res):
        items = prep_res
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Analyze these items: {items}. Give a one-sentence summary."
            }]
        )
        
        return response.choices[0].message.content
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['analysis'] = exec_res
        return "default"


class GenerateReport(AsyncNode):
    async def prep_async(self, shared):
        return {
            'items': shared.get('items'),
            'analysis': shared.get('analysis')
        }
    
    async def exec_async(self, prep_res):
        return f"Report: {prep_res['analysis']}"
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['report'] = exec_res
        return "default"


async def main():
    print("\n🚀 Running Simple Workflow Demo\n")
    
    # Initialize
    init_agora(
        app_name="simple-workflow",
        export_to_file="workflow.jsonl",
        enable_cloud_upload=True,
        project_name="demo"
    )
    
    # Set context
    set_business_context(
        user_id="demo_user",
        custom={"workflow_type": "data_analysis"}
    )
    
    # Build workflow
    fetch = FetchData()
    process = ProcessWithAI()
    report = GenerateReport()
    
    flow = AsyncFlow(name="DataAnalysisFlow")
    flow.start(fetch) >> process >> report
    
    # Run
    shared = {}
    await flow.run_async(shared)
    
    print(f"✅ Result: {shared.get('report')}\n")
    print("📊 Check Agora platform - execution will complete when script exits\n")

if __name__ == "__main__":
    asyncio.run(main())
    # Script exits here → atexit fires → execution marked as "success" ✅
