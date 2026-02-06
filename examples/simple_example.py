"""
SUPER SIMPLE Agora Example
===========================
The absolute simplest way to use Agora.

Run with: PYTHONPATH=. python3 examples/simple_example.py
"""

import asyncio
from agora import AsyncNode, AsyncFlow, init_agora

# Initialize (optional - for telemetry)
init_agora(app_name="Simple Example")


# Step 1: Define a node
class HelloNode(AsyncNode):
    async def prep_async(self, shared):
        # Return the shared data to exec_async
        return shared
    
    async def exec_async(self, prep_res):
        name = prep_res.get("name", "World")
        return f"Hello, {name}!"


# Step 2: Run it
async def main():
    node = HelloNode("greet")
    result = await node.run_async({"name": "Alice"})
    print(result)  # Output: Hello, Alice!

if __name__ == "__main__":
    asyncio.run(main())
