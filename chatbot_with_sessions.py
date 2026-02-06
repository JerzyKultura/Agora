from agora.agora_tracer import TracedAsyncFlow, agora_node, init_agora
from agora.wide_events import BusinessContext, enrich_current_span
from openai import OpenAI
import os
import asyncio
import uuid

init_agora(
    app_name="chatbot-app",
    project_name="chatbot",
    export_to_file="chat.jsonl",
    enable_cloud_upload=True
)

# Session state (in production, store in database/Redis)
class ChatSession:
    def __init__(self):
        self.session_id = str(uuid.uuid4())
        self.conversation = []
        self.turn_number = 0
        self.total_tokens = 0
    
    def add_turn(self, user_msg, bot_msg, tokens_used):
        self.turn_number += 1
        self.total_tokens += tokens_used
        self.conversation.append({"role": "user", "content": user_msg})
        self.conversation.append({"role": "assistant", "content": bot_msg})

@agora_node(name="ProcessMessage")
async def process_message(shared):
    user_msg = shared.get('user_input')
    session = shared.get('session')
    
    # Enrich with business context BEFORE processing
    context = BusinessContext(
        user_id="demo_user_123",
        session_id=session.session_id,
        conversation_turn=session.turn_number + 1,
        total_tokens_this_session=session.total_tokens,
        subscription_tier="premium",
        account_age_days=90,
        feature_flags={
            "new_chat_ui": True,
            "gpt4_access": True
        }
    )
    enrich_current_span(context)
    
    # Process with OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=session.conversation + [{"role": "user", "content": user_msg}]
    )
    
    bot_msg = response.choices[0].message.content
    tokens_used = response.usage.total_tokens
    
    # Update session
    session.add_turn(user_msg, bot_msg, tokens_used)
    
    shared['bot_response'] = bot_msg
    shared['tokens_used'] = tokens_used
    return None

async def chat_turn(user_input, session):
    """Run ONE chat turn as a complete workflow"""
    flow = TracedAsyncFlow("ChatTurn")
    flow.start(process_message)
    
    shared = {
        'user_input': user_input,
        'session': session
    }
    
    await flow.run_async(shared)
    return shared

async def main():
    print("\n💬 CHATBOT WITH SESSION MANAGEMENT\n")
    
    # Create session
    session = ChatSession()
    print(f"📋 Session ID: {session.session_id}\n")
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['exit', 'quit']:
            break
        
        result = await chat_turn(user_input, session)
        print(f"Bot: {result['bot_response']}\n")
        print(f"📊 Turn {session.turn_number} | Total tokens: {session.total_tokens}\n")
    
    print("\n✅ Done!")
    print(f"📈 Session summary: {session.turn_number} turns, {session.total_tokens} tokens")

if __name__ == "__main__":
    asyncio.run(main())
