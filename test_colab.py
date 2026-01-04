"""
Agora Telemetry Test for Google Colab - With Business Context Enrichment
=========================================================================

This script demonstrates the "wide events" pattern - enriching your telemetry
with business context to make debugging 100x easier.

Instructions:
1. Paste your API keys in STEP 1 below
2. Run this entire cell
3. Open http://localhost:5173/monitoring on your laptop
4. Go to the "Traces" tab
5. Click the trace → Click "openai.chat" span → See the magic!

You'll see:
- Prompt & Completions tabs (the chat messages)
- LLM Data tab (model, tokens, cost)
- Details tab with YOUR BUSINESS CONTEXT:
  - User subscription tier
  - Feature flags
  - Session info
  - Custom app context
"""

# ============================================================================
# STEP 1: PASTE YOUR API KEYS HERE
# ============================================================================

# Get your OpenAI key from: https://platform.openai.com/api-keys
OPENAI_API_KEY = ""  # ← PASTE YOUR KEY: sk-proj-...

# Get these from your Agora .env file or Supabase dashboard
SUPABASE_URL = "https://tfueafatqxspitjcbukq.supabase.co"
SUPABASE_ANON_KEY = ""  # ← PASTE YOUR KEY: eyJhbGci...

# ============================================================================
# Validation
# ============================================================================

if not OPENAI_API_KEY or OPENAI_API_KEY == "":
    print("❌ ERROR: Please paste your OPENAI_API_KEY above!")
    print("   Get it from: https://platform.openai.com/api-keys")
    raise ValueError("OPENAI_API_KEY not set")

if not SUPABASE_ANON_KEY or SUPABASE_ANON_KEY == "":
    print("❌ ERROR: Please paste your SUPABASE_ANON_KEY above!")
    print("   Find it in your .env file: VITE_SUPABASE_ANON_KEY=...")
    raise ValueError("SUPABASE_ANON_KEY not set")

print("✅ API keys validated!\n")

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
    app_name="colab-wide-events-demo",
    disable_batch=True  # Send immediately for real-time viewing
)
print("✅ Traceloop initialized!")

# Initialize Agora
from agora.agora_tracer import init_agora
init_agora(
    app_name="colab-wide-events-demo",
    project_name="Colab Wide Events Demo",
    enable_cloud_upload=True  # This sends to Supabase!
)
print("✅ Agora initialized!\n")

# ============================================================================
# Import Business Context Enrichment
# ============================================================================

from agora.wide_events import (
    BusinessContext,
    enrich_current_span,
    enrich_with_user,
    enrich_with_feature_flags
)

print("✅ Wide events module loaded!\n")

# ============================================================================
# DEMO 1: Basic LLM call with business context
# ============================================================================

from openai import OpenAI

print("=" * 70)
print("🎯 DEMO 1: LLM Call with Business Context")
print("=" * 70)
print()

client = OpenAI()

# Build business context (this is what makes debugging powerful!)
context = BusinessContext(
    # User context
    user_id="user_colab_123",
    user_email="test@example.com",
    subscription_tier="premium",  # This helps prioritize issues!
    lifetime_value_cents=50000,   # $500 LTV - important customer!
    account_age_days=120,          # Been with us 4 months

    # Session context
    session_id="sess_colab_abc",
    conversation_turn=1,           # First message in conversation
    total_tokens_this_session=0,

    # Feature flags (track experiments!)
    feature_flags={
        "new_chat_ui": True,
        "gpt4_access": True,
        "experimental_mode": False
    },

    # App-specific context
    workflow_type="testing",       # vs "customer_support", "sales", etc.
    priority="low",                # vs "high" for VIP users
    app_version="1.0.0-colab",

    # Custom attributes (anything you want!)
    custom={
        "test_environment": "google_colab",
        "test_purpose": "wide_events_demo",
        "tester_location": "colab_notebook"
    }
)

# Enrich the span with business context BEFORE making the LLM call
# This is the key! Now when you debug, you'll have ALL this context
enrich_current_span(context)

print("📝 Making LLM call with enriched context...")

try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a helpful assistant demonstrating Agora's wide events telemetry system."
            },
            {
                "role": "user",
                "content": "Hello from Google Colab! I'm testing the wide events pattern. Can you confirm you received this?"
            }
        ],
        temperature=0.7,
        max_tokens=100
    )

    print("\n✅ LLM Call Successful!\n")
    print("🤖 AI Response:")
    print("-" * 70)
    print(response.choices[0].message.content)
    print("-" * 70)
    print()

    print("📊 Token Usage:")
    print(f"   Prompt tokens: {response.usage.prompt_tokens}")
    print(f"   Completion tokens: {response.usage.completion_tokens}")
    print(f"   Total: {response.usage.total_tokens}")
    print()

except Exception as e:
    print(f"\n❌ Error: {e}\n")
    raise

# ============================================================================
# DEMO 2: Quick helper methods
# ============================================================================

print("=" * 70)
print("🎯 DEMO 2: Using Quick Helper Methods")
print("=" * 70)
print()

# Quick helper for user enrichment
enrich_with_user(
    user_id="user_456",
    subscription_tier="enterprise",
    lifetime_value_cents=100000  # $1000 LTV - VIP!
)

# Quick helper for feature flags
enrich_with_feature_flags({
    "beta_features": True,
    "advanced_analytics": True
})

print("📝 Making second LLM call with quick helpers...")

response2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Second test message with quick helpers!"}
    ],
    max_tokens=50
)

print("✅ Second call complete!")
print(f"🤖 Response: {response2.choices[0].message.content}\n")

# ============================================================================
# Instructions for viewing in dashboard
# ============================================================================

print("=" * 70)
print("🎉 TEST COMPLETE!")
print("=" * 70)
print()
print("Now check your localhost dashboard:")
print()
print("1. Open: http://localhost:5173/monitoring")
print("2. Click the 'Traces' tab")
print("3. Find traces named 'openai.chat' or 'colab-wide-events-demo'")
print("4. Click on a trace")
print("5. Click the 'openai.chat' span in the left panel")
print("6. On the right, explore these tabs:")
print()
print("   📝 Prompt Tab:")
print("      - See SYSTEM and USER messages")
print()
print("   💬 Completions Tab:")
print("      - See ASSISTANT response")
print()
print("   📊 LLM Data Tab:")
print("      - Model: gpt-4o-mini")
print("      - Token usage")
print("      - Cost")
print()
print("   🔍 Details Tab - THIS IS THE MAGIC:")
print("      Look for attributes like:")
print("      - user.id = 'user_colab_123'")
print("      - user.subscription_tier = 'premium'")
print("      - user.lifetime_value_cents = 50000")
print("      - user.account_age_days = 120")
print("      - feature_flags.new_chat_ui = True")
print("      - feature_flags.gpt4_access = True")
print("      - app.workflow_type = 'testing'")
print("      - custom.test_environment = 'google_colab'")
print()
print("   📄 Raw Tab:")
print("      - See the complete JSON with ALL attributes")
print()
print("=" * 70)
print()
print("💡 Why This Matters:")
print()
print("When a user reports an issue, you can now ask:")
print()
print('  "Show me errors for premium users only"')
print('  "What\'s the error rate for users with new_chat_ui enabled?"')
print('  "Find all slow requests for enterprise customers"')
print('  "Show me all failed requests from users with >$500 LTV"')
print()
print("All of this is queryable because you enriched the spans!")
print("=" * 70)
print()
print("🎯 Next Steps:")
print()
print("1. In your actual application, build a BusinessContext object")
print("2. Call enrich_current_span() BEFORE your LLM calls")
print("3. Add context like user tier, feature flags, session info")
print("4. Debug 100x faster with full context in every trace")
print()
print("Read agora/wide_events.py for more examples!")
print("=" * 70)
