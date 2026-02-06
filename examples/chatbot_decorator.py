"""
Chatbot with Decorators
========================
Clean chatbot using @agora_node decorator - shows how simple Agora is!

Run: PYTHONPATH=. python3 examples/chatbot_decorator.py
"""

import asyncio
import os
from agora.agora_tracer import agora_node, TracedAsyncFlow, init_agora

try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

init_agora(app_name="Chatbot Decorator")

# Initialize OpenAI client
client = AsyncOpenAI() if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY") else None


@agora_node(name="GetResponse")
async def get_response(shared):
    """Get AI response for user message"""
    user_msg = shared.get("user_message", "")
    history = shared.get("history", [])
    
    if not client:
        # Mock response
        shared["response"] = f"Echo: {user_msg}"
        return "default"
    
    # Build messages with history
    messages = [{"role": "system", "content": "You are a helpful assistant. Be brief."}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_msg})
    
    # Call OpenAI
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=150
    )
    
    ai_response = response.choices[0].message.content
    
    # Update history
    history.append({"role": "user", "content": user_msg})
    history.append({"role": "assistant", "content": ai_response})
    shared["history"] = history
    shared["response"] = ai_response
    
    return "default"


async def main():
    print("\n🤖 Chatbot (type 'quit' to exit)\n")
    
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
        
        # Create flow with single node
        flow = TracedAsyncFlow("Chat")
        flow.start_node = get_response
        
        # Run
        shared["user_message"] = user_input
        await flow.run_async(shared)
        
        # Show response
        print(f"AI:  {shared.get('response', '')}\n")
    
    print("\n👋 Bye!\n")


if __name__ == "__main__":
    asyncio.run(main())
