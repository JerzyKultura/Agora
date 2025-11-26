"""
=============================================================================
AGORA CLOUD + OPENAI CHATBOT - COLAB DEMO
=============================================================================

Copy and paste this entire file into Google Colab to test:
1. OpenAI API key
2. Agora API key (optional)
3. Full chatbot with telemetry

Instructions:
1. Run cell 1 to install
2. Run cell 2 to set your keys
3. Run cell 3 to chat!
"""

# =============================================================================
# CELL 1: INSTALL DEPENDENCIES
# =============================================================================
# Run this first!

"""
!pip install --quiet openai
!pip install --quiet git+https://github.com/JerzyKultura/Agora.git
"""

# =============================================================================
# CELL 2: SET YOUR API KEYS
# =============================================================================
# Replace with your actual keys

import os

# REQUIRED: Your OpenAI API key
os.environ["OPENAI_API_KEY"] = "sk-..."  # <- Paste your OpenAI key here

# OPTIONAL: Your Agora Cloud API key (get from https://your-platform.com/settings)
os.environ["AGORA_API_KEY"] = ""  # <- Paste your Agora key here (or leave empty)

print("✓ Keys configured!")
print(f"  OpenAI: {'✓ Set' if os.environ.get('OPENAI_API_KEY', '').startswith('sk-') else '✗ Missing'}")
print(f"  Agora:  {'✓ Set' if os.environ.get('AGORA_API_KEY', '').startswith('agora_') else '○ Not set (will run in local mode)'}")

# =============================================================================
# CELL 3: RUN THE CHATBOT
# =============================================================================
# Run this to start chatting!

import asyncio
from openai import OpenAI
from agora.agora_tracer import (
    init_traceloop,
    agora_node,
    TracedAsyncFlow
)

# Initialize tracing - Direct Supabase Upload
SUPABASE_URL = os.environ.get("VITE_SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("VITE_SUPABASE_ANON_KEY", "")

# Set Traceloop API key for OpenAI instrumentation
TRACELOOP_KEY = os.environ.get("TRACELOOP_API_KEY", "dummy_key")
os.environ["TRACELOOP_API_KEY"] = TRACELOOP_KEY

if SUPABASE_URL and SUPABASE_KEY:
    print(f"\n✓ Connected to Supabase")
    print(f"URL: {SUPABASE_URL}")
    print(f"View telemetry in your platform's monitoring page\n")
    enable_upload = True
else:
    print("\n⚠️  Running in LOCAL MODE (no cloud sync)")
    print("To sync with cloud, set VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY\n")
    enable_upload = False

init_traceloop(
    app_name="colab_chatbot",
    export_to_console=True,
    export_to_file="chatbot_traces.jsonl",
    enable_cloud_upload=enable_upload,
    project_name="Colab Chatbot"
)

# Create OpenAI client
client = OpenAI()

@agora_node(name="ChatInput")
async def chat_input(shared):
    """Get user input"""
    if "messages" not in shared:
        shared["messages"] = []
        shared["turn"] = 0
        print("=" * 60)
        print("CHATBOT READY")
        print("=" * 60)
        print("Type your message and press Enter")
        print("Type 'exit' or 'quit' to stop")
        print("=" * 60)

    try:
        user_input = input(f"\n[{shared['turn']}] You: ").strip()
    except (EOFError, KeyboardInterrupt):
        user_input = "exit"

    if user_input.lower() in ['exit', 'quit', '']:
        return "exit"

    shared["messages"].append({"role": "user", "content": user_input})
    return "respond"

@agora_node(name="GetResponse")
async def get_response(shared):
    """Get AI response from OpenAI"""
    print(f"[{shared['turn']}] Bot: ", end="", flush=True)

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=shared["messages"],
            temperature=0.7,
            max_tokens=500,
            stream=True
        )

        full_response = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                full_response += content

        print()

        shared["messages"].append({"role": "assistant", "content": full_response})
        shared["turn"] += 1

        return "input"

    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        if "authentication" in str(e).lower() or "api_key" in str(e).lower():
            print("Check your OPENAI_API_KEY in Cell 2!")
        return "exit"

@agora_node(name="Exit")
async def exit_chat(shared):
    """Exit the chat"""
    print("\n" + "=" * 60)
    print(f"Goodbye! You had {shared.get('turn', 0)} conversations.")
    print("=" * 60)

    if AGORA_KEY:
        print("\n✓ Telemetry sent to Agora Cloud")
        print("View at: https://your-platform.com/monitoring")
    else:
        print("\nℹ️  Telemetry saved to: chatbot_traces.jsonl")

    return None

async def run_chatbot():
    """Run the chatbot workflow"""
    flow = TracedAsyncFlow("ColabChatbot")
    flow.start(chat_input)

    chat_input - "respond" >> get_response
    chat_input - "exit" >> exit_chat
    get_response - "input" >> chat_input
    get_response - "exit" >> exit_chat

    shared = {}
    await flow.run_async(shared)

    print("\n" + "=" * 60)
    print("WORKFLOW DIAGRAM")
    print("=" * 60)
    print(flow.to_mermaid())

# Run the chatbot
# Note: In Colab/Jupyter, use 'await' instead of 'asyncio.run()'
# because there's already an event loop running
await run_chatbot()


# =============================================================================
# TROUBLESHOOTING
# =============================================================================

"""
Problem: "AuthenticationError"
Solution:
  - Check your OPENAI_API_KEY in Cell 2
  - Make sure it starts with 'sk-'
  - Get a key from: https://platform.openai.com/api-keys

Problem: "Module not found"
Solution:
  - Re-run Cell 1 to install dependencies
  - Make sure the pip install commands succeeded

Problem: "Agora key invalid"
Solution:
  - Check your AGORA_API_KEY in Cell 2
  - Make sure it starts with 'agora_'
  - Generate a new key at: https://your-platform.com/settings
  - Or leave it empty to run in local mode

Problem: Chat not responding
Solution:
  - Check your internet connection
  - Check OpenAI API status: https://status.openai.com
  - Try a different model (change 'gpt-4o-mini' to 'gpt-3.5-turbo')
"""
