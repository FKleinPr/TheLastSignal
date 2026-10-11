"""Ambiguity detection for The Last Signal game server.

Detects when player input matches multiple present things (objects or characters) by their "names" list.
Returns structured response with options when ambiguity found, without changing state.

Integration: Called from parser.py before executing commands that could modify state.
"""

from typing import Dict, Any, Optional, List, Tuple

from content.loader import get_locations, get_objects, get_characters


def get_present_thing_names(current_location: str, inventory: List[str], characters_here: List[str]) -> Dict[str, List[str]]:
    """Get all present things (objects/characters) and their names.
    
    Returns dict mapping thing IDs to their names list.
    Objects: in current location or in inventory.
    Characters: in current location.
    """
    present_names: Dict[str, List[str]] = {}
    
    # Get objects in current location
    locations = get_locations()
    location_data = locations.get(current_location, {})
    objects_in_location = location_data.get("objects", [])
    
    # Add objects in location to present names
    objects = get_objects()
    for obj_id in objects_in_location:
        if obj_id in objects:
            obj_data = objects[obj_id]
            names = obj_data.get("names", [obj_id])
            present_names[obj_id] = names
    
    # Add objects in inventory to present names
    for obj_id in inventory:
        if obj_id in objects:
            obj_data = objects[obj_id]
            names = obj_data.get("names", [obj_id])
            present_names[obj_id] = names
    
    # Add characters in current location to present names
    characters = get_characters()
    for char_id in characters_here:
        if char_id in characters:
            char_data = characters[char_id]
            names = char_data.get("names", [char_id])
            present_names[char_id] = names
    
    return present_names


def find_ambiguous_matches(text: str, present_names: Dict[str, List[str]]) -> Optional[Tuple[str, List[str]]]:
    """Find ambiguous matches where a word in input matches multiple present things.
    
    Returns tuple of (ambiguous_word, list of matching thing IDs) or None if no ambiguity.
    Used to ask player to clarify.
    """
    words = text.lower().strip().split()
    matches: Dict[str, List[str]] = {}
    
    for word in words:
        word = word.strip().strip(',.!?')
        if not word:
            continue
        
        for thing_id, names in present_names.items():
            # Check if word matches any name (case-insensitive)
            if word.lower() in [n.lower() for n in names]:
                if word not in matches:
                    matches[word] = []
                matches[word].append(thing_id)
    
    # Return first ambiguity found
    for word, matches_list in matches.items():
        if len(matches_list) > 1:
            return (word, matches_list)
    
    return None


def format_ambiguity_response(ambiguous_word: str, matches: List[str], narrator_ambiguous: str) -> str:
    """Format ambiguity response text.
    
    Returns text starting with narrator.ambiguous line, naming each option by its ID.
    """
    options = ", ".join(sorted(matches))
    return f"{narrator_ambiguous} {ambiguous_word}? Options: {options}."


def check_ambiguity(text: str, current_location: str, inventory: List[str], characters_here: List[str], narrator_ambiguous: str) -> Optional[str]:
    """Check if input is ambiguous and return response text if so.
    
    Returns ambiguity response text or None if no ambiguity.
    Does not modify state.
    """
    present_names = get_present_thing_names(current_location, inventory, characters_here)
    
    ambiguous_result = find_ambiguous_matches(text, present_names)
    
    if ambiguous_result:
        ambiguous_word, matches = ambiguous_result
        return format_ambiguity_response(ambiguous_word, matches, narrator_ambiguous)
    
    return None
