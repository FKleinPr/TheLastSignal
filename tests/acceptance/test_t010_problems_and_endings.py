"""Acceptance tests for T-010: Problems and endings.

Verifies AC-006 (3 problems with >=2 solutions, at least one with different consequences) and AC-007
(death, restore, restart). Tests use api and game fixtures, game_data constants, and the planned interfaces
(T-003, T-005). No http_client, no URLs, no OS calls.
"""
import pytest

from game_data import (
    ROUTES,
    TEXT,
)


def test_gate_locked_blocks_sanctum(api, game):
    """Verifies: AC-006 (gate-locked problem blocks exit until solved)."""
    game_id = game["game_id"]
    # Go to sanctum, door is blocked
    api.run(game_id, ROUTES["to_sanctum"])
    # Now send go east and check that response
    r = api.cmd(game_id, "go east")
    assert r["location"] == "sanctum"
    assert TEXT["blocked"] in r["text"].lower()


def test_gate_solved_by_pick(api, game):
    """Verifies: AC-006 (gate-locked problem solvable by lock-pick, consequences: silencer-leader < 0)."""
    game_id = game["game_id"]
    api.run(game_id, ROUTES["gate_by_pick"])
    # Now send go east and check location control-center
    r = api.cmd(game_id, "go east")
    assert r["location"] == "control-center"
    # State should show silencer-leader relationship < 0
    state = api.state(game_id)
    assert state["relationships"].get("silencer-leader", 0) < 0


def test_gate_solved_by_key(api, game):
    """Verifies: AC-006 (gate-locked problem solvable by key, consequences: merchant-jex < 0, silencer-leader >= 0)."""
    game_id = game["game_id"]
    api.run(game_id, ROUTES["gate_by_key"])
    # Now send go east and check location control-center
    r = api.cmd(game_id, "go east")
    assert r["location"] == "control-center"
    # State should show merchant-jex relationship < 0 and silencer-leader not below 0
    state = api.state(game_id)
    assert state["relationships"].get("merchant-jex", 0) < 0
    assert state["relationships"].get("silencer-leader", 0) >= 0


def test_pick_lock_without_tool(api, game):
    """Verifies: AC-006 (impossible action when no tool, no state change)."""
    game_id = game["game_id"]
    api.run(game_id, ROUTES["to_sanctum"])
    # Now try pick lock without lock-pick
    r = api.cmd(game_id, "pick lock")
    # Should have impossible text
    assert TEXT["impossible"] in r["text"]
    # Location should still be sanctum (blocked)
    assert r["location"] == "sanctum"
    # Try go east again - should still be blocked
    r = api.cmd(game_id, "go east")
    assert r["location"] == "sanctum"


def test_ending_awakeners(api, game):
    """Verifies: AC-006 (ending-awakeners conditions, text, warning)."""
    game_id = game["game_id"]
    responses = api.run(game_id, ROUTES["ending_awakeners"])
    # Last response: ending-awakeners, location deep-ribs, text contains ending text
    assert responses[-1]["ending"] == "ending-awakeners"
    assert responses[-1]["location"] == "deep-ribs"
    assert TEXT["ending-awakeners"] in responses[-1]["text"]
    # Second to last: should have awakening_warning
    assert TEXT["awakening_warning"] in responses[-2]["text"]
    # State should show ending-awakeners
    state = api.state(game_id)
    assert state["ending"] == "ending-awakeners"


def test_ending_silencers(api, game):
    """Verifies: AC-006 (ending-silencers conditions, text)."""
    game_id = game["game_id"]
    responses = api.run(game_id, ROUTES["ending_silencers"])
    # Last response: ending-silencers, text contains ending text
    assert responses[-1]["ending"] == "ending-silencers"
    assert TEXT["ending-silencers"] in responses[-1]["text"]


def test_ending_escape(api, game):
    """Verifies: AC-006 (ending-escape conditions, text, location)."""
    game_id = game["game_id"]
    responses = api.run(game_id, ROUTES["ending_escape"])
    # Last response: ending-escape, location edge-of-town, text contains ending text
    assert responses[-1]["ending"] == "ending-escape"
    assert responses[-1]["location"] == "edge-of-town"
    assert TEXT["ending-escape"] in responses[-1]["text"]


def test_death_awakening(api, game):
    """Verifies: AC-007 (death-awakening warning and death text)."""
    game_id = game["game_id"]
    responses = api.run(game_id, ROUTES["death_awakening"])
    # Second to last: should have awakening_warning
    assert TEXT["awakening_warning"] in responses[-2]["text"]
    # Last: dead true, text contains death text
    assert responses[-1]["dead"] is True
    assert TEXT["awakening_death"] in responses[-1]["text"]


def test_death_faction(api, game):
    """Verifies: AC-007 (death-faction warning and death text)."""
    game_id = game["game_id"]
    responses = api.run(game_id, ROUTES["death_faction"])
    # Second to last: should have faction_warning, dead false
    assert TEXT["faction_warning"] in responses[-2]["text"]
    assert responses[-2]["dead"] is False
    # Last: dead true, text contains death text
    assert responses[-1]["dead"] is True
    assert TEXT["faction_death"] in responses[-1]["text"]


def test_death_humming(api, game):
    """Verifies: AC-007 (death-humming warning and death text)."""
    game_id = game["game_id"]
    responses = api.run(game_id, ROUTES["death_humming"])
    # Third to last: should have humming_warning
    assert TEXT["humming_warning"] in responses[-3]["text"]
    # Last: dead true, text contains death text
    assert responses[-1]["dead"] is True
    assert TEXT["humming_death"] in responses[-1]["text"]


def test_ending_persistence_and_restart(api, game):
    """Verifies: AC-006 (ending persistence after ending, restart resets game)."""
    game_id = game["game_id"]
    # Play to ending
    api.run(game_id, ROUTES["ending_escape"])
    # Look after ending should still show ending
    r = api.cmd(game_id, "look")
    assert r["ending"] == "ending-escape"
    # Restart should reset game
    r = api.cmd(game_id, "restart")
    assert r["location"] == "bone-yard"
    assert r["inventory"] == []
    assert r["ending"] is None
    # State should also be reset
    state = api.state(game_id)
    assert state["location"] == "bone-yard"
    assert state["inventory"] == []
    assert state["ending"] is None
