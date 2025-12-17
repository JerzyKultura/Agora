import asyncio
import os

# Try to import from the tracer module
try:
    from agora.agora_tracer import agora_node, TracedAsyncFlow
except ImportError:
    print("❌ Critical Error: 'opentelemetry' or 'traceloop-sdk' not installed.")
    print("   The @agora_node decorator currently requires telemetry dependencies.")
    print("   Run: pip install opentelemetry-api opentelemetry-sdk traceloop-sdk")
    exit(1)

# 1. Define Nodes using Decorators
# Note: The decorator wraps functions into AsyncNodes. 
# They receive 'shared' dict and return the next action (routing).

@agora_node(name="VerifyUser")
async def verify_user(shared):
    """
    Combines prep/exec/post into one function.
    Input: shared state
    Output: routing action string
    """
    user_id = shared.get("user_id")
    print(f"[VerifyUser] Checking user_id: {user_id}")
    
    # Simulate async work
    await asyncio.sleep(0.1)
    
    if user_id > 0:
        return "valid"
    return "invalid"

@agora_node(name="WelcomeUser")
async def welcome_user(shared):
    print("[WelcomeUser] sending welcome email...")
    return "finish"

@agora_node(name="FlagError")
async def flag_error(shared):
    print("[FlagError] logging invalid access attempt...")
    return "finish"

# 2. Build the Flow
# We use TracedAsyncFlow because the nodes are async
flow = TracedAsyncFlow("UserOnboarding")
flow.start(verify_user)

verify_user - "valid" >> welcome_user
verify_user - "invalid" >> flag_error

# 3. Run it
async def main():
    print("--- Running Decorator Scenario 1: Valid User ---")
    shared_state = {"user_id": 123}
    await flow.run_async(shared_state)
    
    print("\n--- Running Decorator Scenario 2: Invalid User ---")
    shared_state = {"user_id": -5}
    await flow.run_async(shared_state)

if __name__ == "__main__":
    asyncio.run(main())
