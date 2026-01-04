"""
Google Colab Test: Wide Events Business Context

Copy and paste this entire file into a Google Colab cell and run it!
"""

# ============================================================================
# STEP 1: Install Dependencies
# ============================================================================
print("📦 Installing dependencies...")
import subprocess
import sys

subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                      "openai", "traceloop-sdk", "supabase", "opentelemetry-api",
                      "opentelemetry-sdk"])

print("✅ Dependencies installed!")
print()

# ============================================================================
# STEP 2: Set Environment Variables (Paste Your Keys Here)
# ============================================================================
import os

# PASTE YOUR KEYS HERE (replace the placeholder values):
os.environ["VITE_SUPABASE_URL"] = "YOUR_SUPABASE_URL_HERE"
os.environ["VITE_SUPABASE_ANON_KEY"] = "YOUR_SUPABASE_ANON_KEY_HERE"
os.environ["AGORA_API_KEY"] = "YOUR_AGORA_API_KEY_HERE"
os.environ["AGORA_PROJECT_ID"] = "YOUR_AGORA_PROJECT_ID_HERE"
os.environ["OPENAI_API_KEY"] = "YOUR_OPENAI_API_KEY_HERE"
os.environ["TRACELOOP_API_KEY"] = "YOUR_TRACELOOP_API_KEY_HERE"

print("✅ Environment variables set!")
print()

# ============================================================================
# STEP 3: Clone and Install Agora SDK
# ============================================================================
print("📥 Cloning Agora repository...")
subprocess.check_call(["git", "clone", "-q", "https://github.com/JerzyKultura/Agora.git"])
subprocess.check_call([sys.executable, "-m", "pip", "install", "-q", "-e", "Agora"])
print("✅ Agora SDK installed!")
print()

# ============================================================================
# STEP 4: Import and Initialize
# ============================================================================
print("=" * 70)
print("🔍 Testing Wide Events Business Context")
print("=" * 70)
print()

# Initialize telemetry
print("2️⃣ Initializing Telemetry...")
from agora.agora_tracer import init_agora

init_agora(
    app_name="wide-events-colab-test",
    project_name="Wide Events Colab Test",
    enable_cloud_upload=True
)
print("✅ Telemetry initialized")
print()

# Import wide events module
print("3️⃣ Importing Wide Events Module...")
from agora.wide_events import BusinessContext, enrich_current_span
print("✅ Wide events module imported")
print()

# ============================================================================
# STEP 5: Create Business Context and Make LLM Call
# ============================================================================
print("4️⃣ Making Test LLM Call with Business Context...")
print()

from openai import OpenAI
client = OpenAI()

# Create rich business context
context = BusinessContext(
    user_id="colab_user_123",
    user_email="test@colab.example.com",
    subscription_tier="enterprise",
    lifetime_value_cents=250000,  # $2,500 LTV
    account_age_days=365,
    session_id="colab_session_xyz",
    conversation_turn=1,
    feature_flags={
        "new_ui": True,
        "advanced_features": True,
        "beta_access": True,
        "colab_integration": True
    },
    workflow_type="testing",
    priority="critical",
    custom={
        "test_run": True,
        "test_timestamp": "2026-01-04",
        "platform": "google_colab",
        "notebook_name": "wide_events_test"
    }
)

print("📊 Business Context Created:")
print(f"   - User ID: {context.user_id}")
print(f"   - Subscription: {context.subscription_tier}")
print(f"   - LTV: ${context.lifetime_value_cents / 100}")
print(f"   - Account Age: {context.account_age_days} days")
print(f"   - Feature Flags: {len(context.feature_flags)} flags")
print(f"   - Custom Attrs: {len(context.custom)} attributes")
print()

# Enrich the current span with business context
enrich_current_span(context)
print("✅ Span enriched with business context")
print()

# Make the LLM call
print("📞 Calling OpenAI...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "system", "content": "You are a helpful assistant testing the wide events pattern."},
        {"role": "user", "content": "Explain what 'wide events' means for LLM observability in one sentence."}
    ],
    max_tokens=100
)

print("✅ LLM call complete!")
print()
print(f"🤖 Response: {response.choices[0].message.content}")
print()

# ============================================================================
# STEP 6: Wait for Upload and Complete Execution
# ============================================================================
print("⏳ Waiting for telemetry to upload to Supabase...")
import time
time.sleep(3)
print("✅ Upload complete!")
print()

# Mark execution as complete
print("📝 Marking execution as complete...")
from agora import agora_tracer
import asyncio

if agora_tracer.cloud_uploader:
    asyncio.run(agora_tracer.cloud_uploader.complete_execution(
        status="success",
        output_data={"message": "Wide events test from Colab successful!", "response": response.choices[0].message.content}
    ))
    print("✅ Execution marked as success!")
print()

# ============================================================================
# STEP 7: View Results
# ============================================================================
print("=" * 70)
print()
print("🎉 SUCCESS! Now Check Your Dashboard!")
print()
print("1. Open: http://localhost:5173/monitoring")
print("   (Or wherever your Agora dashboard is running)")
print()
print("2. Click 'Traces' tab")
print()
print("3. Find the newest trace (should be at the top)")
print("   Look for: 'wide-events-colab-test' or 'openai.chat'")
print()
print("4. Click on the trace, then click on the 'openai.chat' span")
print()
print("5. Click the 'Details' tab")
print()
print("6. Look for the green section:")
print("   🎯 Business Context (Wide Events)")
print()
print("📋 You should see these attributes:")
print("   ✓ user.id = 'colab_user_123'")
print("   ✓ user.subscription_tier = 'enterprise'")
print("   ✓ user.lifetime_value_cents = 250000")
print("   ✓ user.account_age_days = 365")
print("   ✓ feature_flags.new_ui = True")
print("   ✓ feature_flags.advanced_features = True")
print("   ✓ feature_flags.beta_access = True")
print("   ✓ feature_flags.colab_integration = True")
print("   ✓ app.workflow_type = 'testing'")
print("   ✓ app.priority = 'critical'")
print("   ✓ custom.test_run = True")
print("   ✓ custom.platform = 'google_colab'")
print("   ✓ custom.notebook_name = 'wide_events_test'")
print()
print("=" * 70)
print()
print("💡 What Just Happened?")
print()
print("The 'wide events' pattern means:")
print("Instead of logging scattered events like:")
print("  - 'User logged in'")
print("  - 'User clicked button'")
print("  - 'LLM API call made'")
print()
print("We attach ALL business context to EVERY telemetry span:")
print("  - User tier, LTV, account age")
print("  - Feature flags")
print("  - Session info")
print("  - Custom attributes")
print()
print("This gives you ONE comprehensive view of:")
print("  ✓ WHO made the request (user.id, user.email)")
print("  ✓ WHAT they're worth (user.lifetime_value_cents)")
print("  ✓ WHAT features they have access to (feature_flags.*)")
print("  ✓ WHAT context they're in (session.id, app.workflow_type)")
print()
print("All in ONE place, attached to EVERY span!")
print()
print("=" * 70)
