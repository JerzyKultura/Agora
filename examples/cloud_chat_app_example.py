"""
Chat App with Agora Cloud Platform - Automatic Telemetry

All OpenTelemetry spans (including OpenAI calls) captured automatically!
"""

import asyncio
import os
from openai import OpenAI
from agora.agora_tracer import TracedAsyncNode, TracedAsyncFlow, agora_node
from agora.cloud_client import CloudAuditLogger

# ============================================================================
# SETUP
# ============================================================================

API_KEY = "agora_key_hraf8PI8-sKCmD_heUmOaOg00-OYwLNKrwGX4amN6B8"  # Your Agora API key
os.environ["OPENAI_API_KEY"] = "" \
""  # Your OpenAI key

client = OpenAI()

# ============================================================================
# NODES (same as your code!)
# ============================================================================

@agora_node(name="GetUserInput")
async def get_user_input(shared):
    """Get input from user"""
    # Initialize chat on first turn
    if "messages" not in shared:
        shared["messages"] = []
        shared["turn"] = 0
        print("=" * 60)
        print("💬 CHAT READY - Type 'exit' to quit")
        print("=" * 60)
        print()
    
    # Get user input
    user_input = await asyncio.to_thread(input, "👤 You: ")
    user_input = user_input.strip()
    
    # Handle exit
    if user_input.lower() in ["exit", "quit", "bye"]:
        return "exit"
    
    # Store message
    shared["turn"] += 1
    shared["messages"].append({"role": "user", "content": user_input})
    
    return "respond"


@agora_node(name="GenerateResponse")
async def generate_response(shared):
    """Generate AI response - Traceloop auto-instruments OpenAI!"""
    messages = shared["messages"]
    
    # Call OpenAI (automatically traced by Traceloop!)
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7,
        max_tokens=150,
    )
    
    content = response.choices[0].message.content.strip()
    print(f"\n🤖 Bot: {content}\n")
    
    # Store assistant message
    shared["messages"].append({"role": "assistant", "content": content})
    
    return "input"


class ExitNode(TracedAsyncNode):
    """Exit the chat gracefully"""
    async def exec_async(self, prep_res):
        print()
        print("=" * 60)
        print("👋 Thanks for chatting! Goodbye!")
        print("=" * 60)
        return None


# ============================================================================
# MAIN CHAT FLOW with Cloud Platform
# ============================================================================

async def run_chat():
    """Main chat flow with automatic telemetry to Cloud Platform"""
    
    # Create CloudAuditLogger - automatically captures ALL spans! ✨
    logger = CloudAuditLogger(
        api_key=API_KEY,
        workflow_name="ChatApp",
        auto_upload=True  # Auto-upload when done
    )
    
    # Create nodes
    input_node = get_user_input
    response_node = generate_response
    exit_node = ExitNode("ChatExit")
    
    # Build flow
    flow = TracedAsyncFlow("ChatFlow")
    flow.start(input_node)
    
    # Define routing
    input_node - "respond" >> response_node
    input_node - "exit" >> exit_node
    response_node - "input" >> input_node
    
    # Run the flow
    try:
        shared = {}
        await flow.run_async(shared)
        
        # Mark complete and upload (includes ALL spans automatically!)
        # This includes:
        # - Node execution spans (prep/exec/post)
        # - OpenAI API call spans (from Traceloop instrumentation)
        # - Any other traced operations
        logger.mark_complete(status="success")
        
        # Print summary
        print()
        print("=" * 60)
        print("📊 SESSION SUMMARY")
        print("=" * 60)
        print(f"Total turns: {shared.get('turn', 0)}")
        print(f"Total messages: {len(shared.get('messages', []))}")
        print()
        print("🔍 View telemetry at: http://localhost:5173/executions")
        print("   - All node executions")
        print("   - OpenAI API calls with timing")
        print("   - Full trace with parent-child spans")
        print("=" * 60)
        
    except Exception as e:
        logger.mark_complete(status="error", error=str(e))
        raise


# ============================================================================
# RUN IT!
# ============================================================================

if __name__ == "__main__":
    if API_KEY == "agora_key_PASTE_YOUR_KEY_HERE":
        print("\n⚠️  Set your Agora API key first!")
        print("Get it from: http://localhost:5173/api-keys\n")
    elif not os.environ.get("OPENAI_API_KEY") or os.environ["OPENAI_API_KEY"] == "sk-...":
        print("\n⚠️  Set your OpenAI API key first!")
        print("Set OPENAI_API_KEY environment variable\n")
    else:
        asyncio.run(run_chat())