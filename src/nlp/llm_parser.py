"""LLM parser for The Last Signal game server.

Calls OpenAI-compatible LLM endpoint to interpret natural language input.
Returns structured JSON intent or None if LLM is unavailable/invalid response.

Integration: Called from game_engine/parser.py when LLM_BASE_URL is set and model is reachable.

CR-002 updates:
- Build system message with verb list and entity names/ids (design 6.8)
- Strip Markdown code fence from LLM response before parsing JSON
- Stub records real request on /v1/chat/completions (no record_request() needed)
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
                    "temperature": 0.0,
                    "max_tokens": 200,
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
    
    Strips Markdown code fence if present before parsing JSON.
    Returns dict with verb, object, target or None if invalid JSON.
    LLM must return valid JSON or we ignore it and use rule-based parser.
    """
    if not content:
        return None
    
    # Strip Markdown code fence if present (```json ... ```)
    content = content.strip()
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3].strip()
    
    try:
        data = json.loads(content)
        if isinstance(data, dict) and "verb" in data:
            return data
        return None
    except json.JSONDecodeError:
        return None


def interpret_natural_language(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
    """Interpret natural language input via LLM.
    
    Builds system message with verb list and entity names/ids (design 6.8).
    Returns structured intent dict or None if LLM unavailable/invalid.
    Context includes game state for entity resolution.
    """
    if not context:
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
    else:
        # Build system message with verb list and entity names/ids (design 6.8)
        content = context.get("content", {})
        locations = content.get("locations", {})
        objects = content.get("objects", {})
        characters = content.get("characters", {})
        
        # Get valid verbs
        valid_verbs = ["look", "go", "take", "drop", "give", "show", "use", "talk", "ask", "pick-lock", "pick lock", "wait", "save", "load", "continue", "restart"]
        
        # Get entity names and IDs for things present at current location
        current_location = context.get("game_state", {}).get("player_location", "")
        inventory = context.get("game_state", {}).get("inventory", [])
        
        # Get characters in current location
        location_data = locations.get(current_location, {})
        characters_here = location_data.get("characters", [])
        objects_in_location = location_data.get("objects", [])
        
        # Build context lines for present entities
        context_lines = []
        
        # Add verbs
        context_lines.append("Verbs: " + ", ".join(valid_verbs))
        
        # Add objects in location
        for obj_id in objects_in_location:
            if obj_id in objects:
                obj_names = objects[obj_id].get("names", [obj_id])
                context_lines.append(f"Object {obj_id}: {', '.join(obj_names)}")
        
        # Add objects in inventory
        for obj_id in inventory:
            if obj_id in objects:
                obj_names = objects[obj_id].get("names", [obj_id])
                context_lines.append(f"Inventory {obj_id}: {', '.join(obj_names)}")
        
        # Add characters in current location
        for char_id in characters_here:
            if char_id in characters:
                char_names = characters[char_id].get("names", [char_id])
                context_lines.append(f"Character {char_id}: {', '.join(char_names)}")
        
        system_content = "You are a game command parser.\n\n"
        system_content += "Return JSON with 'verb' and optional 'object' and 'target'.\n"
        system_content += "Example: {'verb': 'take', 'object': 'core', 'target': null}\n\n"
        system_content += "Available information:\n" + "\n".join(context_lines)
        
        messages = [
            {
                "role": "system",
                "content": system_content,
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
