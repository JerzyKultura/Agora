from agora.agora_tracer import TracedAsyncFlow, agora_node, init_agora
from agora.wide_events import enrich_with_user
from openai import OpenAI
import os
import asyncio

init_agora(
    app_name="chatbot-app",
    project_name="chatbot",
    export_to_file="chat.jsonl",
    enable_cloud_upload=True
)

@agora_node(name="ProcessMessage")
async def process_message(shared):
    user_msg = shared.get('user_input')
    conversation = shared.get('conversation', [])
    
    conversation.append({"role": "user", "content": user_msg})
    
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation
    )
    
    bot_msg = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": bot_msg})
    
    shared['bot_response'] = bot_msg
    shared['conversation'] = conversation
    return None

async def chat_turn(user_input, conversation):
    """Run ONE chat turn as a complete workflow"""
    flow = TracedAsyncFlow("ChatTurn")  # New flow each turn!
    flow.start(process_message)
    
    shared = {
        'user_input': user_input,
        'conversation': conversation
    }
    
    await flow.run_async(shared)
    return shared

async def main():
    print("\n💬 CHATBOT (Fixed Version)\n")
    conversation = []
    
    while True:
        user_input = input("You: ")
        if user_input.lower() in ['quit', 'exit']:
            break
        
        # Each turn is a SEPARATE workflow that completes!
        shared = await chat_turn(user_input, conversation)
        conversation = shared['conversation']
        
        print(f"Bot: {shared['bot_response']}\n")
    
    print("\n✅ Done!\n")

if __name__ == "__main__":
    asyncio.run(main())
