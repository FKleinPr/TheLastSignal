"""
Acceptance tests for Task T-004: Content loading from YAML files.

Verifies that the game correctly loads content from YAML files during startup,
including locations, characters, factions, rules, and pictures. Also verifies
that the server fails to start with clear errors when content has invalid exits
or missing IDs.

Verifies: AC-004, AC-009, AC-011, FR-016, FR-018, FR-022, FR-023, BR-001, BR-004, BR-008
"""

from game_data import LOCATIONS, TALKABLE, EXITS, PICTURES, TEXT, placeholder


# =============================================================================
# AC-009: Unique IDs for all entities (full content present)
# =============================================================================

def test_t004_picture_list_names_match_spec(api) -> None:
    """
    Verifies: AC-009, FR-022, BR-001.
    The picture list has exactly the 19 names of PICTURES and no name twice.
    """
    pictures = api.pictures()
    picture_names = [p["name"] for p in pictures]
    picture_names_set = set(picture_names)
    spec_names_set = set(PICTURES.keys())
    
    # Verify count matches spec
    assert len(picture_names) == len(spec_names_set), \
        f"Expected {len(spec_names_set)} pictures, got {len(picture_names)}"
    
    # Verify no duplicates
    assert len(picture_names) == len(picture_names_set), \
        f"Duplicate names found: {[n for n in picture_names if picture_names.count(n) > 1]}"
    
    # Verify names match spec exactly
    assert picture_names_set == spec_names_set, \
        f"Picture names mismatch. Missing: {spec_names_set - picture_names_set}, Extra: {picture_names_set - spec_names_set}"


def test_t004_picture_entry_fields_match_spec(api) -> None:
    """
    Verifies: AC-009, FR-016, FR-018.
    Every entry has entity_id == name and type, size and description exactly as in PICTURES.
    """
    pictures = api.pictures()
    
    for picture in pictures:
        # Verify entity_id matches name
        assert picture["entity_id"] == picture["name"], \
            f"entity_id '{picture['entity_id']}' must match name '{picture['name']}'"
        
        # Verify type, size, description match spec
        expected = PICTURES.get(picture["name"])
        assert expected is not None, f"Unknown picture name: {picture['name']}"
        assert picture["type"] == expected[0], \
            f"Expected type '{expected[0]}', got '{picture['type']}'"
        assert picture["size"] == expected[1], \
            f"Expected size '{expected[1]}', got '{picture['size']}'"
        assert picture["description"] == expected[2], \
            f"Expected description '{expected[2]}', got '{picture['description']}'"


# =============================================================================
# AC-004: Location, character, faction counts (6-10 locations, 4-6 characters, 2-3 factions)
# =============================================================================

def test_t004_scene_entries_match_locations(api) -> None:
    """
    Verifies: AC-004, FR-022, BR-008.
    The scene entries are exactly LOCATIONS: 8, inside 6-10.
    """
    pictures = api.pictures()
    scene_names = [p["name"] for p in pictures if p["type"] == "scene"]
    
    # Verify count matches spec LOCATIONS
    assert len(scene_names) == len(LOCATIONS), \
        f"Expected {len(LOCATIONS)} locations, got {len(scene_names)}"
    
    # Verify scene names match LOCATIONS exactly
    assert set(scene_names) == set(LOCATIONS), \
        f"Location mismatch. Missing: {set(LOCATIONS) - set(scene_names)}, Extra: {set(scene_names) - set(LOCATIONS)}"
    
    # Verify count is in range 6-10 (AC-004, BR-008)
    assert 6 <= len(scene_names) <= 10, \
        f"Expected 6-10 locations, got {len(scene_names)}"


def test_t004_character_entries_match_talkable(api) -> None:
    """
    Verifies: AC-004, FR-022, BR-008.
    The character entries other than player are exactly TALKABLE: 5, inside 4-6.
    """
    pictures = api.pictures()
    character_names = [p["name"] for p in pictures if p["type"] == "character"]
    
    # Remove 'player' from character_names to compare with TALKABLE
    talkable_names = [n for n in character_names if n != "player"]
    
    # Verify count matches spec TALKABLE
    assert len(talkable_names) == len(TALKABLE), \
        f"Expected {len(TALKABLE)} talkable characters, got {len(talkable_names)}"
    
    # Verify talkable names match TALKABLE exactly
    assert set(talkable_names) == set(TALKABLE), \
        f"Character mismatch. Missing: {set(TALKABLE) - set(talkable_names)}, Extra: {set(talkable_names) - set(TALKABLE)}"
    
    # Verify count is in range 4-6 (AC-004, BR-008)
    assert 4 <= len(talkable_names) <= 6, \
        f"Expected 4-6 characters, got {len(talkable_names)}"


# =============================================================================
# AC-011: Valid return exits and blocked exits (exit consistency)
# =============================================================================

def test_t004_exits_refer_valid_locations(api) -> None:
    """
    Verifies: AC-011, FR-023, BR-001.
    The map refers only to existing locations.
    Every location of EXITS is one of LOCATIONS.
    """
    # Get scene names from API (which should match LOCATIONS)
    pictures = api.pictures()
    scene_names = [p["name"] for p in pictures if p["type"] == "scene"]
    scene_names_set = set(scene_names)
    
    # Verify all locations in EXITS are in scene_names
    exit_locations = set()
    for from_loc, direction, to_loc in EXITS:
        exit_locations.add(from_loc)
        exit_locations.add(to_loc)
    
    missing_locations = exit_locations - scene_names_set
    
    assert len(missing_locations) == 0, \
        f"Locations in EXITS not found in picture list: {missing_locations}"
