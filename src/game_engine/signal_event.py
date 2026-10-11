"""Signal event system for The Last Signal game server.

Handles the Signal event that triggers when the player picks up the core in bone-yard.
Sets flags "core" and "dust-active", creates a checkpoint before the command, and records signal text.

Integration: Called from process_command_in_game in main.py after engine.execute_command().
"""

from typing import Dict, Any, Optional, List

from content.loader import get_locations, get_deaths, get_endings, get_clues, get_narrator


def trigger_signal_event(game_state: dict, current_location: str, inventory: list, action: str) -> dict:
    """Trigger Signal event when core is taken in bone-yard.
    
    Returns dict with:
    - text: Signal event text from spec 9.2
    - flags: Updated flags list
    - checkpoint_before: State snapshot before the command
    - set_dust_count: 0 (dust_count reset to 0 when signal event fires)
    
    Does not modify game_state directly; returns changes to apply.
    """
    # Check if this is the Signal event trigger: take core in bone-yard
    if current_location == "bone-yard" and action == "take" and "core" in (inventory or []):
        # Get signal text from spec 9.2
        signal_text = "The ship has woken up, and it knows you're here."
        
        # Return changes to apply - set dust_count to 0 when signal event fires
        return {
            "signal_text": signal_text,
            "set_flags": ["core", "dust-active"],
            "create_checkpoint": True,
            "set_dust_count": 0,  # Fix: set dust_count to 0 when signal event fires
        }
    
    return {}


def get_signal_text() -> str:
    """Get the Signal event text from spec 9.2."""
    return "The ship has woken up, and it knows you're here."


def has_signal_event(game_state: dict) -> bool:
    """Check if Signal event has been triggered."""
    flags = game_state.get("flags", [])
    return "core" in flags or "dust-active" in flags


def get_signal_flags(game_state: dict) -> List[str]:
    """Get flags related to signal event."""
    flags = game_state.get("flags", [])
    return [f for f in flags if f in ["core", "dust-active"]]
