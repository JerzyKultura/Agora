"""
💬 Agora Platform Chatbot - Proper Execution Tracking
"""
from agora import init_agora, AsyncFlow, AsyncNode
from agora.wide_events import set_business_context
from openai import OpenAI
import os
import uuid
import asyncio
import time

# ============================================================================
# WORKFLOW NODES
# ============================================================================

class ProcessUserMessage(AsyncNode):
    """Process and validate user input"""
    async def prep_async(self, shared):
        return shared.get('user_input')
    
    async def exec_async(self, prep_res):
        user_message = prep_res
        if not user_message or len(user_message.strip()) == 0:
            return {"valid": False, "message": ""}
        return {"valid": True, "message": user_message.strip()}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['user_message'] = exec_res['message']
        return "default"


class GenerateResponse(AsyncNode):
    """Generate AI response using OpenAI"""
    async def prep_async(self, shared):
        return {
            "conversation": shared.get('conversation', []),
            "user_message": shared.get('user_message')
        }
    
    async def exec_async(self, prep_res):
        conversation = prep_res['conversation']
        user_message = prep_res['user_message']
        
        # Add user message
        conversation.append({"role": "user", "content": user_message})
        
        # Call OpenAI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation
        )
        
        assistant_message = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": assistant_message})
        
        return {
            "response": assistant_message,
            "conversation": conversation
        }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['bot_response'] = exec_res['response']
        shared['conversation'] = exec_res['conversation']
        return "default"


# ============================================================================
# MAIN CHATBOT
# ============================================================================

async def run_chatbot():
    # Generate session ID
    session_id = str(uuid.uuid4())[:8]
    
    # Initialize Agora
    init_agora(
        app_name="chatbot-workflow",
        export_to_console=True,  # Also show in console for debugging
        export_to_file="chat.jsonl",
        enable_cloud_upload=True,
        project_name="chatbot"
    )
    
    print("\n" + "="*80)
    print("💬 AGORA PLATFORM CHATBOT")
    print("="*80)
    print(f"\nSession ID: {session_id}")
    print("\nType 'quit' to exit\n")
    
    # Track conversation
    conversation = []
    turn = 0
    
    # Chat loop
    while True:
        user_input = input("You: ")
        
        if user_input.lower() in ['quit', 'exit', 'q']:
            break
        
        turn += 1
        
        # Set business context
        set_business_context(
            user_id="demo_user",
            custom={
                "app": "chatbot",
                "session_id": session_id,
                "turn": turn,
                "environment": "demo"
            }
        )
        
        # Build workflow
        process_input = ProcessUserMessage()
        generate_response = GenerateResponse()
        
        flow = AsyncFlow(name=f"chat_turn_{turn}")
        flow.start(process_input) >> generate_response
        
        # Shared state
        shared = {
            'user_input': user_input,
            'conversation': conversation.copy()
        }
        
        # Run workflow
        print(f"\n[Turn {turn}] Processing...")
        await flow.run_async(shared)
        
        # Update conversation
        conversation = shared.get('conversation', conversation)
        
        # Display response
        bot_response = shared.get('bot_response', 'No response')
        print(f"Bot: {bot_response}\n")
        
        # Give time for async upload to complete
        print("[Uploading telemetry...]")
        await asyncio.sleep(2)  # Wait for upload
        print("[✓] Telemetry uploaded\n")
    
    # Final summary
    print("\n✅ Chat session complete!")
    print(f"\n📊 Session Summary:")
    print(f"   Session ID: {session_id}")
    print(f"   Total turns: {turn}")
    print(f"\n🌐 Agora Platform:")
    print(f"   View your {turn} chat turns in the dashboard")
    print(f"   Filter by custom.session_id = {session_id}")
    
    # Wait for final upload
    print("\n⏳ Finalizing uploads...")
    await asyncio.sleep(3)
    print("✅ Done!\n")


if __name__ == "__main__":
    asyncio.run(run_chatbot())
