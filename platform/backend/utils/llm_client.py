"""
LLM Client for Context Summarization

Supports BYOK (Bring Your Own Key) for Gemini and OpenAI.
Falls back to rule-based summary if no API key available.
"""

import os
from typing import Optional, Dict, Any, List
import json


async def generate_context_summary(
    failures: List[Dict[str, Any]],
    codebase: List[Dict[str, Any]],
    active_state: Optional[Dict[str, Any]],
    project_name: str,
    org_llm_key: Optional[str] = None,
    org_llm_provider: Optional[str] = None
) -> tuple[str, str]:
    """
    Generate intelligent context summary using LLM.
    
    Args:
        failures: Recent error spans
        codebase: Recently updated code nodes
        active_state: Latest execution state
        project_name: Name of the project
        org_llm_key: Organization's LLM API key (BYOK)
        org_llm_provider: "gemini" or "openai"
        
    Returns:
        Tuple of (summary_text, provider_used)
    """
    # Build prompt
    prompt = _build_prompt(failures, codebase, active_state, project_name)
    
    # Try organization's key first (BYOK)
    if org_llm_key and org_llm_provider:
        if org_llm_provider == "gemini":
            summary = await _gemini_summary(prompt, org_llm_key)
            if summary:
                return summary, "gemini"
        elif org_llm_provider == "openai":
            summary = await _openai_summary(prompt, org_llm_key)
            if summary:
                return summary, "openai"
    
    # Fallback to system keys
    if os.getenv("GEMINI_API_KEY"):
        summary = await _gemini_summary(prompt, os.getenv("GEMINI_API_KEY"))
        if summary:
            return summary, "gemini"
    
    if os.getenv("OPENAI_API_KEY"):
        summary = await _openai_summary(prompt, os.getenv("OPENAI_API_KEY"))
        if summary:
            return summary, "openai"
    
    # Final fallback: rule-based summary
    return _fallback_summary(failures, codebase, active_state, project_name), "fallback"


def _build_prompt(
    failures: List[Dict[str, Any]],
    codebase: List[Dict[str, Any]],
    active_state: Optional[Dict[str, Any]],
    project_name: str
) -> str:
    """Build LLM prompt from intelligence data."""
    
    prompt = f"""You are an AI assistant analyzing project context for developer productivity.

Given the following data about a software project, generate a concise, machine-readable summary (max 2-3 sentences) that highlights:
1. Project status (active development, debugging, stable)
2. Most critical issue or focus area
3. Recommended next action

Project Name: {project_name}

Recent Failures ({len(failures)} errors):
"""
    
    if failures:
        for f in failures[:3]:  # Top 3
            prompt += f"- {f.get('name', 'unknown')}: {f.get('error_message', 'no message')}\n"
    else:
        prompt += "- No recent failures\n"
    
    prompt += f"\nRecent Code Changes ({len(codebase)} updates):\n"
    if codebase:
        for c in codebase[:5]:  # Top 5
            prompt += f"- {c.get('file_path', 'unknown')}: {c.get('name', 'unknown')} ({c.get('node_type', 'unknown')})\n"
    else:
        prompt += "- No recent changes tracked\n"
    
    prompt += "\nActive Execution:\n"
    if active_state and active_state.get('execution_id'):
        prompt += f"- Workflow: {active_state.get('workflow_name', 'unknown')}\n"
        prompt += f"- Status: {active_state.get('status', 'unknown')}\n"
    else:
        prompt += "- No active execution\n"
    
    prompt += '\n\nFormat: "Project: {name}. Status: {status}. {critical_insight}. Recommended focus: {action}."\n\nGenerate summary:'
    
    return prompt


async def _gemini_summary(prompt: str, api_key: str) -> Optional[str]:
    """Generate summary using Google Gemini (async)."""
    try:
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Use async API to avoid blocking FastAPI event loop
        response = await model.generate_content_async(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        return None


async def _openai_summary(prompt: str, api_key: str) -> Optional[str]:
    """Generate summary using OpenAI."""
    try:
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=api_key)
        
        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a concise technical analyst."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        return response.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return None


def _fallback_summary(
    failures: List[Dict[str, Any]],
    codebase: List[Dict[str, Any]],
    active_state: Optional[Dict[str, Any]],
    project_name: str
) -> str:
    """Rule-based summary when no LLM available."""
    
    # Determine status
    if failures:
        status = "Debugging"
        critical = f"Last failure: {failures[0].get('name', 'unknown')}"
        if failures[0].get('error_message'):
            critical += f" ({failures[0]['error_message'][:50]}...)"
        action = f"Investigate {failures[0].get('name', 'error')}"
    elif codebase:
        status = "Active development"
        critical = f"Recent changes in {codebase[0].get('file_path', 'unknown')}"
        action = f"Review {codebase[0].get('name', 'recent changes')}"
    elif active_state and active_state.get('status') == 'running':
        status = "Execution in progress"
        critical = f"Workflow '{active_state.get('workflow_name', 'unknown')}' running"
        action = "Monitor execution"
    else:
        status = "Stable"
        critical = "No recent activity"
        action = "Ready for new development"
    
    return f"Project: {project_name}. Status: {status}. {critical}. Recommended focus: {action}."
