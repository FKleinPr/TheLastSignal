"""Rule-based parser for The Last Signal game server.

Parses natural language commands into structured actions when LLM is unavailable.
Supports verbs: go, take, drop, give, show, use, talk, ask, pick-lock, wait, save, load, continue, restart, look.

Integration: Called from game_engine/commands.py when LLM_BASE_URL is down or no valid JSON response.

LLM Integration: When LLM_BASE_URL is set and model is reachable, calls LLM endpoint first.
If LLM returns valid JSON with non-null verb from the verb list AND all named entities are present,
uses that intent. If LLM is down, returns invalid JSON, or names things not present, falls back to
rule-based parsing. For "go" commands, converts model's "object" to "direction".
"""

import re
from typing import Optional, Dict, Any

from content.loader import get_locations, get_objects, get_characters, get_narrator
from game_engine.ambiguity import check_ambiguity, get_present_thing_names
from nlp.llm_parser import interpret_natural_language, record_request


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
        "pick-lock", "pick_lock", "wait", "save", "load", "continue", "restart", "look"
    }


def get_valid_nouns(game_state: Optional[dict] = None, current_location: Optional[str] = None) -> set:
    """Return set of all valid nouns (objects and characters)."""
    valid = set()
    
    # Get objects
    objects = get_objects()
    for obj_id, obj_data in objects.items():
        valid.add(obj_id)
        if "names" in obj_data:
            for name in obj_data["names"]:
                valid.add(name.lower())
    
    # Get characters - add all character names/synonyms (case-insensitive)
    characters = get_characters()
    for char_id, char_data in characters.items():
        valid.add(char_id)
        if "names" in char_data:
            for name in char_data["names"]:
                valid.add(name.lower())
    
    # Add directions if game_state and current_location provided
    if game_state and current_location:
        location_data = get_locations().get(current_location, {})
        exits = location_data.get("exits", [])
        for exit_info in exits:
            direction = exit_info.get("direction")
            if direction:
                valid.add(direction.lower())
    
    return valid


def _check_entity_present(entity_type: str, entity_name: str, game_state: dict, current_location: str) -> bool:
    """Check if an entity is present in the current context.
    
    For "take" commands: object must be in current location or inventory.
    For "go" commands: direction must be valid exit from current location.
    For "talk" commands: character must be in current location.
    For "give"/"show"/"use" commands: object must be in inventory, target must be in current location.
    
    Returns True if entity is present, False otherwise.
    """
    if entity_type == "object":
        # Check if object is in current location or inventory
        location_data = get_locations().get(current_location, {})
        objects_in_location = location_data.get("objects", [])
        objects = get_objects()
        
        # Check if object ID matches
        if entity_name in objects_in_location:
            return True
        
        # Check if entity_name is a synonym for an object in location
        for obj_id in objects_in_location:
            if obj_id in objects:
                obj_names = objects[obj_id].get("names", [])
                if entity_name.lower() in [names.lower() for names in obj_names]:
                    return True
        
        # Check if object is in inventory
        if entity_name in game_state.get("inventory", []):
            return True
        
        # Check if entity_name is a synonym for an object in inventory
        for inv_obj_id in game_state.get("inventory", []):
            if inv_obj_id in objects:
                obj_names = objects[inv_obj_id].get("names", [])
                if entity_name.lower() in [names.lower() for names in obj_names]:
                    return True
        
        return False
    
    elif entity_type == "direction":
        # Check if direction is valid exit from current location
        location_data = get_locations().get(current_location, {})
        exits = location_data.get("exits", [])
        for exit_info in exits:
            if exit_info.get("direction") == entity_name:
                return True
        return False
    
    elif entity_type == "character":
        # Check if character is in current location
        location_data = get_locations().get(current_location, {})
        characters_here = location_data.get("characters", [])
        characters = get_characters()
        
        # Normalize entity_name: remove optional "the", lower case
        normalized_name = entity_name.lower().strip()
        
        # Check if entity_name matches any character's names
        for char_id in characters_here:
            if char_id in characters:
                char_names = characters[char_id].get("names", [])
                # Check if normalized_name matches any of the character's names (case-insensitive)
                if normalized_name in [names.lower() for names in char_names]:
                    return True
        
        return False
    
    return False


def _validate_llm_intent(intent: Dict[str, Any], game_state: dict, current_location: str) -> bool:
    """Validate LLM intent: verb must be non-null and valid, named entities must be present.
    
    Returns True if intent is valid, False otherwise (fall back to rule-based).
    """
    verb = intent.get("verb")
    
    # LLM returned null or empty verb - invalid, use rule-based
    if not verb or not isinstance(verb, str) or verb.strip() == "":
        return False
    
    # Check if verb is in valid verb list
    valid_verbs = get_valid_verbs()
    if verb not in valid_verbs:
        return False
    
    # Check named entities are present
    if "object" in intent and intent.get("object") is not None:
        object_name = intent.get("object", "")
        if not isinstance(object_name, str) or object_name.strip() == "":
            return False
        
        # For "go" commands, object is actually a direction
        if verb == "go":
            if not _check_entity_present("direction", object_name.lower(), game_state, current_location):
                return False
        else:
            if not _check_entity_present("object", object_name.lower(), game_state, current_location):
                return False
    
    # Check target if present
    if "target" in intent and intent.get("target") is not None:
        target_name = intent.get("target", "")
        if not isinstance(target_name, str) or target_name.strip() == "":
            return False
        
        # For talk/give/show/use, target is a character
        if verb in ["talk", "give", "show", "use", "ask"]:
            if not _check_entity_present("character", target_name.lower(), game_state, current_location):
                return False
    
    return True


def _convert_llm_intent_to_command(intent: Dict[str, Any], game_state: dict) -> Dict[str, Any]:
    """Convert LLM intent to command format.
    
    For "go" commands, converts "object" to "direction".
    Returns command dict ready for execution.
    """
    verb = intent.get("verb", "")
    
    if verb == "go":
        # Model returns direction in "object" field, convert to "direction"
        direction = intent.get("object")
        if direction:
            direction = normalize_direction(direction)
            if direction:
                return {"verb": "go", "direction": direction}
        return {"verb": "go"}
    
    # For other verbs, keep as is
    return intent


def parse_command(text: str, game_state: Optional[dict] = None, content: Optional[dict] = None) -> Optional[Dict[str, Any]]:
    """Parse natural language command into structured action.
    
    First tries LLM interpretation if LLM_BASE_URL is set and model is reachable.
    If LLM returns valid JSON with non-null verb from the verb list AND all named entities are present,
    uses that intent. If LLM is down, returns invalid JSON, or names things not present, falls back to
    rule-based parsing.
    
    Returns dict with verb, object, target, or None if no intent found.
    Returns {"verb": null} for unknown commands (no intent detected).
    Returns {"verb": "ambiguous"} with options when ambiguity detected.
    """
    text_lower = text.lower().strip()
    
    if not text_lower:
        return None
    
    # Handle special commands that are exact matches
    if text_lower in ["save", "load", "continue_from_checkpoint", "restart_act_i"]:
        return {"verb": text_lower}
    
    # Handle look command (exact match)
    if text_lower == "look":
        return {"verb": "look"}
    
    # Record LLM request before calling (for testing)
    if game_state and content:
        record_request(text)
    
    # Get current location and inventory from game_state
    current_location = game_state.get("player_location", "") if game_state else ""
    inventory = game_state.get("inventory", []) if game_state else []
    
    # Get characters in current location from content
    characters_here = []
    if content and "locations" in content:
        location_data = content["locations"].get(current_location, {})
        characters_here = location_data.get("characters", [])
    
    # Get narrator "ambiguous" line from content
    narrator_ambiguous = ""
    if content and "narrator" in content:
        narrator_ambiguous = content["narrator"].get("ambiguous", "Which")
    
    # Check ambiguity BEFORE LLM and rule-based parsing (per reviewer hint)
    # This must be done before any state-changing logic
    ambiguity_result = check_ambiguity_for_command(text_lower, current_location, inventory, characters_here, narrator_ambiguous)
    if ambiguity_result:
        return ambiguity_result
    
    # Try LLM interpretation if available
    llm_intent = None
    if game_state and content:
        llm_intent = interpret_natural_language(text, {"game_state": game_state, "content": content})
    
    # Validate LLM intent: must have non-null valid verb and all named entities present
    if llm_intent and isinstance(llm_intent, dict) and "verb" in llm_intent:
        if _validate_llm_intent(llm_intent, game_state, current_location):
            # Convert LLM intent to command format (e.g., "object" to "direction" for "go")
            return _convert_llm_intent_to_command(llm_intent, game_state)
    
    # Fall back to rule-based parsing when LLM intent is invalid/null or LLM is down
    return _parse_rule_based(text_lower, game_state)


def _parse_rule_based(text: str, game_state: Optional[dict] = None) -> Optional[Dict[str, Any]]:
    """Parse command using rule-based approach (when LLM unavailable or invalid)."""
    if not text:
        return None
    # An article before a name is optional: "talk to the merchant" is "talk to merchant" (CR-001)
    text = re.sub(r"\bthe\s+", "", text)
    
    # Get current location for context
    current_location = None
    if game_state:
        current_location = game_state.get("player_location", "")
    
    # Look command (exact match for "look")
    if text == "look":
        return {"verb": "look"}
    
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
        if object_name in get_valid_nouns(game_state, current_location):
            return {"verb": "take", "object": object_name}
    
    # Drop commands
    drop_match = re.match(r"drop\s+(.+)", text)
    if drop_match:
        object_name = drop_match.group(1).strip()
        if object_name in get_valid_nouns(game_state, current_location):
            return {"verb": "drop", "object": object_name}
    
    # Give commands: "give X to Y"
    give_match = re.match(r"give\s+(\S+)\s+to\s+(\S+)", text)
    if give_match:
        object_name = give_match.group(1).strip()
        target_name = give_match.group(2).strip()
        if object_name in get_valid_nouns(game_state, current_location) and target_name in get_valid_nouns(game_state, current_location):
            return {"verb": "give", "object": object_name, "target": target_name}
    
    # Show commands: "show X to Y"
    show_match = re.match(r"show\s+(\S+)\s+to\s+(\S+)", text)
    if show_match:
        object_name = show_match.group(1).strip()
        target_name = show_match.group(2).strip()
        if object_name in get_valid_nouns(game_state, current_location) and target_name in get_valid_nouns(game_state, current_location):
            return {"verb": "show", "object": object_name, "target": target_name}
    
    # Use commands: "use X on Y"
    use_match = re.match(r"use\s+(\S+)\s+on\s+(\S+)", text)
    if use_match:
        object_name = use_match.group(1).strip()
        target_name = use_match.group(2).strip()
        valid = get_valid_nouns(game_state, current_location) | {"door", "gate", "lock"}  # the sanctum door
        if object_name in valid and target_name in valid:
            return {"verb": "use", "object": object_name, "target": target_name}
    
    # Talk commands: "talk to Y" (accept synonyms)
    talk_match = re.match(r"talk\s+to\s+(\S+)", text)
    if talk_match:
        target_name = talk_match.group(1).strip()
        if target_name in get_valid_nouns(game_state, current_location):
            return {"verb": "talk", "target": target_name}
    
    # Ask commands: "ask X about Y"
    ask_match = re.match(r"ask\s+(\S+)\s+about\s+(\S+)", text)
    if ask_match:
        target_name = ask_match.group(1).strip()
        object_name = ask_match.group(2).strip()
        if target_name in get_valid_nouns(game_state, current_location) and object_name in get_valid_nouns(game_state, current_location):
            return {"verb": "ask", "target": target_name, "object": object_name}
    
    # Pick-lock command
    if text.startswith("pick-lock") or text.startswith("pick lock"):
        return {"verb": "pick-lock"}
    
    # Wait command
    if text == "wait":
        return {"verb": "wait"}
    
    # Return None for unknown commands (no intent detected)
    return {"verb": None}


def check_ambiguity_for_command(text: str, current_location: str, inventory: list, characters_here: list, narrator_ambiguous: str) -> Optional[Dict[str, Any]]:
    """Check if command is ambiguous and return ambiguity response.
    
    Returns dict with {"verb": "ambiguous", "options": [...], "text": "..."} or None if no ambiguity.
    Does not modify state.
    Only checks character matches for talk commands.
    """
    from game_engine.ambiguity import check_ambiguity
    
    # Extract just the target from the text for ambiguity checking
    # This is needed because check_ambiguity() checks all present things, but we want to focus on characters
    # for talk commands
    
    # Get ambiguity text from the check_ambiguity function
    ambiguity_response = check_ambiguity(text, current_location, inventory, characters_here, narrator_ambiguous)
    
    if ambiguity_response:
        return {"verb": "ambiguous", "text": ambiguity_response}
    
    return None
