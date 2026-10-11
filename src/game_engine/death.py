"""Death system for The Last Signal game server.

Handles death conditions and text.
Provides choices when dead: "continue" (restore checkpoint) or "restart" (reset game).

Integration: Called from process_command_in_game in main.py to handle dead state.
"""

from typing import Dict, Any, Optional, List

from content.loader import get_deaths


def trigger_death(game_state: dict) -> dict:
    """Trigger death and return death text and choices.
    
    Returns dict with:
    - text: death text from spec 9.8
    - dead: True
    - choices: ["continue", "restart"]
    """
    flags = game_state.get("flags", [])
    
    # Determine death type based on flags and location
    if "dust-active" in flags and game_state.get("player_location") == "bone-yard":
        dust_count = game_state.get("dust_count", 0)
        if dust_count >= 3:
            return {
                "text": "You are now part of the bone-yard's collection. It is not a selective collection.",
                "dead": True,
                "choices": ["continue", "restart"],
            }
    
    # Get death text from content
    deaths = get_deaths()
    current_location = game_state.get("player_location", "")
    
    # Find death text for current location
    for death_id, death_data in deaths.items():
        death_location = death_data.get("location")
        if death_location and death_location == current_location:
            return {
                "text": death_data.get("text", "You have died."),
                "dead": True,
                "choices": ["continue", "restart"],
            }
    
    # Default death text if no specific death found
    return {
        "text": "You have died. The game ends here.",
        "dead": True,
        "choices": ["continue", "restart"],
    }


def get_death_text(death_id: str) -> str:
    """Get death text for a specific death ID."""
    deaths = get_deaths()
    if death_id in deaths:
        return deaths[death_id].get("text", "You have died.")
    return "You have died."


def get_death_choices() -> List[str]:
    """Get the choices available when dead."""
    return ["continue", "restart"]


def is_dead(game_state: dict) -> bool:
    """Check if player is dead."""
    return game_state.get("dead", False)
