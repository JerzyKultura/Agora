"""
LLM Integration Example
=======================
Demonstrates how to integrate LLMs with Agora workflows.

This example shows:
- OpenAI integration with automatic tracing
- Token usage tracking
- Error handling for API calls
- Chaining LLM calls
"""

import asyncio
import os
from agora.agora_tracer import init_agora, TracedAsyncNode, TracedAsyncFlow

# Check if OpenAI is available
try:
    from openai import OpenAI
    from agora.instrument_openai import trace_openai_call
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not installed. Install with: pip install openai")

# Initialize Agora
init_agora(
    project_name="LLM Workflow Example",
    silent_mode=False
)


class GeneratePromptNode(TracedAsyncNode):
    """Generates a prompt based on user input"""
    
    def __init__(self):
        super().__init__("Generate Prompt")
    
    async def exec_async(self, prep_res):
        topic = prep_res.get("topic", "AI")
        prompt = f"Write a short, engaging tweet about {topic}. Keep it under 280 characters."
        print(f"📝 Generated prompt for topic: {topic}")
        return {"prompt": prompt, "topic": topic}


class CallLLMNode(TracedAsyncNode):
    """Calls OpenAI API with automatic tracing"""
    
    def __init__(self):
        super().__init__("Call LLM", max_retries=2, wait=1)
        if OPENAI_AVAILABLE:
            self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        else:
            self.client = None
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        if not OPENAI_AVAILABLE or not self.client:
            print("⚠️  OpenAI not configured, using mock response")
            return {
                "response": "AI is transforming how we build software! 🚀 #AI #Tech",
                "tokens": 15,
                "model": "mock"
            }
        
        prompt = prep_res.get("prompt", "")
        print(f"🤖 Calling OpenAI API...")
        
        try:
            # This call is automatically traced with token usage!
            response = trace_openai_call(
                self.client,
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            content = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            print(f"   ✅ Response received ({tokens} tokens)")
            
            return {
                "response": content,
                "tokens": tokens,
                "model": "gpt-4o-mini"
            }
        except Exception as e:
            print(f"   ❌ API call failed: {e}")
            raise
    
    async def exec_fallback_async(self, prep_res, exc):
        # Fallback to a default response if API fails
        print("   ⚠️  Using fallback response")
        return {
            "response": "AI is amazing! Check out the latest developments.",
            "tokens": 0,
            "model": "fallback",
            "error": str(exc)
        }


class RefineResponseNode(TracedAsyncNode):
    """Optionally refines the LLM response"""
    
    def __init__(self):
        super().__init__("Refine Response")
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        response = prep_res.get("response", "")
        tokens = prep_res.get("tokens", 0)
        
        # Simple refinement: add hashtags if missing
        if "#" not in response:
            response += " #AI #Innovation"
        
        print(f"✨ Refined response ({len(response)} chars)")
        
        return {
            "final_response": response,
            "total_tokens": tokens,
            "char_count": len(response)
        }


class LLMWorkflow(TracedAsyncFlow):
    """Workflow that generates content using LLM"""
    
    def __init__(self):
        # Create nodes
        self.generate_prompt = GeneratePromptNode()
        self.call_llm = CallLLMNode()
        self.refine = RefineResponseNode()
        
        # Set up routing
        self.generate_prompt.successors = {"default": self.call_llm}
        self.call_llm.successors = {"default": self.refine}
        
        # Initialize flow
        super().__init__("LLM Content Generation", start=self.generate_prompt)


async def main():
    print("="*60)
    print("🤖 LLM Integration Example")
    print("="*60)
    print()
    
    # Test with different topics
    topics = ["Python programming", "Machine Learning", "Cloud Computing"]
    
    for topic in topics:
        print(f"\n📌 Topic: {topic}")
        print("-" * 60)
        
        workflow = LLMWorkflow()
        result = await workflow.run_async({"topic": topic})
        
        print()
        print(f"📝 Final Tweet:")
        print(f"   {result.get('final_response', 'N/A')}")
        print(f"   Tokens used: {result.get('total_tokens', 0)}")
        print()
    
    print("="*60)
    print("✅ All workflows completed!")
    print("="*60)
    print()
    print("📊 Check your dashboard at: http://localhost:5173/monitoring")
    print("   You'll see token usage, latency, and costs!")


if __name__ == "__main__":
    if not OPENAI_AVAILABLE:
        print("\n💡 Tip: Install OpenAI to see real API calls:")
        print("   pip install openai")
        print("   export OPENAI_API_KEY=your-key\n")
    
    asyncio.run(main())
