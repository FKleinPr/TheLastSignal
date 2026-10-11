"""API endpoint for processing player commands.

Processes natural language commands through NLP parser or rule-based fallback.
Handles movement, items, character interaction, and game state changes.

Integration: Included in main.py as router for /api/games/{id}/commands.
"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from game_engine.parser import parse_command
from game_engine.commands import CommandEngine

router = APIRouter()


def process_game_command(game_state: dict, text: str, content: dict) -> Dict[str, Any]:
    """Process a game command and return response.
    
    Uses rule-based parser when LLM is unavailable.
    Returns Response dict with text, location, inventory, etc.
    """
    # Parse command
    parsed = parse_command(text)
    
    # Create engine and execute
    engine = CommandEngine(game_state, content)
    result = engine.execute_command(parsed)
    
    return result


@router.post("/api/games/{game_id}/commands")
def process_command(game_id: str, game_state: dict, content: dict, payload: dict):
    """Handle POST /api/games/{id}/commands endpoint.
    
    Returns Response with game state changes.
    """
    text = payload.get("text", "")
    
    if not text:
        raise HTTPException(status_code=422, detail="Empty or missing text")
    
    # Process command
    result = process_game_command(game_state, text, content)
    
    return result
