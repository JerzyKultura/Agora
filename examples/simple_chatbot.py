"""
Simple Chatbot - Clean & Easy
==============================
Shows how ridiculously easy it is to build a chatbot with Agora.

Run: PYTHONPATH=. python3 examples/simple_chatbot.py
"""

import asyncio
import os
from agora import AsyncNode, AsyncFlow, init_agora
from agora.agora_tracer import TracedAsyncNode, TracedAsyncFlow

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

init_agora(app_name="Simple Chatbot")


class ChatNode(TracedAsyncNode):
    """Single node that handles the entire chat"""
    
    def __init__(self):
        super().__init__("Chat")
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = AsyncOpenAI()
        else:
            self.client = None
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        user_msg = prep_res.get("user_message", "")
        history = prep_res.get("history", [])
        
        if not self.client:
            return f"Echo: {user_msg}"
        
        # Build messages
        messages = [{"role": "system", "content": "You are a helpful assistant. Be brief."}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_msg})
        
        # Call OpenAI
        response = await self.client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=150
        )
        
        return response.choices[0].message.content
    
    async def post_async(self, shared, prep_res, exec_res):
        # Update history
        history = shared.get("history", [])
        history.append({"role": "user", "content": prep_res.get("user_message", "")})
        history.append({"role": "assistant", "content": exec_res})
        shared["history"] = history
        shared["response"] = exec_res
        return "default"


class SimpleChatFlow(TracedAsyncFlow):
    """Dead simple chat flow"""
    
    def __init__(self):
        self.chat = ChatNode()
        super().__init__("Simple Chat", start=self.chat)


async def main():
    print("\n🤖 Simple Chatbot (type 'quit' to exit)\n")
    
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("⚠️  No OpenAI key - running in echo mode\n")
    
    shared = {"history": []}
    
    while True:
        # Get user input
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        
        if not user_input or user_input.lower() in ['quit', 'exit']:
            break
        
        # Run flow
        shared["user_message"] = user_input
        flow = SimpleChatFlow()
        await flow.run_async(shared)
        
        # Show response
        print(f"AI:  {shared.get('response', '')}\n")
    
    print("\n👋 Bye!\n")


if __name__ == "__main__":
    asyncio.run(main())
