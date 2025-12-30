"""
🚀 GOOGLE COLAB SETUP SCRIPT
============================

This script sets up your Google Colab environment to run Agora demos.

INSTRUCTIONS:
1. In Colab, click the 🔑 key icon in the left sidebar
2. Add these secrets:
   - OPENAI_API_KEY (required)
   - TRACELOOP_API_KEY (optional, defaults to provided key)
   - AGORA_SUPABASE_URL (optional, for comparison)
   - AGORA_SUPABASE_KEY (optional, for comparison)
   - AGORA_API_KEY (optional, for comparison)
   - AGORA_PROJECT_ID (optional, for comparison)

3. Run this cell
4. Choose which demo to run below

OR: Skip the secrets and just hardcode them below (less secure but faster)
"""

# ============================================================================
# STEP 1: Install dependencies
# ============================================================================

print("📦 Installing dependencies...")
get_ipython().system('pip install -q traceloop-sdk openai supabase')
print("✅ Core dependencies installed")

# Ask if user wants to install Agora for comparison
install_agora = input("\n🤔 Install Agora for side-by-side comparison? (y/n): ").strip().lower()
if install_agora == 'y':
    print("📦 Installing Agora from GitHub...")
    get_ipython().system('pip install -q git+https://github.com/JerzyKultura/Agora.git')
    print("✅ Agora installed")
    ENABLE_AGORA = True
else:
    print("⏭️  Skipping Agora installation")
    ENABLE_AGORA = False

print()

# ============================================================================
# STEP 2: Load credentials
# ============================================================================

print("🔐 Loading credentials...")

# Try to load from Colab secrets first
try:
    from google.colab import userdata

    # OpenAI (required)
    try:
        OPENAI_API_KEY = userdata.get('OPENAI_API_KEY')
        print("✅ OpenAI API key loaded from secrets")
    except:
        OPENAI_API_KEY = input("Enter your OpenAI API key: ").strip()
        print("✅ OpenAI API key entered manually")

    # Traceloop (optional, has default)
    try:
        TRACELOOP_API_KEY = userdata.get('TRACELOOP_API_KEY')
        print("✅ Traceloop API key loaded from secrets")
    except:
        TRACELOOP_API_KEY = "tl_6894c89d3a0343afab2828f7cf371a25"
        print("✅ Using default Traceloop API key")

    # Agora credentials (optional)
    if ENABLE_AGORA:
        try:
            AGORA_SUPABASE_URL = userdata.get('AGORA_SUPABASE_URL')
            AGORA_SUPABASE_KEY = userdata.get('AGORA_SUPABASE_KEY')
            AGORA_API_KEY = userdata.get('AGORA_API_KEY')
            AGORA_PROJECT_ID = userdata.get('AGORA_PROJECT_ID')
            print("✅ Agora credentials loaded from secrets")
        except:
            print("⚠️  Agora credentials not found in secrets. Agora telemetry will be disabled.")
            AGORA_SUPABASE_URL = ""
            AGORA_SUPABASE_KEY = ""
            AGORA_API_KEY = ""
            AGORA_PROJECT_ID = ""
            ENABLE_AGORA = False

except ImportError:
    # Not in Colab, fallback to manual entry
    print("⚠️  Not running in Colab, using manual entry...")
    OPENAI_API_KEY = input("Enter your OpenAI API key: ").strip()
    TRACELOOP_API_KEY = input("Enter your Traceloop API key (or press Enter for default): ").strip() or "tl_6894c89d3a0343afab2828f7cf371a25"

    if ENABLE_AGORA:
        AGORA_SUPABASE_URL = input("Enter Agora Supabase URL (or press Enter to skip): ").strip()
        if AGORA_SUPABASE_URL:
            AGORA_SUPABASE_KEY = input("Enter Agora Supabase Key: ").strip()
            AGORA_API_KEY = input("Enter Agora API Key: ").strip()
            AGORA_PROJECT_ID = input("Enter Agora Project ID: ").strip()
        else:
            ENABLE_AGORA = False

print()

# ============================================================================
# STEP 3: Set environment variables
# ============================================================================

import os

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY

if ENABLE_AGORA:
    os.environ["VITE_SUPABASE_URL"] = AGORA_SUPABASE_URL
    os.environ["VITE_SUPABASE_ANON_KEY"] = AGORA_SUPABASE_KEY
    os.environ["AGORA_API_KEY"] = AGORA_API_KEY
    os.environ["AGORA_PROJECT_ID"] = AGORA_PROJECT_ID

print("✅ Environment variables set")
print()

# ============================================================================
# STEP 4: Initialize telemetry
# ============================================================================

from traceloop.sdk import Traceloop
from openai import OpenAI

print("🔧 Initializing Traceloop...")
Traceloop.init(
    app_name="colab-demo",
    disable_batch=True,  # Real-time telemetry
    api_key=TRACELOOP_API_KEY
)
print("✅ Traceloop initialized!")
print("📊 View at: https://app.traceloop.com")
print()

if ENABLE_AGORA:
    print("🔧 Initializing Agora...")
    from agora.agora_tracer import init_agora

    init_agora(
        app_name="colab-demo",
        project_name="Colab Comparison",
        enable_cloud_upload=True,
        export_to_console=False
    )
    print("✅ Agora initialized!")
    print("📊 View at: http://localhost:5173/live (or your hosted URL)")
    print()

# ============================================================================
# STEP 5: Create chatbot
# ============================================================================

client = OpenAI(api_key=OPENAI_API_KEY)

conversation_history = [
    {
        "role": "system",
        "content": "You are a helpful AI assistant. Keep responses concise."
    }
]

def ask(question: str) -> str:
    """
    Ask a question and get an answer.
    Automatically traced by Traceloop (and Agora if enabled)!
    """
    print(f"\n💭 Question: {question}")
    print("🤖 Thinking...")

    conversation_history.append({
        "role": "user",
        "content": question
    })

    # This call is automatically instrumented!
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=conversation_history,
        temperature=0.7,
        max_tokens=300
    )

    answer = response.choices[0].message.content
    conversation_history.append({
        "role": "assistant",
        "content": answer
    })

    usage = response.usage
    print(f"\n💬 Answer: {answer}")
    print()
    print(f"📊 Stats:")
    print(f"   • Tokens: {usage.total_tokens} ({usage.prompt_tokens} + {usage.completion_tokens})")
    print(f"   • Cost: ~${usage.total_tokens * 0.00000015:.6f}")
    print(f"   • Model: gpt-4o-mini")
    print()

    return answer

# ============================================================================
# READY!
# ============================================================================

print("=" * 70)
print("✅ SETUP COMPLETE!")
print("=" * 70)
print()
print("You can now:")
print("1. Ask questions: ask('What is machine learning?')")
print("2. Run the demo below")
print()
print("Telemetry is being sent to:")
print("   • Traceloop: https://app.traceloop.com")
if ENABLE_AGORA:
    print("   • Agora: http://localhost:5173/live")
print()
print("=" * 70)
print()

# ============================================================================
# DEMO: Run 3 preset queries (optional)
# ============================================================================

run_demo = input("🎮 Run demo with 3 preset queries? (y/n): ").strip().lower()

if run_demo == 'y':
    print()
    print("=" * 70)
    print("🚀 RUNNING DEMO")
    print("=" * 70)

    queries = [
        "What is machine learning?",
        "Explain neural networks in simple terms",
        "What's the difference between AI and ML?"
    ]

    for i, query in enumerate(queries, 1):
        print()
        print("━" * 70)
        print(f"QUESTION {i}/{len(queries)}")
        print("━" * 70)
        ask(query)

        if i < len(queries):
            print("⏳ Waiting 2 seconds before next query...")
            import time
            time.sleep(2)

    print()
    print("=" * 70)
    print("✅ DEMO COMPLETE!")
    print("=" * 70)
    print()
    print("📊 Check your dashboards now!")
    print()

else:
    print()
    print("💡 You can ask questions anytime:")
    print("   ask('your question here')")
    print()
    print("Or start an interactive chat:")
    print()
    print("while True:")
    print("    q = input('Ask: ')")
    print("    if q.lower() == 'exit': break")
    print("    ask(q)")
    print()
