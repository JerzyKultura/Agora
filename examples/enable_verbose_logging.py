"""
Example: Enable Comprehensive Verbose Logging in Agora

This script demonstrates how to enable detailed, step-by-step logging throughout
the Agora SDK to make debugging and analysis trivial.

The logging captures:
- Every node execution (prep, exec, post phases)
- Flow orchestration and routing decisions
- Retry attempts with exponential backoff
- Batch operations and sizes
- Span hierarchy and OpenTelemetry traces
- Network operations and Supabase uploads
- Error conditions with full context

Run this script to see exhaustive logging in action!
"""

import asyncio
from agora import AsyncNode, AsyncFlow
from agora.logging_config import enable_verbose_logging


# ======================================================================
# STEP 1: Enable Comprehensive Logging
# ======================================================================

# This single line enables DEBUG-level logging across ALL Agora modules
# Every execution path, decision point, retry, and error will emit logs
enable_verbose_logging(level="DEBUG")

# Alternative configurations:
# enable_verbose_logging(level="INFO")  # Less verbose, only major events
# enable_file_logging("agora_debug.log")  # Log to file with rotation
# setup_structured_logging()  # JSON logs for log aggregation systems

print("=" * 80)
print("COMPREHENSIVE LOGGING ENABLED")
print("=" * 80)
print()
print("Watch the logs below to see EVERY step of execution:")
print("  - Node creation and initialization")
print("  - Successor registration (routing setup)")
print("  - Flow orchestration steps")
print("  - Phase execution (prep → exec → post)")
print("  - Retry attempts and backoff delays")
print("  - Shared state changes")
print("  - Span creation and hierarchy")
print()
print("=" * 80)
print()


# ======================================================================
# STEP 2: Define a Simple Workflow
# ======================================================================

class StartNode(AsyncNode):
    """Simple start node that sets initial state."""
    async def exec_async(self, prep_result):
        print("  [USER CODE] StartNode executing...")
        self.context["counter"] = 0
        return "process"


class ProcessNode(AsyncNode):
    """Process node that increments counter."""
    async def exec_async(self, prep_result):
        print("  [USER CODE] ProcessNode executing...")
        self.context["counter"] += 1
        await asyncio.sleep(0.1)  # Simulate work
        return "finish"


class FinishNode(AsyncNode):
    """Finish node that prints result."""
    async def exec_async(self, prep_result):
        print("  [USER CODE] FinishNode executing...")
        print(f"  [USER CODE] Final counter value: {self.context['counter']}")
        return "done"


# ======================================================================
# STEP 3: Build and Run the Flow
# ======================================================================

async def main():
    """Run the example workflow with comprehensive logging."""

    print("\n📋 Creating workflow nodes...")
    start = StartNode(name="Start")
    process = ProcessNode(name="Process")
    finish = FinishNode(name="Finish")

    print("\n📋 Connecting nodes (setting up routing)...")
    start >> process  # Default routing
    process - "finish" >> finish  # Conditional routing

    print("\n📋 Creating flow...")
    flow = AsyncFlow(name="ExampleFlow", start=start)

    print("\n📋 Running flow with comprehensive logging...\n")
    print("=" * 80)
    print("EXECUTION LOGS (every decision, every step)")
    print("=" * 80)
    print()

    # Run the flow - every step will be logged
    shared = {}
    result = await flow.run_async(shared)

    print()
    print("=" * 80)
    print("EXECUTION COMPLETE")
    print("=" * 80)
    print(f"\nFinal result: {result}")
    print(f"Shared state: {shared}")

    print("\n" + "=" * 80)
    print("WHAT DID WE LOG?")
    print("=" * 80)
    print("""
The logs above showed you:

✓ Node creation with configuration details
✓ Successor registration and routing setup
✓ Flow orchestration start and initialization
✓ Each orchestration step with node names
✓ Shared state keys at each step
✓ Phase execution (prep, exec, post) for each node
✓ Routing decisions (which action led to which node)
✓ Flow completion with result

For debugging, you can:
1. Search logs for specific node names
2. Trace execution flow by following orchestration steps
3. Check shared state evolution at each step
4. Identify where errors occurred and what led to them
5. Verify retry logic when failures happen

This level of observability makes debugging trivial!
    """)


if __name__ == "__main__":
    asyncio.run(main())
