"""
Error Handling Example
=======================
Shows retries and fallbacks.

Run with: PYTHONPATH=. python3 examples/error_handling.py
"""

import asyncio
import random
from agora import AsyncNode, AsyncFlow, init_agora

init_agora(app_name="Error Handling")


class UnreliableNode(AsyncNode):
    def __init__(self):
        super().__init__(
            "unreliable_api",
            max_retries=3,  # Retry 3 times
            wait=1          # Wait 1 second between retries
        )
        self.attempt = 0
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        self.attempt += 1
        print(f"🔄 Attempt {self.attempt}...")
        
        # 70% chance of failure
        if random.random() < 0.7:
            print(f"   ❌ Failed!")
            raise Exception("API timeout")
        
        print(f"   ✅ Success!")
        return "Success!"
    
    async def exec_fallback_async(self, prep_res, exc):
        print(f"   ⚠️  All retries failed, using fallback")
        return "Fallback data (cached)"


async def main():
    node = UnreliableNode()
    
    print("="*50)
    print("Testing unreliable API with retries...")
    print("="*50)
    
    result = await node.run_async({})
    print(f"\n✅ Final result: {result}")
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())
