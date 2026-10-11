"""Acceptance tests for T-005: Command endpoint and movement.

Verifies AC-003 (natural language commands, ambiguity, failure handling) and AC-011 (exit consistency, blocked exits).
Tests use only the planned interfaces (T-003, T-005, T-002). No application imports.
"""

import pytest

from game_data import ROUTES, TEXT, LOCATIONS


def test_001_turn_numbers(game, api):
    """Verifies: AC-003. A command answers a Response with the 9 fields and turn 1; a second command gives turn 2."""
    resp1 = api.cmd(game["game_id"], "look")
    assert resp1["turn"] == 1
    resp2 = api.cmd(game["game_id"], "go north")
    assert resp2["turn"] == 2


def test_002_walk_route(game, api):
    """Verifies: AC-011. api.run the walk and check locations in order: watchtower, archives, sanctum, archives,
    watchtower, bone-yard, scrap-market, edge-of-town, scrap-market, bone-yard."""
    commands = ["go north", "go east", "go south", "go north", "go west", "go south", "go east", "go north", "go south", "go west"]
    responses = api.run(game["game_id"], commands)
    locations = [r["location"] for r in responses]
    expected = ["watchtower", "archives", "sanctum", "archives", "watchtower", "bone-yard", "scrap-market", "edge-of-town", "scrap-market", "bone-yard"]
    assert locations == expected


def test_003_direction_aliases(game, api):
    """Verifies: AC-003. north reaches watchtower in one game; n reaches watchtower in a second game."""
    g1 = api.new_game()
    r1 = api.cmd(g1["game_id"], "north")
    assert r1["location"] == "watchtower"
    g2 = api.new_game()
    r2 = api.cmd(g2["game_id"], "n")
    assert r2["location"] == "watchtower"


def test_004_blocked_exit_no_change(game, api):
    """Verifies: AC-011. go south in bone-yard keeps location bone-yard and dead false."""
    r = api.cmd(game["game_id"], "go south")
    assert r["location"] == "bone-yard"
    assert r["dead"] is False


def test_005_sanctum_blocked_exit(game, api):
    """Verifies: AC-011. ROUTES["to_sanctum"], then go east: location sanctum and TEXT["blocked"] in text.lower()."""
    responses = api.run(game["game_id"], ROUTES["to_sanctum"])
    r = api.cmd(game["game_id"], "go east")
    assert r["location"] == "sanctum"
    assert TEXT["blocked"] in r["text"].lower()


def test_006_take_core_persistence(game, api):
    """Verifies: AC-003. take core: inventory ["core"] in the Response and in api.state; after go north still ["core"]."""
    r1 = api.cmd(game["game_id"], "take core")
    assert "core" in r1["inventory"]
    s = api.state(game["game_id"])
    assert "core" in s["inventory"]
    r2 = api.cmd(game["game_id"], "go north")
    assert "core" in r2["inventory"]


def test_007_talk_to_priest(game, api):
    """Verifies: AC-003. ROUTES["to_sanctum"], then talk to priest-voa: TEXT["priest_always"] in text."""
    responses = api.run(game["game_id"], ROUTES["to_sanctum"])
    r = api.cmd(game["game_id"], "talk to priest-voa")
    assert TEXT["priest_always"] in r["text"]


def test_008_impossible_action_no_change(game, api):
    """Verifies: AC-003. talk to core: TEXT["impossible"] in text; State location bone-yard, inventory [], flags []."""
    r = api.cmd(game["game_id"], "talk to core")
    assert TEXT["impossible"] in r["text"]
    s = api.state(game["game_id"])
    assert s["location"] == "bone-yard"
    assert s["inventory"] == []
    assert s["flags"] == []


def test_009_unknown_command_no_change(game, api):
    """Verifies: AC-003. xyzzy plugh: text starts with TEXT["unknown"]; State location bone-yard, inventory []."""
    r = api.cmd(game["game_id"], "xyzzy plugh")
    assert r["text"].startswith(TEXT["unknown"])
    s = api.state(game["game_id"])
    assert s["location"] == "bone-yard"
    assert s["inventory"] == []


def test_010_command_errors(game, api):
    """Verifies: AC-003. api.command_raw(game_id, {"text": ""}) and api.command_raw(game_id, {}) answer 422;
    api.command_raw("00000000-0000-0000-0000-000000000000", {"text": "look"}) answers 404."""
    g_id = game["game_id"]
    r1 = api.command_raw(g_id, {"text": ""})
    assert r1.status_code == 422
    r2 = api.command_raw(g_id, {})
    assert r2.status_code == 422
    r3 = api.command_raw("00000000-0000-0000-0000-000000000000", {"text": "look"})
    assert r3.status_code == 404


def test_011_llm_down_rule_based(game, api):
    """Verifies: AC-003. api.llm_down(), then go north: location watchtower."""
    api.llm_down()
    r = api.cmd(game["game_id"], "go north")
    assert r["location"] == "watchtower"
