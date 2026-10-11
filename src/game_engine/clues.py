"""Clue system for The Last Signal game server.

Manages clue discovery and tracking in game state.
Clues are discovered when:
- Player looks at certain locations (clue-location)
- Player talks to certain characters (clue-character)
- Player takes certain objects (clue-object)

Integration: Called from commands.py when talk/take commands execute.
"""

from typing import Dict, Any, Optional, List

from content.loader import get_locations, get_objects, get_characters, get_clues


def discover_clue(clue_id: str, game_state: dict) -> None:
    """Discover a clue and add it to game state.
    
    Adds clue_id to game_state["clues"] if not already present.
    Does not modify state if clue already discovered.
    """
    if clue_id not in game_state.get("clues", []):
        if "clues" not in game_state:
            game_state["clues"] = []
        game_state["clues"].append(clue_id)


def get_clue_text(clue_id: str) -> Optional[str]:
    """Get the text of a discovered clue.
    
    Returns clue text from content.clues, or None if not found.
    """
    clues = get_clues()
    if clue_id in clues:
        return clues[clue_id].get("text", "")
    return None


def check_location_clue(location_id: str) -> Optional[str]:
    """Check if location has a discoverable clue.
    
    Returns clue_id if location has a clue, None otherwise.
    Clues are discovered when player looks at the location.
    """
    clues = get_clues()
    for clue_id, clue_data in clues.items():
        found_in = clue_data.get("found_in")
        if found_in == location_id:
            return clue_id
    return None


def check_character_clue(character_id: str, has_core: bool = False) -> Optional[str]:
    """Check if character has a discoverable clue.
    
    Returns clue_id if character has a clue, None otherwise.
    Some clues are conditional on game state (e.g., having core).
    """
    clues = get_clues()
    for clue_id, clue_data in clues.items():
        found_in = clue_data.get("found_in")
        if found_in == character_id:
            # Check if clue is conditional on having core
            conditional = clue_data.get("conditional")
            if conditional and not has_core:
                return None
            return clue_id
    return None


def check_object_clue(object_id: str) -> Optional[str]:
    """Check if object has a discoverable clue.
    
    Returns clue_id if object has a clue, None otherwise.
    Clues are discovered when player takes the object.
    """
    clues = get_clues()
    for clue_id, clue_data in clues.items():
        found_in = clue_data.get("found_in")
        if found_in == object_id:
            return clue_id
    return None
