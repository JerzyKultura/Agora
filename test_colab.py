"""
Agora Telemetry Test for Google Colab
======================================

This script tests if your Agora telemetry is working from Google Colab.
You'll be able to see the chat messages in your localhost dashboard!

Instructions:
1. Fill in your API keys below (STEP 1)
2. Run this entire cell
3. Open http://localhost:5173/monitoring on your laptop
4. Go to the "Traces" tab
5. Click the trace that appears
6. Click the "openai.chat" span
7. See your chat messages in the Prompt and Completions tabs!

"""

# ============================================================================
# STEP 1: FILL IN YOUR API KEYS HERE
# ============================================================================

OPENAI_API_KEY = "sk-proj-YOUR_OPENAI_KEY_HERE"  # ← PUT YOUR OPENAI KEY HERE
SUPABASE_URL = "https://tfueafatqxspitjcbukq.supabase.co"  # ← Already filled in
SUPABASE_ANON_KEY = "YOUR_SUPABASE_ANON_KEY_HERE"  # ← PUT YOUR SUPABASE KEY HERE

# ============================================================================
# Install dependencies
# ============================================================================

print("📦 Installing dependencies...")
!pip install -q traceloop-sdk openai supabase python-dotenv

print("✅ Dependencies installed!\n")

# ============================================================================
# Set environment variables
# ============================================================================

import os

os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
os.environ["VITE_SUPABASE_URL"] = SUPABASE_URL
os.environ["VITE_SUPABASE_ANON_KEY"] = SUPABASE_ANON_KEY

print("✅ Environment variables set!\n")

# ============================================================================
# Clone Agora SDK (if not already cloned)
# ============================================================================

import sys
import os

if not os.path.exists('/content/Agora'):
    print("📥 Cloning Agora SDK...")
    !git clone https://github.com/JerzyKultura/Agora.git /content/Agora
    print("✅ Agora cloned!\n")
else:
    print("✅ Agora already exists!\n")

# Add to Python path
sys.path.insert(0, '/content/Agora')

# ============================================================================
# Initialize Telemetry
# ============================================================================

print("🔧 Initializing telemetry systems...\n")

# Initialize Traceloop (auto-instruments OpenAI)
from traceloop.sdk import Traceloop
Traceloop.init(
    app_name="colab-test",
    disable_batch=True  # Send immediately for real-time viewing
)
print("✅ Traceloop initialized!")

# Initialize Agora
from agora.agora_tracer import init_agora
init_agora(
    app_name="colab-test",
    project_name="Colab Test",
    enable_cloud_upload=True  # This sends to Supabase!
)
print("✅ Agora initialized!\n")

# ============================================================================
# Make a test LLM call
# ============================================================================

from openai import OpenAI

print("=" * 70)
print("🤖 Making a test LLM call to OpenAI...")
print("=" * 70)

client = OpenAI()

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",  # Using cheaper model for testing
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant testing the Agora telemetry system."
            },
            {
                "role": "user",
                "content": "Hello from Google Colab! Can you confirm you received this message? Reply with: 'Message received from Colab!'"
            }
        ],
        temperature=0.7,
        max_tokens=50
    )

    print("\n✅ LLM Call Successful!\n")
    print("📝 AI Response:")
    print("-" * 70)
    print(response.choices[0].message.content)
    print("-" * 70)
    print()

    # Print telemetry info
    print("📊 Telemetry Information:")
    print(f"   Model: {response.model}")
    print(f"   Tokens Used: {response.usage.total_tokens}")
    print(f"   - Prompt: {response.usage.prompt_tokens}")
    print(f"   - Completion: {response.usage.completion_tokens}")
    print()

except Exception as e:
    print(f"\n❌ Error: {e}\n")
    print("Please check your OPENAI_API_KEY is correct!")
    raise

# ============================================================================
# Instructions for viewing in dashboard
# ============================================================================

print("=" * 70)
print("🎉 TEST COMPLETE!")
print("=" * 70)
print()
print("Now check your localhost dashboard:")
print()
print("1. On your laptop, open: http://localhost:5173/monitoring")
print("2. Click the 'Traces' tab (should be selected by default)")
print("3. You should see a new trace called 'colab-test' or 'openai.chat'")
print("4. Click on that trace")
print("5. In the left panel, click the 'openai.chat' span")
print("6. On the right, you'll see tabs:")
print()
print("   📝 Prompt Tab - Should show:")
print("      - SYSTEM: You are a helpful assistant testing...")
print("      - USER: Hello from Google Colab! Can you confirm...")
print()
print("   💬 Completions Tab - Should show:")
print("      - ASSISTANT: Message received from Colab!")
print()
print("   📊 LLM Data Tab - Should show:")
print("      - Model: gpt-4o-mini")
print("      - Provider: openai")
print("      - Token usage and cost")
print()
print("=" * 70)
print()
print("🔍 If you don't see the trace:")
print("   1. Wait 5-10 seconds and refresh the page")
print("   2. Check that your frontend is running (npm run dev)")
print("   3. Verify SUPABASE_ANON_KEY is correct")
print()
print("💡 The telemetry was sent to:")
print(f"   {SUPABASE_URL}")
print()
print("✅ All data is stored permanently in Supabase!")
print("=" * 70)
