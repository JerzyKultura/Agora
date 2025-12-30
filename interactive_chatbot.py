#!/usr/bin/env python3
"""
Interactive Chatbot with Live Telemetry
========================================

Real-time chatbot that sends telemetry to your Live Telemetry dashboard.
Watch http://localhost:5173/live to see prompts, responses, tokens, and costs!

Setup:
1. export OPENAI_API_KEY="sk-..."
2. export VITE_SUPABASE_URL="https://your-project.supabase.co"
3. export VITE_SUPABASE_ANON_KEY="eyJhbGci..."
4. python interactive_chatbot.py

Type your questions and watch them appear in Live Telemetry in real-time!
Type 'exit' or 'quit' to stop.
"""

import os
import asyncio
from openai import OpenAI

from agora.agora_tracer import init_agora

# Initialize Agora telemetry (Traceloop auto-instruments OpenAI!)
print("🔧 Initializing Agora telemetry...")
init_agora(
    app_name="interactive-chatbot",
    project_name="Interactive Chatbot",
    export_to_console=False,
    enable_cloud_upload=True,
    capture_io=True
)

# Initialize OpenAI client (automatically instrumented by Traceloop)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Conversation history
conversation_history = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant. Keep responses concise and friendly."
    }
]


def chat(user_message: str) -> str:
    """
    Send a message and get a response.
    Each call is automatically tracked in Live Telemetry!
    """
    # Add user message to history
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # Call OpenAI - this is automatically traced!
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        temperature=0.7,
        max_tokens=500
    )

    # Extract response
    assistant_message = response.choices[0].message.content

    # Add to history
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    # Show token usage
    usage = response.usage
    print(f"\n📊 Tokens: {usage.total_tokens} ({usage.prompt_tokens} + {usage.completion_tokens})")
    print(f"💰 Cost: ~${usage.total_tokens * 0.00000015:.6f}\n")

    return assistant_message


def main():
    """Run the interactive chatbot"""
    print("=" * 70)
    print("🤖 INTERACTIVE CHATBOT WITH LIVE TELEMETRY")
    print("=" * 70)
    print()
    print("💬 Ask me anything! Each query is tracked in real-time.")
    print("📡 Watch: http://localhost:5173/live")
    print()
    print("Commands:")
    print("  - Type your question and press Enter")
    print("  - Type 'exit' or 'quit' to stop")
    print("  - Type 'clear' to reset conversation history")
    print()
    print("=" * 70)
    print()

    while True:
        try:
            # Get user input
            user_input = input("You: ").strip()

            # Check for exit commands
            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye! Check your Live Telemetry dashboard for the full conversation.\n")
                break

            # Check for clear command
            if user_input.lower() == 'clear':
                conversation_history.clear()
                conversation_history.append({
                    "role": "system",
                    "content": "You are a helpful AI assistant. Keep responses concise and friendly."
                })
                print("\n🔄 Conversation history cleared!\n")
                continue

            # Skip empty input
            if not user_input:
                continue

            # Get response
            print("\n🤖 Assistant: ", end="", flush=True)
            response = chat(user_input)
            print(response)

        except KeyboardInterrupt:
            print("\n\n👋 Goodbye! Check your Live Telemetry dashboard.\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}\n")
            print("Check your API key and internet connection.\n")


if __name__ == "__main__":
    # Check for OpenAI key
    if not os.environ.get("OPENAI_API_KEY"):
        print("❌ ERROR: OPENAI_API_KEY not set!")
        print()
        print("Set it with:")
        print('  export OPENAI_API_KEY="sk-..."')
        print()
        exit(1)

    main()