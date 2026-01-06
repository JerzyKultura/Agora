"""
Agora Wide Events Test - Google Colab (FIXED VERSION)
======================================================
Copy and paste this entire cell into Google Colab and run it!
"""

# ============================================================================
# STEP 1: FORCE FRESH INSTALL (Clear all caches!)
# ============================================================================
print("🧹 Clearing caches and installing fresh...")
import subprocess
import sys
import os
import shutil

# Force remove any cached Agora
for path in ["/content/Agora", "/usr/local/lib/python3.10/dist-packages/agora"]:
    if os.path.exists(path):
        shutil.rmtree(path)
        print(f"   Removed {path}")

# Uninstall if previously installed as package
subprocess.run([sys.executable, "-m", "pip", "uninstall", "-y", "agora"],
               capture_output=True)

# Install dependencies
print("📦 Installing dependencies...")
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
    "openai", "traceloop-sdk", "supabase", "opentelemetry-api",
    "opentelemetry-sdk", "python-dotenv"])

# Clone FRESH from the feature branch
print("📥 Cloning fresh from GitHub (claude/llm-token-tracking-VfDEH branch)...")
subprocess.check_call(["git", "clone", "-q", "https://github.com/JerzyKultura/Agora.git", "/content/Agora"])
subprocess.check_call(["git", "-C", "/content/Agora", "checkout", "-q", "claude/llm-token-tracking-VfDEH"])

# Add to path (don't pip install, just use directly)
sys.path.insert(0, "/content/Agora")

# Verify the function exists
print("🔍 Verifying set_business_context exists...")
with open("/content/Agora/agora/wide_events.py") as f:
    content = f.read()
    if "def set_business_context" in content:
        print("   ✅ Found set_business_context!")
    else:
        print("   ❌ NOT FOUND - please check GitHub")
        raise Exception("set_business_context not in file!")

print("✅ Setup complete!\n")

# ============================================================================
# STEP 2: Set Credentials (REPLACE WITH YOUR ACTUAL KEYS!)
# ============================================================================
print("🔑 Setting environment variables...")

# REQUIRED: Supabase credentials
os.environ["VITE_SUPABASE_URL"] = "YOUR_SUPABASE_URL_HERE"  # ← REPLACE!
os.environ["VITE_SUPABASE_ANON_KEY"] = "YOUR_SUPABASE_ANON_KEY_HERE"  # ← REPLACE!

# REQUIRED: OpenAI API key
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY_HERE"  # ← REPLACE!

# ⚠️ CRITICAL for Colab: Set AGORA_PROJECT_ID to bypass RLS errors!
# Get this UUID from your local database or dashboard
# Query: SELECT id FROM projects WHERE name = 'your-project-name';
os.environ["AGORA_PROJECT_ID"] = "YOUR_PROJECT_UUID_HERE"  # ← REPLACE!

print("✅ Environment variables set!\n")

# ============================================================================
# STEP 3: Initialize Agora
# ============================================================================
print("=" * 70)
print("🔧 Initializing Agora telemetry...")
print("=" * 70)

from agora.agora_tracer import init_agora

init_agora(
    app_name="colab-wide-events-test",
    project_name="Colab Wide Events Test",
    enable_cloud_upload=True
)

print("\n")

# ============================================================================
# STEP 4: Set Business Context (Plug-and-Play API!)
# ============================================================================
print("=" * 70)
print("🎯 Setting Business Context (ONE TIME!)...")
print("=" * 70)

from agora.wide_events import set_business_context

set_business_context(
    user_id="user_colab_456",
    user_email="colab-test@example.com",
    subscription_tier="enterprise",
    lifetime_value_cents=284700,  # $2,847 LTV
    account_age_days=730,  # 2 years
    feature_flags={
        "new_checkout_flow": True,
        "ai_recommendations": True,
        "premium_support": True
    },
    workflow_type="testing",
    priority="high",
    custom={
        "test_source": "google_colab",
        "sdk_version": "0.1.0",
        "notebook_name": "wide_events_test"
    }
)

print("✅ Business context set!")
print("   → ALL future LLM calls will be auto-enriched!")
print("\n")

# ============================================================================
# STEP 5: Make LLM Calls (NO WRAPPING NEEDED!)
# ============================================================================
print("=" * 70)
print("📞 Making LLM calls (auto-enriched with business context)...")
print("=" * 70)

from openai import OpenAI
client = OpenAI()

# First call
print("\n1️⃣ First LLM call...")
response1 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say 'Wide events test #1 successful!' in one line."}],
    max_tokens=30
)
print(f"   ✅ Response: {response1.choices[0].message.content}")

# Second call
print("\n2️⃣ Second LLM call...")
response2 = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "Say 'Wide events test #2 successful!' in one line."}],
    max_tokens=30
)
print(f"   ✅ Response: {response2.choices[0].message.content}")

print("\n✅ All LLM calls completed!")
print("\n")

# ============================================================================
# STEP 6: Wait for Upload & Complete Execution
# ============================================================================
print("=" * 70)
print("⏳ Waiting for telemetry to upload to Supabase...")
print("=" * 70)

import time
time.sleep(5)  # Give it time to batch and upload

print("✅ Upload time elapsed!\n")

# Mark execution as complete (FIX: Use asyncio.run, not bare await)
print("📝 Marking execution as complete...")
from agora import agora_tracer
import asyncio

if agora_tracer.cloud_uploader:
    try:
        asyncio.run(agora_tracer.cloud_uploader.complete_execution(
            status="success",
            output_data={
                "message": "Wide events Colab test successful!",
                "num_llm_calls": 2,
                "responses": [
                    response1.choices[0].message.content,
                    response2.choices[0].message.content
                ]
            }
        ))
        print("✅ Execution marked as success!")
    except Exception as e:
        print(f"⚠️  Failed to complete execution: {e}")
else:
    print("⚠️  No cloud uploader available")

print("\n")

# ============================================================================
# STEP 7: Success!
# ============================================================================
print("=" * 70)
print("🎉 TEST COMPLETE!")
print("=" * 70)
print()
print("Now check your Agora dashboard:")
print("  http://localhost:5173/monitoring")
print()
print("Look for:")
print("  ✅ 2 LLM calls (gpt-4o-mini)")
print("  ✅ Business context in each span:")
print("     - user.id = 'user_colab_456'")
print("     - user.subscription_tier = 'enterprise'")
print("     - user.lifetime_value_cents = 284700")
print("     - feature_flags.* (3 flags)")
print("     - custom.test_source = 'google_colab'")
print()
print("=" * 70)
print()
print("💡 Key Points:")
print("  1. Business context was set ONCE")
print("  2. Both LLM calls were auto-enriched")
print("  3. No manual span wrapping needed!")
print("  4. This is the 'wide events' pattern in action!")
print()
print("=" * 70)
