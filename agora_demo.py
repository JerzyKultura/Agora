"""
🚀 AGORA - Complete Demo
Shows: Workflows, LLM tracking, conditional routing, and programmatic queries
"""
from agora import init_agora, AsyncFlow, AsyncNode
from agora.wide_events import set_business_context
from openai import OpenAI
import os
import asyncio
import json

# ============================================================================
# WORKFLOW: AI Content Generator with Quality Check
# ============================================================================

class GenerateContent(AsyncNode):
    """Generate blog content using AI"""
    async def exec_async(self, prep_res):
        topic = prep_res or "AI in healthcare"
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Write a 100-word blog post about: {topic}"
            }]
        )
        return response.choices[0].message.content
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['content'] = exec_res
        return "default"


class QualityCheck(AsyncNode):
    """Check content quality and route accordingly"""
    async def prep_async(self, shared):
        return shared.get('content')
    
    async def exec_async(self, prep_res):
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{
                "role": "user",
                "content": f"Rate this content quality 1-10:\n{prep_res}\n\nJust give the number."
            }]
        )
        
        score = int(''.join(filter(str.isdigit, response.choices[0].message.content)) or 0)
        return {"score": score, "content": prep_res}
    
    async def post_async(self, shared, prep_res, exec_res):
        shared['quality_score'] = exec_res['score']
        # Conditional routing based on quality
        if exec_res['score'] >= 7:
            return "approve"
        else:
            return "reject"


class ApproveContent(AsyncNode):
    """Publish approved content"""
    async def exec_async(self, prep_res):
        return "✅ Content approved and published!"


class RejectContent(AsyncNode):
    """Handle rejected content"""
    async def exec_async(self, prep_res):
        return "❌ Content rejected - needs improvement"


# ============================================================================
# DEMO RUNNER
# ============================================================================

async def run_demo():
    print("\n" + "="*80)
    print("🚀 AGORA DEMO - AI Content Workflow")
    print("="*80 + "\n")
    
    # 1. Initialize Agora
    print("📦 Step 1: Initialize Agora SDK")
    init_agora(
        app_name="content-generator",
        export_to_file="telemetry.jsonl",
        enable_cloud_upload=False
    )
    print()
    
    # 2. Set business context (tracks user, session, etc.)
    print("👤 Step 2: Set business context")
    set_business_context(
        user_id="demo_user_123",
        custom={
            "workflow_name": "content_generation",
            "team": "marketing",
            "experiment": "agora_demo"
        }
    )
    print("   ✅ Context set: user=demo_user_123, workflow=content_generation")
    print()
    
    # 3. Build workflow with conditional routing
    print("🔧 Step 3: Build workflow")
    generate = GenerateContent()
    quality_check = QualityCheck()
    approve = ApproveContent()
    reject = RejectContent()
    
    flow = AsyncFlow()
    flow.start(generate) >> quality_check
    quality_check - "approve" >> approve
    quality_check - "reject" >> reject
    
    print("   ✅ Workflow built:")
    print("      Generate → QualityCheck → [Approve OR Reject]")
    print()
    
    # 4. Run workflow
    print("▶️  Step 4: Running workflow...")
    result = await flow.run_async("AI in healthcare")
    
    print(f"\n   📄 Generated content: {result.get('content', 'N/A')[:100]}...")
    print(f"   📊 Quality score: {result.get('quality_score', 'N/A')}/10")
    print()
    
    # 5. Query telemetry programmatically
    print("="*80)
    print("📊 Step 5: Query Telemetry (SDK Style)")
    print("="*80 + "\n")
    
    # Load telemetry
    spans = []
    with open("telemetry.jsonl", 'r') as f:
        for line in f:
            if line.strip():
                spans.append(json.loads(line))
    
    print(f"✅ Loaded {len(spans)} telemetry spans\n")
    
    # AI Metrics
    print("🤖 AI METRICS:")
    total_tokens = 0
    total_calls = 0
    for span in spans:
        attrs = span.get('attributes', {})
        tokens = attrs.get('llm.usage.total_tokens', 0)
        model = attrs.get('gen_ai.request.model')
        
        if tokens > 0:
            total_calls += 1
            total_tokens += tokens
            print(f"   • LLM Call: {model}, Tokens: {tokens}")
    
    print(f"\n   Total LLM calls: {total_calls}")
    print(f"   Total tokens: {total_tokens:,}")
    print(f"   Estimated cost: ${total_tokens * 0.00002:.4f}")
    print()
    
    # User tracking
    print("👤 USER TRACKING:")
    user_spans = [s for s in spans if s.get('attributes', {}).get('user.id') == 'demo_user_123']
    print(f"   User 'demo_user_123' had {len(user_spans)} tracked operations")
    
    workflow_name = user_spans[0].get('attributes', {}).get('custom.workflow_name') if user_spans else None
    print(f"   Workflow: {workflow_name}")
    print()
    
    print("="*80)
    print("✅ DEMO COMPLETE!")
    print("="*80)
    print("\nWhat just happened:")
    print("  ✅ Initialized Agora SDK (1 line of code)")
    print("  ✅ Tracked user context automatically")
    print("  ✅ Built multi-step workflow with conditional routing")
    print("  ✅ Auto-tracked all LLM calls (no manual instrumentation)")
    print("  ✅ Queried telemetry programmatically")
    print("  ✅ Everything stored locally in telemetry.jsonl")
    print("\nView raw telemetry:")
    print("  cat telemetry.jsonl | jq")


if __name__ == "__main__":
    asyncio.run(run_demo())
