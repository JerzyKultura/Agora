"""
Conditional Routing Example
============================
Shows how to route based on data.

Run with: PYTHONPATH=. python3 examples/conditional_routing.py
"""

import asyncio
from agora import AsyncNode, AsyncFlow, init_agora

init_agora(app_name="Routing Example")


class ClassifyNode(AsyncNode):
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        amount = prep_res.get("amount", 0)
        print(f"🔍 Classifying: ${amount}")
        
        if amount > 1000:
            print("   → VIP route")
            return "vip"
        else:
            print("   → Standard route")
            return "standard"
    
    async def post_async(self, shared, prep_res, exec_res):
        # exec_res is already the action string
        return exec_res


class VIPNode(AsyncNode):
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        print("👑 VIP processing (15% discount)")
        amount = prep_res.get("amount", 0)
        final = amount * 0.85
        return final
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["final_amount"] = exec_res
        return exec_res


class StandardNode(AsyncNode):
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        print("📝 Standard processing")
        amount = prep_res.get("amount", 0)
        return amount
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["final_amount"] = exec_res
        return exec_res


async def main():
    # Create nodes
    classify = ClassifyNode("classify")
    vip = VIPNode("vip")
    standard = StandardNode("standard")
    
    # Set up routing
    classify.successors = {
        "vip": vip,
        "standard": standard
    }
    
    # Create flow
    flow = AsyncFlow("Routing Demo", start=classify)
    
    # Test 1: Standard
    print("="*50)
    print("Test 1: $500")
    shared1 = {"amount": 500}
    result1 = await flow.run_async(shared1)
    print(f"✅ Final: ${shared1.get('final_amount', result1)}")
    
    # Test 2: VIP
    print("\n" + "="*50)
    print("Test 2: $2000")
    shared2 = {"amount": 2000}
    result2 = await flow.run_async(shared2)
    print(f"✅ Final: ${shared2.get('final_amount', result2)}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
