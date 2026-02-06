"""
Chatbot Flow - Properly Visualized
===================================
A chatbot implemented as a proper flow with multiple nodes for visualization.

Setup:
1. pip install openai
2. export OPENAI_API_KEY=sk-your-key-here
3. Run: PYTHONPATH=. python3 examples/chatbot_flow.py

This will show up properly in the dashboard with full workflow visualization!
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

init_agora(app_name="Chatbot Flow Demo")


class GetUserInputNode(TracedAsyncNode):
    """Gets user input (simulated for demo)"""
    
    def __init__(self):
        super().__init__("Get User Input")
        self.code = """
async def get_user_input():
    # In real app, this would get actual user input
    return user_message
"""
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        user_message = prep_res.get("user_message", "")
        print(f"\n👤 User: {user_message}")
        return {"user_message": user_message}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"


class ProcessContextNode(TracedAsyncNode):
    """Processes conversation context"""
    
    def __init__(self):
        super().__init__("Process Context")
        self.code = """
async def process_context(user_message, chat_history):
    # Build conversation context
    messages = [system_prompt] + chat_history + [user_message]
    return messages
"""
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        user_message = prep_res.get("user_message", "")
        chat_history = prep_res.get("chat_history", [])
        
        # Build messages
        messages = [
            {"role": "system", "content": "You are a helpful AI assistant. Be concise and friendly."}
        ]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})
        
        print(f"   📝 Processing context ({len(messages)} messages)")
        
        return {"messages": messages}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"


class CallLLMNode(TracedAsyncNode):
    """Calls the LLM API"""
    
    def __init__(self):
        super().__init__("Call LLM", max_retries=2, wait=1)
        self.code = """
async def call_llm(messages):
    response = await openai.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        max_tokens=200
    )
    return response.choices[0].message.content
"""
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = AsyncOpenAI()
        else:
            self.client = None
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        messages = prep_res.get("messages", [])
        
        if not self.client:
            print("   ⚠️  Using mock response")
            return {
                "response": "This is a mock response. Set OPENAI_API_KEY for real responses.",
                "tokens": 0
            }
        
        print("   🤖 Calling OpenAI API...")
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            print(f"   ✅ Got response ({tokens} tokens)")
            
            return {
                "response": ai_response,
                "tokens": tokens
            }
        except Exception as e:
            print(f"   ❌ Error: {e}")
            raise
    
    async def post_async(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"
    
    async def exec_fallback_async(self, prep_res, exc):
        print("   ⚠️  Using fallback response")
        return {
            "response": "Sorry, I encountered an error. Please try again.",
            "tokens": 0,
            "error": str(exc)
        }


class UpdateHistoryNode(TracedAsyncNode):
    """Updates conversation history"""
    
    def __init__(self):
        super().__init__("Update History")
        self.code = """
async def update_history(user_message, ai_response, chat_history):
    chat_history.append({"role": "user", "content": user_message})
    chat_history.append({"role": "assistant", "content": ai_response})
    return chat_history
"""
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        user_message = prep_res.get("user_message", "")
        ai_response = prep_res.get("response", "")
        chat_history = prep_res.get("chat_history", [])
        
        # Update history
        chat_history.append({"role": "user", "content": user_message})
        chat_history.append({"role": "assistant", "content": ai_response})
        
        print(f"   💾 Updated history ({len(chat_history)} messages)")
        
        return {
            "chat_history": chat_history,
            "updated": True
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared["chat_history"] = exec_res.get("chat_history", [])
        return "default"


class DisplayResponseNode(TracedAsyncNode):
    """Displays the AI response"""
    
    def __init__(self):
        super().__init__("Display Response")
        self.code = """
async def display_response(response):
    print(f"AI: {response}")
    return response
"""
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        response = prep_res.get("response", "")
        print(f"\n🤖 AI: {response}")
        return {"displayed": True}


class ChatbotFlow(TracedAsyncFlow):
    """Complete chatbot workflow"""
    
    def __init__(self):
        # Create nodes
        self.get_input = GetUserInputNode()
        self.process_context = ProcessContextNode()
        self.call_llm = CallLLMNode()
        self.update_history = UpdateHistoryNode()
        self.display = DisplayResponseNode()
        
        # Chain them: input → context → llm → history → display
        self.get_input.successors = {"default": self.process_context}
        self.process_context.successors = {"default": self.call_llm}
        self.call_llm.successors = {"default": self.update_history}
        self.update_history.successors = {"default": self.display}
        
        # Initialize flow
        super().__init__("Chatbot Conversation Flow", start=self.get_input)


async def main():
    print("="*60)
    print("🤖 Chatbot Flow Demo")
    print("="*60)
    print()
    
    if not OPENAI_AVAILABLE or not os.getenv("OPENAI_API_KEY"):
        print("⚠️  Running in MOCK mode")
        print("   Install: pip install openai")
        print("   Set key: export OPENAI_API_KEY=sk-...")
        print()
    
    # Conversation state
    shared = {
        "chat_history": [],
        "total_tokens": 0
    }
    
    # Demo conversation
    demo_messages = [
        "Hello! Who are you?",
        "What can you help me with?",
        "Tell me a fun fact about Python programming."
    ]
    
    for user_message in demo_messages:
        # Update shared state
        shared["user_message"] = user_message
        
        # Create and run flow
        flow = ChatbotFlow()
        await flow.run_async(shared)
        
        # Update token count
        tokens = shared.get("tokens", 0)
        shared["total_tokens"] = shared.get("total_tokens", 0) + tokens
        
        print()
    
    # Show stats
    print("="*60)
    print(f"📊 Conversation Statistics:")
    print(f"   Messages: {len(demo_messages)}")
    print(f"   Total tokens: {shared.get('total_tokens', 0)}")
    print(f"   History length: {len(shared.get('chat_history', []))}")
    print("="*60)
    print()
    print("📊 Check dashboard: http://localhost:5173/monitoring")
    print("   You'll see the full workflow visualization!")
    print("   Each conversation turn is a complete flow with 5 nodes!")


if __name__ == "__main__":
    asyncio.run(main())
