from agora.agora_tracer import TracedAsyncFlow, init_agora
from agora import AsyncNode
from agora.wide_events import set_business_context
from openai import OpenAI
import os
import asyncio
import uuid

# Initialize Agora
init_agora(
    app_name="chatbot-single-session",
    project_name="chatbot",
    export_to_file="chat.jsonl",
    enable_cloud_upload=True
)

class GetUserInput(AsyncNode):
    """Wait for user input (blocking)"""
    async def prep_async(self, shared):
        return shared

    async def exec_async(self, shared):
        print("\n" + "-"*40)
        user_input = await asyncio.to_thread(input, "You: ")
        
        if user_input.lower() in ['quit', 'exit']:
            return "quit"
            
        shared['user_input'] = user_input
        return "continue"
    
    async def post_async(self, shared, prep_res, exec_res):
        # Return the action from exec_async for routing
        return exec_res

class GenerateResponse(AsyncNode):
    """Generate AI response"""
    async def prep_async(self, shared):
        return shared

    async def exec_async(self, shared):
        user_msg = shared.get('user_input')
        conversation = shared.get('conversation', [])
        
        # Add to history
        conversation.append({"role": "user", "content": user_msg})
        
        # Build context
        set_business_context(
            user_id="demo_user",
            custom={
                "session_id": shared['session_id'],
                "turn": len(conversation) // 2
            }
        )
        
        # Call AI
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        print("🤖 Thinking...", end="\r")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=conversation
        )
        print(" " * 20, end="\r") # Clear loading
        
        bot_msg = response.choices[0].message.content
        conversation.append({"role": "assistant", "content": bot_msg})
        
        print(f"Bot: {bot_msg}")
        
        shared['conversation'] = conversation
        return bot_msg
    
    async def post_async(self, shared, prep_res, exec_res):
        # Return routing action to loop back to input
        return "next"

async def run_single_session():
    session_id = str(uuid.uuid4())[:8]
    print(f"\n💬 CHATBOT (Single Session Mode) - ID: {session_id}")
    print("One execution bar for the whole chat!\n")
    
    # Define Nodes
    get_input = GetUserInput(name="Wait For Input")
    generate = GenerateResponse(name="Generate AI Reply")
    
    # Define Cyclic Flow
    flow = TracedAsyncFlow(name=f"ChatSession_{session_id}")
    
    # 1. Start at Input
    flow.start(get_input)
    
    # 2. Input -> Generate (if "continue")
    get_input.next(generate, "continue")
    
    # 3. Generate -> Input (Loop back!)
    generate.next(get_input, "next")
    
    # 4. Input -> End (if "quit", it goes nowhere, so it stops)
    
    # Shared State
    shared = {
        'conversation': [],
        'session_id': session_id
    }
    
    # Run the One Big Loop
    await flow.run_async(shared)
    
    print("\n✅ Session Ended. Telemetry uploading...")
    await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(run_single_session())
