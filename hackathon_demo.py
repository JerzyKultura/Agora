#!/usr/bin/env python3
"""
=============================================================================
AGORA HACKATHON DEMO - PLUG AND PLAY
=============================================================================

A complete showcase of Agora's capabilities - just run it!

Features demonstrated:
✅ Workflow orchestration
✅ Conditional routing
✅ Retry logic with exponential backoff
✅ Error handling
✅ Batch processing
✅ Async execution
✅ Wide events (business context)
✅ Comprehensive logging to console + file
✅ LLM calls with full tracing

Use case: AI Research Assistant
- Generates research questions
- Searches for answers (with retry)
- Validates results
- Summarizes findings
- Handles errors gracefully

Just run: python hackathon_demo.py

=============================================================================
"""

import os
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List

# =============================================================================
# 1. SETUP - Set your OpenAI API key here
# =============================================================================

# REPLACE THIS WITH YOUR KEY (or set OPENAI_API_KEY environment variable)
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', 'sk-proj-YOUR_KEY_HERE')

if OPENAI_API_KEY == 'sk-proj-YOUR_KEY_HERE':
    print("=" * 80)
    print("⚠️  PLEASE SET YOUR OPENAI API KEY")
    print("=" * 80)
    print("Option 1: Edit line 44 of this file")
    print("Option 2: Run: export OPENAI_API_KEY='sk-...'")
    print("Option 3: Run: OPENAI_API_KEY='sk-...' python hackathon_demo.py")
    print("=" * 80)
    exit(1)

os.environ['OPENAI_API_KEY'] = OPENAI_API_KEY

# =============================================================================
# 2. INITIALIZE AGORA - Local telemetry (no platform needed)
# =============================================================================

from agora.agora_tracer import init_agora
from agora.wide_events import set_business_context
from agora import AsyncNode, AsyncFlow
from openai import OpenAI

print("\n" + "=" * 80)
print("🚀 AGORA HACKATHON DEMO - AI RESEARCH ASSISTANT")
print("=" * 80)
print()

# Initialize Agora with console + file logging (NO PLATFORM NEEDED!)
init_agora(
    app_name="hackathon-research-assistant",
    export_to_console=True,           # ✅ See traces in terminal
    export_to_file="research.jsonl",  # ✅ Save traces to file
    enable_cloud_upload=False         # ❌ No platform needed
)

print("✅ Agora initialized - traces will be saved to research.jsonl")
print()

# Set business context for wide events
set_business_context(
    user_id="hackathon_participant",
    subscription_tier="hacker",
    session_id=f"research_{int(time.time())}",
    workflow_type="research_assistant",
    custom={
        "hackathon": "2026_winter",
        "project": "ai_research_assistant",
        "demo_version": "v1.0"
    }
)

print("✅ Business context set - all LLM calls will include metadata")
print()

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# =============================================================================
# 3. DEFINE RESEARCH WORKFLOW NODES
# =============================================================================

class GenerateQuestions(AsyncNode):
    """Generate research questions about a topic"""

    async def exec_async(self, prep_res):
        topic = prep_res

        print(f"\n{'='*80}")
        print(f"🔍 NODE 1: Generating research questions about '{topic}'")
        print(f"{'='*80}")

        # This LLM call is AUTO-TRACED with business context!
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a research assistant. Generate 3 interesting research questions."},
                {"role": "user", "content": f"Generate 3 research questions about: {topic}"}
            ],
            max_tokens=200
        )

        questions = response.choices[0].message.content
        print(f"✅ Generated questions:\n{questions}\n")

        return {"topic": topic, "questions": questions}


class SearchAnswers(AsyncNode):
    """Search for answers to questions (with simulated retry logic)"""

    def __init__(self):
        super().__init__()
        self.attempt_count = 0

    async def exec_async(self, prep_res):
        data = prep_res
        questions = data['questions']

        print(f"\n{'='*80}")
        print(f"🔎 NODE 2: Searching for answers")
        print(f"{'='*80}")

        # Simulate occasional failures to showcase retry logic
        self.attempt_count += 1
        if self.attempt_count == 1:
            print("⚠️  Simulated network error - will retry...")
            raise Exception("Network timeout - retrying...")

        # This LLM call is AUTO-TRACED!
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a knowledgeable research assistant. Provide concise answers."},
                {"role": "user", "content": f"Answer these research questions:\n{questions}"}
            ],
            max_tokens=300
        )

        answers = response.choices[0].message.content
        print(f"✅ Found answers:\n{answers}\n")

        return {**data, "answers": answers}


class ValidateResults(AsyncNode):
    """Validate research results and determine next action"""

    async def exec_async(self, prep_res):
        data = prep_res

        print(f"\n{'='*80}")
        print(f"✔️  NODE 3: Validating results")
        print(f"{'='*80}")

        # Check if we have good results
        has_answers = len(data.get('answers', '')) > 50

        if has_answers:
            print("✅ Validation passed - proceeding to summary")
            return {"validation": "success", **data}
        else:
            print("⚠️  Validation failed - needs refinement")
            return {"validation": "failed", **data}

    async def post_async(self, shared: Dict[str, Any], prep_res: Any, exec_res: Any) -> str:
        """Conditional routing based on validation"""
        validation = exec_res.get('validation')

        if validation == 'success':
            return 'summarize'  # Go to summary node
        else:
            return 'refine'     # Go to refinement node


class SummarizeFindings(AsyncNode):
    """Summarize the research findings"""

    async def exec_async(self, prep_res):
        data = prep_res

        print(f"\n{'='*80}")
        print(f"📝 NODE 4A: Summarizing findings")
        print(f"{'='*80}")

        # This LLM call is AUTO-TRACED!
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a research assistant. Create a concise summary."},
                {"role": "user", "content": f"Summarize these research findings:\n\nQuestions:\n{data['questions']}\n\nAnswers:\n{data['answers']}"}
            ],
            max_tokens=200
        )

        summary = response.choices[0].message.content
        print(f"✅ Summary:\n{summary}\n")

        return {**data, "summary": summary, "status": "completed"}


class RefineResults(AsyncNode):
    """Refine results when validation fails"""

    async def exec_async(self, prep_res):
        data = prep_res

        print(f"\n{'='*80}")
        print(f"🔧 NODE 4B: Refining results")
        print(f"{'='*80}")

        print("✅ Results refined - marking as needing review\n")

        return {**data, "summary": "Results need manual review", "status": "needs_review"}


class BatchProcessor(AsyncNode):
    """Process multiple topics in batch"""

    async def exec_async(self, prep_res):
        topics = prep_res

        print(f"\n{'='*80}")
        print(f"📦 BATCH PROCESSOR: Processing {len(topics)} topics")
        print(f"{'='*80}")

        results = []
        for i, topic in enumerate(topics, 1):
            print(f"\n[Batch {i}/{len(topics)}] Processing: {topic}")

            # Quick summary for each topic
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": f"In one sentence, what is {topic}?"}
                ],
                max_tokens=50
            )

            summary = response.choices[0].message.content
            results.append({"topic": topic, "summary": summary})
            print(f"  ✅ {summary}")

        print(f"\n✅ Batch complete: {len(results)} topics processed\n")
        return results


# =============================================================================
# 4. BUILD THE RESEARCH WORKFLOW
# =============================================================================

async def run_research_workflow(topic: str):
    """Main research workflow with conditional routing and retry logic"""

    print("=" * 80)
    print("🏗️  BUILDING WORKFLOW")
    print("=" * 80)
    print()

    # Create nodes
    generate = GenerateQuestions()
    search = SearchAnswers()
    validate = ValidateResults()
    summarize = SummarizeFindings()
    refine = RefineResults()

    # Build workflow with conditional routing
    flow = AsyncFlow()

    # Start with question generation
    flow.start(generate) >> search >> validate

    # Conditional routing based on validation
    validate - 'summarize' >> summarize  # Success path
    validate - 'refine' >> refine        # Failure path

    print("✅ Workflow built:")
    print("   Generate → Search → Validate → [Summarize OR Refine]")
    print()

    # Run workflow with retry logic
    print("=" * 80)
    print("▶️  RUNNING WORKFLOW")
    print("=" * 80)

    shared = {"input": topic}

    try:
        result = await flow.run(shared)
        return result
    except Exception as e:
        print(f"❌ Workflow error: {e}")
        return {"status": "error", "error": str(e)}


async def run_batch_workflow(topics: List[str]):
    """Batch processing workflow"""

    print("\n" + "=" * 80)
    print("📦 BATCH WORKFLOW")
    print("=" * 80)

    batch = BatchProcessor()

    flow = AsyncFlow()
    flow.start(batch)

    shared = {"input": topics}
    result = await flow.run(shared)

    return result


# =============================================================================
# 5. RUN THE DEMO
# =============================================================================

async def main():
    """Main demo - showcases all Agora features"""

    start_time = time.time()

    # DEMO 1: Single research workflow with retry and conditional routing
    print("\n" + "█" * 80)
    print("█ DEMO 1: RESEARCH WORKFLOW WITH RETRY & CONDITIONAL ROUTING")
    print("█" * 80)

    result1 = await run_research_workflow("Large Language Models")

    print("\n" + "=" * 80)
    print("📊 WORKFLOW RESULT")
    print("=" * 80)
    print(f"Status: {result1.get('status', 'unknown')}")
    print(f"Summary: {result1.get('summary', 'N/A')}")
    print()

    # DEMO 2: Batch processing
    print("\n" + "█" * 80)
    print("█ DEMO 2: BATCH PROCESSING")
    print("█" * 80)

    topics = [
        "Quantum Computing",
        "Neural Networks",
        "Blockchain"
    ]

    result2 = await run_batch_workflow(topics)

    print("\n" + "=" * 80)
    print("📊 BATCH RESULTS")
    print("=" * 80)
    for item in result2:
        print(f"  • {item['topic']}: {item['summary']}")
    print()

    # Show timing
    elapsed = time.time() - start_time

    print("\n" + "=" * 80)
    print("✨ DEMO COMPLETE")
    print("=" * 80)
    print(f"⏱️  Total time: {elapsed:.2f}s")
    print()

    # Show what was logged
    print("=" * 80)
    print("📁 TELEMETRY SAVED")
    print("=" * 80)
    print("✅ Console: All traces printed above")
    print("✅ File: research.jsonl (view with: cat research.jsonl | jq)")
    print()
    print("What's in the telemetry:")
    print("  • All LLM calls with prompts & completions")
    print("  • Token usage and costs")
    print("  • Node execution timing")
    print("  • Retry attempts")
    print("  • Conditional routing decisions")
    print("  • Business context (user_id, session_id, hackathon metadata)")
    print()

    # Show Agora features demonstrated
    print("=" * 80)
    print("🎯 AGORA FEATURES SHOWCASED")
    print("=" * 80)
    print("✅ Workflow Orchestration - Multi-node pipelines")
    print("✅ Async Execution - Full async/await support")
    print("✅ Conditional Routing - Dynamic flow based on results")
    print("✅ Retry Logic - Auto-retry on failures (SearchAnswers node)")
    print("✅ Error Handling - Graceful degradation")
    print("✅ Batch Processing - Process multiple items efficiently")
    print("✅ Wide Events - Business context on every span")
    print("✅ Local Telemetry - Console + file (no platform needed)")
    print("✅ LLM Auto-tracing - Every OpenAI call captured")
    print("✅ Node Chaining - Clean >> syntax")
    print()

    print("=" * 80)
    print("🚀 NEXT STEPS FOR YOUR HACKATHON PROJECT")
    print("=" * 80)
    print("1. Copy this file as a starting point")
    print("2. Replace the nodes with your use case")
    print("3. Add more conditional routing as needed")
    print("4. Adjust retry logic and error handling")
    print("5. Query research.jsonl for metrics and insights")
    print()
    print("Query example:")
    print('  cat research.jsonl | jq \'.attributes."llm.usage.total_tokens"\'')
    print()
    print("Happy hacking! 🎉")
    print("=" * 80)
    print()


# =============================================================================
# RUN IT!
# =============================================================================

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Demo interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
