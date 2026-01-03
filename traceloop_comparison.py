#!/usr/bin/env python3
"""
Traceloop Comparison Demo - Works Locally & in Google Colab
============================================================

This demo sends telemetry to BOTH:
1. Traceloop Dashboard (https://app.traceloop.com)
2. Your Agora Platform (http://localhost:5173/live)

Run this to compare the two telemetry systems side-by-side!

LOCAL SETUP:
1. Create .env file with your API keys (see .env.example)
2. Run: python3 traceloop_comparison.py
3. Choose demo or interactive mode
4. View telemetry in both dashboards

COLAB SETUP:
1. Copy this entire file into a Colab cell
2. Uncomment the !pip install line below
3. Set your API keys in the COLAB CONFIGURATION section
4. Run the cell

"""

# ============================================================================
# GOOGLE COLAB: Install dependencies
# ============================================================================
# Uncomment these lines if running in Google Colab:

# !pip install -q traceloop-sdk openai supabase python-dotenv

# ============================================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================================

import os

# Try to load .env file (for local development)
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("✅ Loaded credentials from .env file")
except ImportError:
    print("⚠️  python-dotenv not installed, using hardcoded values")
except:
    pass

# ============================================================================
# CONFIGURATION - For Colab users, set your keys here
# ============================================================================

# If running in Colab, set your keys here (otherwise they'll be loaded from .env)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "sk-...")  # ← Replace in Colab
TRACELOOP_API_KEY = os.getenv("TRACELOOP_API_KEY", "tl_6894c89d3a0343afab2828f7cf371a25")
AGORA_SUPABASE_URL = os.getenv("VITE_SUPABASE_URL", "")
AGORA_SUPABASE_KEY = os.getenv("VITE_SUPABASE_ANON_KEY", "")
AGORA_API_KEY = os.getenv("AGORA_API_KEY", "")
AGORA_PROJECT_ID = os.getenv("AGORA_PROJECT_ID", "")

# Set environment variables for libraries to use
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
if AGORA_SUPABASE_URL:
    os.environ["VITE_SUPABASE_URL"] = AGORA_SUPABASE_URL
    os.environ["VITE_SUPABASE_ANON_KEY"] = AGORA_SUPABASE_KEY
if AGORA_API_KEY:
    os.environ["AGORA_API_KEY"] = AGORA_API_KEY
    os.environ["AGORA_PROJECT_ID"] = AGORA_PROJECT_ID

# ============================================================================
# INITIALIZE TRACELOOP
# ============================================================================

from traceloop.sdk import Traceloop
from openai import OpenAI

print("🔧 Initializing Traceloop SDK...")
Traceloop.init(
    app_name="comparison-chatbot",
    disable_batch=True,  # Send immediately for real-time viewing
    api_key=TRACELOOP_API_KEY
)

print("✅ Traceloop initialized!")
print("📊 View telemetry at: https://app.traceloop.com")
print()

# ============================================================================
# OPTIONAL: ALSO SEND TO AGORA (if you want to compare both)
# ============================================================================

SEND_TO_AGORA = bool(AGORA_SUPABASE_URL and AGORA_SUPABASE_KEY)

if SEND_TO_AGORA:
    try:
        from agora.agora_tracer import init_agora

        print("🔧 Also initializing Agora telemetry...")
        init_agora(
            app_name="comparison-chatbot",
            project_name="Traceloop Comparison",
            enable_cloud_upload=True,
            export_to_console=False
        )
        print("✅ Agora telemetry enabled!")
        print("📊 View at: http://localhost:5173/live")
        print()
    except ImportError:
        print("⚠️  Agora not installed. Install with: pip install -e .")
        print("    Continuing with Traceloop-only mode...")
        SEND_TO_AGORA = False
        print()

# ============================================================================
# CHATBOT
# ============================================================================

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant. Keep responses concise."
    }
]

def chat(user_message: str) -> str:
    """
    Send a message and get a response.
    Automatically traced by Traceloop!
    """
    conversation_history.append({
        "role": "user",
        "content": user_message
    })

    # This call is automatically instrumented by Traceloop
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        temperature=0.7,
        max_tokens=300
    )

    assistant_message = response.choices[0].message.content
    conversation_history.append({
        "role": "assistant",
        "content": assistant_message
    })

    # Show token usage
    usage = response.usage
    print(f"📊 Tokens: {usage.total_tokens} ({usage.prompt_tokens} + {usage.completion_tokens})")
    print(f"💰 Cost: ~${usage.total_tokens * 0.00000015:.6f}")

    return assistant_message


# ============================================================================
# INTERACTIVE MODE (for Colab)
# ============================================================================

def run_interactive():
    """Run interactive chatbot in Colab"""
    print("=" * 70)
    print("🤖 TRACELOOP COMPARISON CHATBOT")
    print("=" * 70)
    print()
    print("💬 Ask me anything!")
    print("📡 Telemetry is being sent to:")
    print("   • Traceloop: https://app.traceloop.com")
    if SEND_TO_AGORA:
        print("   • Agora: http://localhost:5173/live")
    print()
    print("Type 'exit' to quit")
    print()
    print("=" * 70)
    print()

    while True:
        try:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ['exit', 'quit', 'q']:
                print("\n👋 Goodbye!")
                print()
                print("📊 Check your dashboards:")
                print("   • Traceloop: https://app.traceloop.com")
                if SEND_TO_AGORA:
                    print("   • Agora: http://localhost:5173/live")
                print()
                break

            if not user_input:
                continue

            print("\n🤖 Assistant: ", end="", flush=True)
            response = chat(user_input)
            print(response)
            print()

        except KeyboardInterrupt:
            print("\n\n👋 Interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Check your API keys and internet connection.\n")


# ============================================================================
# DEMO MODE (runs 3 preset queries)
# ============================================================================

def run_demo():
    """Run automated demo with preset queries"""
    print("=" * 70)
    print("🤖 TRACELOOP COMPARISON DEMO")
    print("=" * 70)
    print()
    print("Running 3 example queries...")
    print("Watch the telemetry appear in:")
    print("   • Traceloop: https://app.traceloop.com")
    if SEND_TO_AGORA:
        print("   • Agora: http://localhost:5173/live")
    print()
    print("=" * 70)
    print()

    queries = [
        "What is machine learning?",
        "Explain neural networks in simple terms",
        "What's the difference between AI and ML?"
    ]

    for i, query in enumerate(queries, 1):
        print(f"\n{'=' * 70}")
        print(f"QUERY {i}/{len(queries)}")
        print(f"{'=' * 70}\n")
        print(f"👤 You: {query}\n")
        print("🤖 Assistant: ", end="", flush=True)

        response = chat(query)
        print(response)
        print()

        if i < len(queries):
            print("⏳ Waiting 2 seconds before next query...")
            import time
            time.sleep(2)

    print()
    print("=" * 70)
    print("✅ Demo complete!")
    print("=" * 70)
    print()
    print("📊 Now check your dashboards:")
    print("   • Traceloop: https://app.traceloop.com")
    if SEND_TO_AGORA:
        print("   • Agora: http://localhost:5173/live")
    print()
    print("You should see:")
    print("   • All 3 queries and responses")
    print("   • Token usage for each call")
    print("   • Model info (gpt-4o-mini)")
    print("   • Temperature (0.7)")
    print()


# ============================================================================
# RUN
# ============================================================================

if __name__ == "__main__":
    # Check if OpenAI key is set
    if OPENAI_API_KEY == "sk-...":
        print("❌ ERROR: Please set your OPENAI_API_KEY in the code!")
        print()
        print("Find it here: https://platform.openai.com/api-keys")
        print()
    else:
        # Choose mode
        print("Choose mode:")
        print("1. Demo mode (3 preset queries)")
        print("2. Interactive mode (ask your own questions)")
        print()

        # In Colab, default to demo mode
        try:
            import google.colab
            print("🎮 Running in Colab - starting demo mode...")
            print()
            run_demo()
        except:
            # Not in Colab, ask user
            choice = input("Enter 1 or 2: ").strip()
            print()

            if choice == "1":
                run_demo()
            else:
                run_interactive()