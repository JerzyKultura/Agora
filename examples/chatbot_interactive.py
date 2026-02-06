"""
Interactive Chatbot Example
============================
A simple chatbot where you can have a conversation with an AI.

Setup:
1. pip install openai
2. export OPENAI_API_KEY=sk-your-key-here
3. Run: PYTHONPATH=. python3 examples/chatbot_interactive.py

Type your messages and press Enter. Type 'quit' or 'exit' to stop.
"""

import asyncio
import os
from agora import AsyncNode, AsyncFlow, init_agora

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  Install OpenAI: pip install openai")

init_agora(app_name="Interactive Chatbot")


class ChatNode(AsyncNode):
    """Handles one chat turn with the AI"""
    
    def __init__(self):
        super().__init__("chat", max_retries=2, wait=1)
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = AsyncOpenAI()
        else:
            self.client = None
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        user_message = prep_res.get("user_message", "")
        chat_history = prep_res.get("chat_history", [])
        
        if not self.client:
            # Mock response
            return {
                "response": f"Echo: {user_message}",
                "tokens": 0
            }
        
        # Build messages with history
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Be concise and friendly."}
        ]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})
        
        try:
            # Call OpenAI
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            return {
                "response": ai_response,
                "tokens": tokens
            }
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
            return {
                "response": "Sorry, I encountered an error. Please try again.",
                "tokens": 0,
                "error": str(e)
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        # Update chat history
        chat_history = shared.get("chat_history", [])
        chat_history.append({"role": "user", "content": prep_res.get("user_message", "")})
        chat_history.append({"role": "assistant", "content": exec_res.get("response", "")})
        shared["chat_history"] = chat_history
        shared["last_response"] = exec_res.get("response", "")
        shared["total_tokens"] = shared.get("total_tokens", 0) + exec_res.get("tokens", 0)
        return "default"


async def main():
    print("="*60)
    print("🤖 Interactive Chatbot")
    print("="*60)
    print()
    
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Running in MOCK mode (no OpenAI)")
        print("   Install: pip install openai")
        print("   Set key: export OPENAI_API_KEY=sk-...")
        print()
    
    print("Type your message and press Enter.")
    print("Type 'quit' or 'exit' to stop.")
    print("="*60)
    print()
    
    # Create chat node
    chat_node = ChatNode()
    
    # Shared state for conversation
    shared = {
        "chat_history": [],
        "total_tokens": 0
    }
    
    while True:
        # Get user input
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 Goodbye!")
            break
        
        if not user_input:
            continue
        
        if user_input.lower() in ['quit', 'exit', 'bye']:
            print("\n👋 Goodbye!")
            break
        
        # Update shared state with user message
        shared["user_message"] = user_input
        
        # Run chat node
        await chat_node.run_async(shared)
        
        # Display AI response
        response = shared.get("last_response", "")
        print(f"AI:  {response}")
        print()
    
    # Show stats
    total_tokens = shared.get("total_tokens", 0)
    turns = len(shared.get("chat_history", [])) // 2
    
    print()
    print("="*60)
    print(f"📊 Chat Statistics:")
    print(f"   Turns: {turns}")
    print(f"   Total tokens: {total_tokens}")
    print("="*60)
    print()
    print("📊 Check dashboard: http://localhost:5173/monitoring")
    print("   You'll see all your chat turns tracked!")


if __name__ == "__main__":
    asyncio.run(main())
