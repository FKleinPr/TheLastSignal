"""LLM parser for The Last Signal game server.

Calls OpenAI-compatible LLM endpoint to interpret natural language input.
Returns structured JSON intent or None if LLM is unavailable/invalid response.

Integration: Called from game_engine/parser.py when LLM_BASE_URL is set and model is reachable.
"""

import os
import json
from typing import Optional, Dict, Any

import httpx

LLM_BASE_URL = os.getenv("LLM_BASE_URL", "")
LLM_MODEL = os.getenv("LLM_MODEL", "stub")
LLM_API_KEY = os.getenv("LLM_API_KEY", "stub")
LLM_TIMEOUT_S = int(os.getenv("LLM_TIMEOUT_S", "5"))


def call_llm(messages: list[dict]) -> Optional[str]:
    """Call the LLM endpoint and return response content.
    
    Returns None if LLM is down, times out, or returns invalid response.
    Messages format: [{"role": "user", "content": "..."}]
    """
    if not LLM_BASE_URL:
        return None
    
    try:
        with httpx.Client(timeout=LLM_TIMEOUT_S) as client:
            response = client.post(
                f"{LLM_BASE_URL}/chat/completions",
                json={
                    "model": LLM_MODEL,
                    "messages": messages,
                    "temperature": 0,
                },
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
            )
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                content = choices[0].get("message", {}).get("content", "")
                return content.strip()
            
            return None
            
    except (httpx.ConnectError, httpx.TimeoutException, json.JSONDecodeError, KeyError):
        return None


def parse_llm_response(content: str) -> Optional[Dict[str, Any]]:
    """Parse LLM response content into structured intent.
    
    Returns dict with verb, object, target or None if invalid JSON.
    LLM must return valid JSON or we ignore it and use rule-based parser.
    """
    if not content:
        return None
    
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "verb" in data:
            return data
        return None
    except json.JSONDecodeError:
        return None


def interpret_natural_language(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Interpret natural language input via LLM.
    
    Returns structured intent dict or None if LLM unavailable/invalid.
    Context includes game state for entity resolution.
    """
    messages = [
        {
            "role": "system",
            "content": "You are a game command parser. Return JSON with 'verb' and optional 'object' and 'target'. Example: {'verb': 'take', 'object': 'core', 'target': null}",
        },
        {
            "role": "user",
            "content": text,
        },
    ]
    
    llm_response = call_llm(messages)
    
    if llm_response:
        return parse_llm_response(llm_response)
    
    return None


def record_request(text: str) -> None:
    """Record LLM request for testing purposes."""
    messages = [
        {
            "role": "user",
            "content": text,
        },
    ]
    try:
        with httpx.Client(timeout=5.0) as client:
            client.post("http://stub-llm:8001/control/record", json={"messages": messages})
    except Exception:
        pass  # Stub might be down, that's okay
