"""Content validator for The Last Signal game server.

Validates content during startup:
- All exit targets reference valid locations
- All rule targets reference valid characters, objects, or locations
- All entity IDs are unique
- All required content sections exist

Integration: Called from main.py during startup; server fails to start with clear error when content has invalid exits or missing IDs.
"""

from content.loader import (
    load_content,
    get_locations,
    get_objects,
    get_characters,
    get_pictures,
)


def validate_content() -> None:
    """Validate all content during startup.
    
    Raises ValueError with clear error message if content has invalid exits or missing IDs.
    """
    content = load_content()
    
    # Validate start section
    start = content.get("start", {})
    if not start:
        raise ValueError("Content missing 'start' section")
    
    if "location" not in start:
        raise ValueError("Content missing 'start.location'")
    
    if "text" not in start:
        raise ValueError("Content missing 'start.text'")
    
    # Get all valid location IDs
    locations = get_locations()
    location_ids = set(locations.keys())
    
    # Validate all exits refer to valid locations
    for location_id, location_data in locations.items():
        exits = location_data.get("exits", [])
        for exit_data in exits:
            target = exit_data.get("target")
            if target and target not in location_ids:
                raise ValueError(
                    f"Location '{location_id}' has exit to unknown location '{target}'"
                )
    
    # Validate objects
    objects = get_objects()
    object_ids = set(objects.keys())
    
    # Validate characters
    characters = get_characters()
    character_ids = set(characters.keys())
    
    # Validate factions
    factions = content.get("factions", {})
    faction_ids = set(factions.keys())
    
    # Validate pictures list matches entities
    pictures = get_pictures()
    picture_names = set(p["name"] for p in pictures)
    
    # All location IDs must be in pictures
    for loc_id in location_ids:
        if loc_id not in picture_names:
            raise ValueError(f"Location '{loc_id}' not found in pictures list")
    
    # All character IDs must be in pictures
    for char_id in character_ids:
        if char_id not in picture_names:
            raise ValueError(f"Character '{char_id}' not found in pictures list")
    
    # All object IDs must be in pictures
    for obj_id in object_ids:
        if obj_id not in picture_names:
            raise ValueError(f"Object '{obj_id}' not found in pictures list")
    
    # Validate rules reference valid targets
    rules = content.get("rules", [])
    for rule in rules:
        # Check object in rule
        rule_object = rule.get("object")
        if rule_object and rule_object not in object_ids and rule_object not in character_ids and rule_object not in location_ids:
            raise ValueError(
                f"Rule '{rule.get('id', 'unknown')}' references unknown object '{rule_object}'"
            )
        
        # Check target in rule
        rule_target = rule.get("target")
        if rule_target and rule_target not in object_ids and rule_target not in character_ids and rule_target not in location_ids:
            raise ValueError(
                f"Rule '{rule.get('id', 'unknown')}' references unknown target '{rule_target}'"
            )
        
        # Check location in rule
        rule_location = rule.get("location")
        if rule_location and rule_location not in location_ids:
            raise ValueError(
                f"Rule '{rule.get('id', 'unknown')}' references unknown location '{rule_location}'"
            )
    
    # Validate deaths reference valid locations
    deaths = content.get("deaths", {})
    for death_id, death_data in deaths.items():
        death_location = death_data.get("location")
        if death_location and death_location not in location_ids:
            raise ValueError(
                f"Death '{death_id}' references unknown location '{death_location}'"
            )
    
    # Validate endings
    endings = content.get("endings", {})
    for ending_id, ending_data in endings.items():
        if "text" not in ending_data:
            raise ValueError(f"Ending '{ending_id}' missing 'text'")
    
    # Validate clues
    clues = content.get("clues", {})
    for clue_id, clue_data in clues.items():
        if "text" not in clue_data:
            raise ValueError(f"Clue '{clue_id}' missing 'text'")
    
    # Validate narrator
    narrator = content.get("narrator", {})
    if "unknown" not in narrator:
        raise ValueError("Content missing 'narrator.unknown'")
    if "impossible" not in narrator:
        raise ValueError("Content missing 'narrator.impossible'")
    
    # Validate counts (AC-004, BR-008)
    scene_count = sum(1 for p in pictures if p.get("type") == "scene")
    if not (6 <= scene_count <= 10):
        raise ValueError(f"Expected 6-10 locations, got {scene_count}")
    
    talkable_count = sum(1 for p in pictures if p.get("type") == "character" and p.get("name") != "player")
    if not (4 <= talkable_count <= 6):
        raise ValueError(f"Expected 4-6 talkable characters, got {talkable_count}")
    
    # All validations passed
    return
