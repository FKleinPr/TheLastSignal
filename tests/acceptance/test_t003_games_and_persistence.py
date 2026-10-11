"""Acceptance tests for Task T-003: Games and persistence.

These tests verify that the game server can create game sessions,
maintain state between turns, and persist that state to SQLite.

Tested through the interfaces in the plan only (T-003 endpoints).
"""

import pytest
from game_data import TEXT, placeholder


# =============================================================================
# AC-001: Game creation and starting location
# =============================================================================

def test_ac001_new_game_starts_at_bone_yard(game: dict) -> None:
    """Verifies: AC-001, FR-001. New game starts at bone-yard with empty inventory."""
    response = game["response"]
    
    assert response["location"] == "bone-yard", \
        f"Expected start location 'bone-yard', got '{response['location']}'"
    assert response["inventory"] == [], \
        f"Expected empty inventory at start, got {response['inventory']}"
    assert response["turn"] == 0, \
        f"Expected turn to start at 0, got {response['turn']}"


def test_ac001_new_game_returns_game_id(game: dict) -> None:
    """Verifies: AC-001, FR-001. Game creation returns valid game_id."""
    game_id = game["game_id"]
    
    assert isinstance(game_id, str), \
        f"Expected game_id to be string, got {type(game_id)}"
    assert len(game_id) == 36, \
        f"Expected 36-character UUID-style game_id, got {len(game_id)}"


# =============================================================================
# AC-012: HTTP API endpoints and Response/State structures
# =============================================================================

def test_ac012_post_games_creates_game(game: dict) -> None:
    """Verifies: AC-012, FR-019. POST /api/games creates new game with 201 status."""
    assert game["game_id"] is not None, \
        "Expected game_id in POST /api/games response"
    assert game["response"]["location"] is not None, \
        "Expected location in response"


def test_ac012_response_structure(game: dict) -> None:
    """Verifies: AC-012, FR-017, FR-021. Response has exactly 9 fields."""
    response = game["response"]
    
    expected_fields = ["game_id", "text", "location", "inventory", "pictures", 
                       "choices", "dead", "ending", "turn"]
    actual_fields = list(response.keys())
    
    assert set(actual_fields) == set(expected_fields), \
        f"Response has wrong fields. Expected {expected_fields}, got {actual_fields}"


def test_ac012_response_fields_content(game: dict) -> None:
    """Verifies: AC-012, FR-017. Response content matches spec."""
    response = game["response"]
    
    assert response["location"] == "bone-yard", \
        f"Expected location 'bone-yard', got '{response['location']}'"
    assert response["inventory"] == [], \
        f"Expected empty inventory, got {response['inventory']}"
    assert response["turn"] == 0, \
        f"Expected turn 0, got {response['turn']}"
    assert response["dead"] is False, \
        f"Expected dead false, got {response['dead']}"
    assert response["ending"] is None, \
        f"Expected ending null, got {response['ending']}"
    assert response["choices"] == [], \
        f"Expected choices [], got {response['choices']}"
    assert TEXT["opening"] in response["text"], \
        f"Expected opening text in response, got: {response['text']}"


def test_ac012_response_pictures(game: dict) -> None:
    """Verifies: AC-012, FR-017. Response includes pictures list."""
    response = game["response"]
    
    assert "pictures" in response, "Response missing 'pictures' field"
    assert isinstance(response["pictures"], list), \
        f"Expected pictures to be list, got {type(response['pictures'])}"
    
    # Check that bone-yard is in pictures with correct structure
    bone_yard_pic = None
    for p in response["pictures"]:
        if p["name"] == "bone-yard":
            bone_yard_pic = p
            break
    
    assert bone_yard_pic is not None, "Picture list missing 'bone-yard' entry"
    assert "name" in bone_yard_pic, "Picture missing 'name'"
    assert "type" in bone_yard_pic, "Picture missing 'type'"
    assert "size" in bone_yard_pic, "Picture missing 'size'"
    assert "available" in bone_yard_pic, "Picture missing 'available'"
    assert "terminal" in bone_yard_pic, "Picture missing 'terminal'"
    assert "placeholder" in bone_yard_pic, "Picture missing 'placeholder'"


def test_ac012_get_games_returns_state(game: dict, api) -> None:
    """Verifies: AC-012, FR-019. GET /api/games/{id} returns game state."""
    game_id = game["game_id"]
    
    state = api.state(game_id)
    
    assert state["game_id"] == game_id, \
        f"GET state game_id mismatch: expected {game_id}, got {state['game_id']}"
    assert "dead" in state, "State missing 'dead' field"
    assert "ending" in state, "State missing 'ending' field"


def test_ac012_get_games_404_unknown_game(api) -> None:
    """Verifies: AC-012, FR-019. GET /api/games/{id} returns 404 for unknown game."""
    unknown_id = "00000000-0000-0000-0000-000000000000"
    
    r = api.state_raw(unknown_id)
    assert r.status_code == 404, \
        f"Expected 404 for unknown game, got {r.status_code}"


def test_ac012_state_structure(game: dict, api) -> None:
    """Verifies: AC-012, FR-002. State has exactly 12 fields."""
    game_id = game["game_id"]
    state = api.state(game_id)
    
    expected_fields = ["game_id", "location", "inventory", "flags", "relationships", 
                       "clues", "events", "turn", "dead", "ending", "has_checkpoint", "has_save"]
    actual_fields = list(state.keys())
    
    assert set(actual_fields) == set(expected_fields), \
        f"State has wrong fields. Expected {expected_fields}, got {actual_fields}"


def test_ac012_state_fields_content(game: dict, api) -> None:
    """Verifies: AC-012, FR-002. State content matches spec."""
    game_id = game["game_id"]
    state = api.state(game_id)
    
    assert state["location"] == "bone-yard", \
        f"Expected location 'bone-yard', got '{state['location']}'"
    assert state["inventory"] == [], \
        f"Expected empty inventory, got {state['inventory']}"
    assert state["flags"] == [], \
        f"Expected empty flags, got {state['flags']}"
    assert state["clues"] == [], \
        f"Expected empty clues, got {state['clues']}"
    assert state["events"] == [], \
        f"Expected empty events, got {state['events']}"
    assert state["turn"] == 0, \
        f"Expected turn 0, got {state['turn']}"
    assert state["dead"] is False, \
        f"Expected dead false, got {state['dead']}"
    assert state["ending"] is None, \
        f"Expected ending null, got {state['ending']}"
    assert state["has_checkpoint"] is True, \
        f"Expected has_checkpoint true, got {state['has_checkpoint']}"
    assert state["has_save"] is False, \
        f"Expected has_save false, got {state['has_save']}"
    assert isinstance(state["relationships"], dict), \
        f"Expected relationships to be dict, got {type(state['relationships'])}"


# =============================================================================
# AC-002: State maintenance and persistence
# =============================================================================

def test_ac002_state_consistency_multiple_gets(game: dict, api) -> None:
    """Verifies: AC-002, FR-002. State is consistent across multiple GET requests."""
    game_id = game["game_id"]
    
    # Get state 5 times
    states = []
    for _ in range(5):
        state = api.state(game_id)
        states.append(state)
    
    # All states should have same location, inventory, turn
    for i, state in enumerate(states[1:], start=1):
        assert state["location"] == states[0]["location"], \
            f"Location changed between GET {i} and GET 0"
        assert state["inventory"] == states[0]["inventory"], \
            f"Inventory changed between GET {i} and GET 0"
        assert state["turn"] == states[0]["turn"], \
            f"Turn changed between GET {i} and GET 0"


def test_ac002_state_persists_across_requests(game: dict, api) -> None:
    """Verifies: AC-002, FR-002. State persists across requests without commands."""
    game_id = game["game_id"]
    
    # Get state, then get it again after some time
    state1 = api.state(game_id)
    state2 = api.state(game_id)
    
    assert state1["location"] == state2["location"], \
        "Location changed between requests"
    assert state1["inventory"] == state2["inventory"], \
        "Inventory changed between requests"
    assert state1["flags"] == state2["flags"], \
        "Flags changed between requests"
    assert state1["turn"] == state2["turn"], \
        "Turn changed between requests"


# =============================================================================
# AC-012: Response dead/ending fields (AC-007, AC-021)
# =============================================================================

def test_ac012_response_dead_ending_fields(game: dict, api) -> None:
    """Verifies: AC-012, FR-021. Response includes dead (bool) and ending (null/str) fields."""
    game_id = game["game_id"]
    
    state = api.state(game_id)
    
    assert "dead" in state, "State missing 'dead' field"
    assert isinstance(state["dead"], bool), \
        f"Expected dead to be bool, got {type(state['dead'])}"
    assert "ending" in state, "State missing 'ending' field"
    assert state["ending"] is None, \
        f"Expected ending to be None at start, got {state['ending']}"


# =============================================================================
# AC-002: Two new games get different ids
# =============================================================================

def test_ac002_two_games_different_ids(api) -> None:
    """Verifies: AC-002, FR-002. Two new games get different ids."""
    game1 = api.new_game()
    game2 = api.new_game()
    
    assert game1["game_id"] != game2["game_id"], \
        f"Expected different game_ids, got {game1['game_id']} and {game2['game_id']}"
    
    # Each State answers with its own game_id
    state1 = api.state(game1["game_id"])
    state2 = api.state(game2["game_id"])
    
    assert state1["game_id"] == game1["game_id"], \
        f"State1 game_id mismatch"
    assert state2["game_id"] == game2["game_id"], \
        f"State2 game_id mismatch"


# =============================================================================
# AC-012: Reset functionality
# =============================================================================

def test_ac012_reset_deletes_games(api) -> None:
    """Verifies: AC-012, FR-019. After reset, GET of a game created before answers 404."""
    game = api.new_game()
    game_id = game["game_id"]
    
    # Reset state
    api.reset_raw()
    
    # Try to get the old game
    r = api.state_raw(game_id)
    assert r.status_code == 404, \
        f"Expected 404 after reset, got {r.status_code}"
