"""
OpenAI Integration Example
===========================
Shows how to use OpenAI with Agora for automatic token tracking.

Setup:
1. pip install openai
2. export OPENAI_API_KEY=your-key-here
3. Run: PYTHONPATH=. python3 examples/openai_example.py
"""

import asyncio
import os
from agora import AsyncNode, AsyncFlow, init_agora

# Check if OpenAI is available
try:
    from openai import AsyncOpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("⚠️  OpenAI not installed. Install with: pip install openai")

init_agora(app_name="OpenAI Example")


class GenerateStoryNode(AsyncNode):
    """Generates a short story using GPT"""
    
    def __init__(self):
        super().__init__("generate_story", max_retries=2, wait=1)
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = AsyncOpenAI()
        else:
            self.client = None
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        topic = prep_res.get("topic", "AI")
        
        if not self.client:
            print("⚠️  OpenAI not configured, using mock response")
            return {
                "story": f"Once upon a time, {topic} changed the world...",
                "tokens": 0,
                "model": "mock"
            }
        
        print(f"🤖 Generating story about: {topic}")
        
        try:
            # Call OpenAI API
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a creative storyteller."},
                    {"role": "user", "content": f"Write a 2-sentence story about {topic}."}
                ],
                max_tokens=100,
                temperature=0.7
            )
            
            story = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            print(f"   ✅ Generated story ({tokens} tokens)")
            
            return {
                "story": story,
                "tokens": tokens,
                "model": "gpt-4o-mini"
            }
            
        except Exception as e:
            print(f"   ❌ API error: {e}")
            raise
    
    async def post_async(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"
    
    async def exec_fallback_async(self, prep_res, exc):
        print("   ⚠️  Using fallback story")
        return {
            "story": "An error occurred, but the system gracefully recovered.",
            "tokens": 0,
            "model": "fallback",
            "error": str(exc)
        }


class SummarizeNode(AsyncNode):
    """Summarizes the story to a tweet"""
    
    def __init__(self):
        super().__init__("summarize", max_retries=2)
        if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
            self.client = AsyncOpenAI()
        else:
            self.client = None
    
    async def prep_async(self, shared):
        return shared
    
    async def exec_async(self, prep_res):
        story = prep_res.get("story", "")
        
        if not self.client:
            print("⚠️  Using mock summary")
            return {
                "summary": story[:100] + "...",
                "tokens": 0
            }
        
        print(f"📝 Creating tweet summary...")
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "user", "content": f"Summarize this in one tweet (max 280 chars):\n\n{story}"}
                ],
                max_tokens=60,
                temperature=0.5
            )
            
            summary = response.choices[0].message.content
            tokens = response.usage.total_tokens if response.usage else 0
            
            print(f"   ✅ Created summary ({tokens} tokens)")
            
            return {
                "summary": summary,
                "tokens": tokens
            }
            
        except Exception as e:
            print(f"   ❌ Summary failed: {e}")
            # Just return the original story truncated
            return {
                "summary": story[:280],
                "tokens": 0,
                "error": str(e)
            }
    
    async def post_async(self, shared, prep_res, exec_res):
        shared.update(exec_res)
        return "default"  # Return action string, not dict!


async def main():
    print("="*60)
    print("🤖 OpenAI Integration Example")
    print("="*60)
    
    if not OPENAI_AVAILABLE:
        print("\n💡 Install OpenAI: pip install openai")
        print("💡 Set API key: export OPENAI_API_KEY=sk-...\n")
    
    # Create nodes
    generate = GenerateStoryNode()
    summarize = SummarizeNode()
    
    # Chain them
    generate.successors = {"default": summarize}
    
    # Create flow
    flow = AsyncFlow("Story Generator", start=generate)
    
    # Test with different topics
    topics = ["robots", "space exploration", "quantum computing"]
    
    for topic in topics:
        print(f"\n📌 Topic: {topic}")
        print("-" * 60)
        
        shared = {"topic": topic}
        result = await flow.run_async(shared)
        
        print()
        print(f"📖 Story:")
        print(f"   {shared.get('story', 'N/A')}")
        print()
        print(f"🐦 Tweet:")
        print(f"   {shared.get('summary', 'N/A')}")
        print()
        print(f"📊 Total tokens: {shared.get('tokens', 0)}")
        print()
    
    print("="*60)
    print("✅ All stories generated!")
    print("="*60)
    print()
    print("📊 Check dashboard: http://localhost:5173/monitoring")
    print("   You'll see token usage and costs!")

if __name__ == "__main__":
    asyncio.run(main())
