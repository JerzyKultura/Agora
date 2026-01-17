"""
💬 Simple Chatbot with Agora Telemetry
Shows: Multi-turn conversation with full LLM tracking
"""
from agora import init_agora
from agora.wide_events import set_business_context
from openai import OpenAI
import os
import json

# Initialize Agora
init_agora(
    app_name="chatbot-demo",
    export_to_file="chat_telemetry.jsonl",
    enable_cloud_upload=False
)

# Set user context
set_business_context(
    user_id="demo_user",
    custom={"app": "chatbot", "session": "demo_session_1"}
)

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

print("\n" + "="*80)
print("💬 AGORA CHATBOT DEMO")
print("="*80)
print("Type 'quit' to exit and see telemetry stats\n")

conversation = []

while True:
    user_input = input("You: ")
    
    if user_input.lower() in ['quit', 'exit', 'q']:
        break
    
    conversation.append({"role": "user", "content": user_input})
    
    # LLM call - automatically tracked by Agora!
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation
    )
    
    assistant_message = response.choices[0].message.content
    conversation.append({"role": "assistant", "content": assistant_message})
    
    print(f"Bot: {assistant_message}\n")

# Show telemetry stats
print("\n" + "="*80)
print("📊 TELEMETRY STATS")
print("="*80 + "\n")

spans = []
with open("chat_telemetry.jsonl", 'r') as f:
    for line in f:
        if line.strip():
            spans.append(json.loads(line))

print(f"Total LLM calls: {len(spans)}")

total_tokens = 0
for i, span in enumerate(spans, 1):
    attrs = span.get('attributes', {})
    tokens = attrs.get('llm.usage.total_tokens', 0)
    prompt_tokens = attrs.get('llm.usage.prompt_tokens', 0)
    completion_tokens = attrs.get('llm.usage.completion_tokens', 0)
    
    print(f"\nTurn {i}:")
    print(f"  Prompt tokens: {prompt_tokens}")
    print(f"  Completion tokens: {completion_tokens}")
    print(f"  Total tokens: {tokens}")
    
    total_tokens += tokens

print(f"\n{'='*80}")
print(f"Total tokens used: {total_tokens:,}")
print(f"Estimated cost: ${total_tokens * 0.00002:.4f}")
print(f"\n✅ All conversation data saved to: chat_telemetry.jsonl")
print(f"{'='*80}\n")
