"""Rule-based parser for The Last Signal game server.

Parses natural language commands into structured actions when LLM is unavailable.
Supports verbs: go, take, drop, give, show, use, talk, ask, pick-lock, wait, save, load, continue, restart.

Integration: Called from game_engine/commands.py when LLM_BASE_URL is down or no valid JSON response.
"""

import re
from typing import Optional, Tuple, Dict, Any

from content.loader import get_locations, get_objects, get_characters


def normalize_direction(direction: str) -> Optional[str]:
    """Normalize direction aliases to full direction names."""
    direction = direction.lower().strip()
    aliases = {
        "n": "north", "north": "north",
        "s": "south", "south": "south",
        "e": "east", "east": "east",
        "w": "west", "west": "west",
    }
    return aliases.get(direction)


def get_valid_verbs() -> set:
    """Return set of valid verbs for the game."""
    return {
        "go", "take", "drop", "give", "show", "use", "talk", "ask",
        "pick-lock", "pick_lock", "wait", "save", "load", "continue", "restart"
    }


def get_valid_nouns() -> set:
    """Return set of all valid nouns (objects and characters)."""
    valid = set()
    
    # Get objects
    objects = get_objects()
    for obj_id, obj_data in objects.items():
        valid.add(obj_id)
        if "names" in obj_data:
            for name in obj_data["names"]:
                valid.add(name.lower())
    
    # Get characters
    characters = get_characters()
    for char_id in characters.keys():
        valid.add(char_id)
    
    return valid


def parse_command(text: str) -> Optional[Dict[str, Any]]:
    """Parse natural language command into structured action.
    
    Returns dict with verb, object, target, or None if no intent found.
    Returns {"verb": null} for unknown commands (no intent detected).
    """
    text = text.lower().strip()
    
    if not text:
        return None
    
    # Handle special commands that are exact matches
    if text in ["save", "load", "continue_from_checkpoint", "restart_act_i"]:
        return {"verb": text}
    
    # Try to match known verbs
    verbs = get_valid_verbs()
    
    # Pattern: verb (object/target) [to target]
    # Examples: "go north", "take core", "talk to priest-voa", "give key to merchant-jex"
    
    # Go commands (movement) - with "go" prefix
    go_match = re.match(r"go\s+(north|south|east|west|n|s|e|w)\b", text)
    if go_match:
        direction = normalize_direction(go_match.group(1))
        if direction:
            return {"verb": "go", "direction": direction}
    
    # Simple go commands with direction as direct text - with "go" prefix
    if text.startswith("go "):
        rest = text[3:].strip()
        direction = normalize_direction(rest)
        if direction:
            return {"verb": "go", "direction": direction}
    
    # Bare direction commands (e.g., "north", "n", "south", "s")
    if text in ["north", "south", "east", "west", "n", "s", "e", "w"]:
        direction = normalize_direction(text)
        if direction:
            return {"verb": "go", "direction": direction}
    
    # Take commands
    take_match = re.match(r"take\s+(.+)", text)
    if take_match:
        object_name = take_match.group(1).strip()
        # Check if object exists
        if object_name in get_valid_nouns():
            return {"verb": "take", "object": object_name}
    
    # Drop commands
    drop_match = re.match(r"drop\s+(.+)", text)
    if drop_match:
        object_name = drop_match.group(1).strip()
        if object_name in get_valid_nouns():
            return {"verb": "drop", "object": object_name}
    
    # Give commands: "give X to Y"
    give_match = re.match(r"give\s+(\S+)\s+to\s+(\S+)", text)
    if give_match:
        object_name = give_match.group(1).strip()
        target_name = give_match.group(2).strip()
        if object_name in get_valid_nouns() and target_name in get_valid_nouns():
            return {"verb": "give", "object": object_name, "target": target_name}
    
    # Show commands: "show X to Y"
    show_match = re.match(r"show\s+(\S+)\s+to\s+(\S+)", text)
    if show_match:
        object_name = show_match.group(1).strip()
        target_name = show_match.group(2).strip()
        if object_name in get_valid_nouns() and target_name in get_valid_nouns():
            return {"verb": "show", "object": object_name, "target": target_name}
    
    # Use commands: "use X on Y"
    use_match = re.match(r"use\s+(\S+)\s+on\s+(\S+)", text)
    if use_match:
        object_name = use_match.group(1).strip()
        target_name = use_match.group(2).strip()
        if object_name in get_valid_nouns() and target_name in get_valid_nouns():
            return {"verb": "use", "object": object_name, "target": target_name}
    
    # Talk commands: "talk to Y"
    talk_match = re.match(r"talk\s+to\s+(\S+)", text)
    if talk_match:
        target_name = talk_match.group(1).strip()
        if target_name in get_valid_nouns():
            return {"verb": "talk", "target": target_name}
    
    # Ask commands: "ask X about Y"
    ask_match = re.match(r"ask\s+(\S+)\s+about\s+(\S+)", text)
    if ask_match:
        target_name = ask_match.group(1).strip()
        object_name = ask_match.group(2).strip()
        if target_name in get_valid_nouns() and object_name in get_valid_nouns():
            return {"verb": "ask", "target": target_name, "object": object_name}
    
    # Pick-lock command
    if text.startswith("pick-lock") or text.startswith("pick lock"):
        return {"verb": "pick-lock"}
    
    # Wait command
    if text == "wait":
        return {"verb": "wait"}
    
    # Return None for unknown commands (no intent detected)
    return {"verb": None}


def find_ambiguous_matches(text: str, valid_nouns: set) -> Optional[str]:
    """Find ambiguous matches where multiple nouns match the same word.
    
    Returns the ambiguous word if found, None otherwise.
    Used to ask player to clarify.
    """
    words = text.split()
    matches = {}
    
    for word in words:
        if word in valid_nouns:
            if word not in matches:
                matches[word] = []
            matches[word].append(word)
    
    if len(matches) > 1:
        return list(matches.keys())[0]
    
    return None
