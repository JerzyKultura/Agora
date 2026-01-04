"""
Simple Test: Check if Wide Events Business Context is Working

This tests if the business context attributes actually show up in Supabase.
"""

import os
import sys

# Load .env file FIRST
from dotenv import load_dotenv
import pathlib

# Get the directory where this script is located
script_dir = pathlib.Path(__file__).parent.resolve()
env_file = script_dir / ".env"

print("=" * 70)
print("🔍 Testing Wide Events Business Context")
print("=" * 70)
print()
print(f"📁 Script directory: {script_dir}")
print(f"📄 Looking for .env at: {env_file}")
print(f"📄 .env exists: {env_file.exists()}")

# Load the .env file
loaded = load_dotenv(env_file)
print(f"📄 .env loaded: {loaded}")
print()
print("=" * 70)
print()

# Check environment variables
print("1️⃣ Checking Environment Variables...")
print()

supabase_url = os.getenv("VITE_SUPABASE_URL")
supabase_key = os.getenv("VITE_SUPABASE_ANON_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

if not supabase_url:
    print("❌ VITE_SUPABASE_URL not set!")
    print()
    print("   Make sure your .env file contains (WITHOUT quotes):")
    print("   VITE_SUPABASE_URL=https://tfueafatqxspitjcbukq.supabase.co")
    print()
    print("   Or export it:")
    print("   export VITE_SUPABASE_URL='https://tfueafatqxspitjcbukq.supabase.co'")
    sys.exit(1)
else:
    print(f"✅ VITE_SUPABASE_URL: {supabase_url}")

if not supabase_key:
    print("❌ VITE_SUPABASE_ANON_KEY not set!")
    print("   Set it in .env file or export it:")
    print("   export VITE_SUPABASE_ANON_KEY='eyJhbGci...'")
    sys.exit(1)
else:
    print(f"✅ VITE_SUPABASE_ANON_KEY: {supabase_key[:10]}...{supabase_key[-10:]}")

if not openai_key:
    print("❌ OPENAI_API_KEY not set!")
    print("   Set it in .env file or export it:")
    print("   export OPENAI_API_KEY='sk-proj-...'")
    sys.exit(1)
else:
    print(f"✅ OPENAI_API_KEY: {openai_key[:10]}...{openai_key[-4:]}")

print()
print("=" * 70)
print()

# Initialize telemetry
print("2️⃣ Initializing Telemetry...")
print()

from traceloop.sdk import Traceloop
Traceloop.init(app_name="wide-events-test", disable_batch=True)
print("✅ Traceloop initialized")

from agora.agora_tracer import init_agora
init_agora(
    app_name="wide-events-test",
    project_name="Wide Events Test",
    enable_cloud_upload=True
)
print("✅ Agora initialized")

print()
print("=" * 70)
print()

# Import wide events
print("3️⃣ Importing Wide Events Module...")
print()

from agora.wide_events import BusinessContext, enrich_current_span
print("✅ Wide events module imported")

print()
print("=" * 70)
print()

# Make a test LLM call with business context
print("4️⃣ Making Test LLM Call with Business Context...")
print()

from openai import OpenAI
client = OpenAI()

# Create business context
context = BusinessContext(
    user_id="test_user_999",
    user_email="test@example.com",
    subscription_tier="premium",
    lifetime_value_cents=75000,  # $750 LTV
    account_age_days=200,
    session_id="test_session_abc",
    conversation_turn=1,
    feature_flags={
        "new_ui": True,
        "advanced_features": True,
        "beta_access": False
    },
    workflow_type="testing",
    priority="high",
    custom={
        "test_run": True,
        "test_timestamp": "2026-01-04"
    }
)

print("📊 Business Context Created:")
print(f"   - User ID: {context.user_id}")
print(f"   - Subscription: {context.subscription_tier}")
print(f"   - LTV: ${context.lifetime_value_cents / 100}")
print(f"   - Feature Flags: {len(context.feature_flags)} flags")
print(f"   - Custom Attrs: {len(context.custom)} attributes")
print()

# Enrich the span BEFORE making the LLM call
enrich_current_span(context)
print("✅ Span enriched with business context")
print()

# Make the LLM call
print("📞 Calling OpenAI...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a test assistant."},
        {"role": "user", "content": "Say 'Business context test successful!' in one sentence."}
    ],
    max_tokens=50
)

print("✅ LLM call complete!")
print()
print(f"🤖 Response: {response.choices[0].message.content}")
print()

# Wait for telemetry to be uploaded to Supabase
print("⏳ Waiting for telemetry to upload to Supabase...")
import time
time.sleep(3)
print("✅ Upload complete!")
print()

print("=" * 70)
print()
print("5️⃣ Now Check Your Dashboard!")
print()
print("1. Open: http://localhost:5173/monitoring")
print("2. Click 'Traces' tab")
print("3. Find the trace (should be at the top)")
print("4. Click on the trace")
print("5. Click the 'openai.chat' span in the left panel")
print("6. Click the 'Details' tab on the right")
print()
print("📋 Look for these attributes:")
print("   ✓ user.id = 'test_user_999'")
print("   ✓ user.subscription_tier = 'premium'")
print("   ✓ user.lifetime_value_cents = 75000")
print("   ✓ user.account_age_days = 200")
print("   ✓ feature_flags.new_ui = True")
print("   ✓ feature_flags.advanced_features = True")
print("   ✓ app.workflow_type = 'testing'")
print("   ✓ app.priority = 'high'")
print("   ✓ custom.test_run = True")
print()
print("7. Also check the 'Raw' tab to see ALL attributes")
print()
print("=" * 70)
print()
print("💡 What Credentials Were Needed?")
print()
print("✅ REQUIRED:")
print("   - VITE_SUPABASE_URL (to send data to Supabase)")
print("   - VITE_SUPABASE_ANON_KEY (to authenticate with Supabase)")
print("   - OPENAI_API_KEY (to make LLM calls)")
print()
print("❌ NOT REQUIRED:")
print("   - AGORA_API_KEY (optional, only for project association)")
print("   - AGORA_PROJECT_ID (optional, only for project association)")
print()
print("The telemetry flows:")
print("  Python Script → Traceloop SDK → Agora SDK → Supabase Cloud")
print("                                              ↓")
print("                                  Your Browser reads from Supabase")
print()
print("=" * 70)
