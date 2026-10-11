"""Tests for signal event, timers and death (T-008).

Verifies AC-005 (signal event in first location with flags set) and AC-007 (death with choices, continue/restart).
"""

import pytest

from game_data import TEXT, ROUTES, DEAD_CHOICES


def test_t008_01_signal_event_sets_flags(api, game):
    """Verifies: AC-005 - Signal event triggers when core picked up, sets flags dust-active and core."""
    game_id = game["game_id"]
    r = api.cmd(game_id, "take core")
    
    assert TEXT["signal"] in r["text"]
    assert "core" in r["inventory"]
    assert "core" in api.state(game_id)["flags"]
    assert "dust-active" in api.state(game_id)["flags"]


def test_t008_02_death_dust_warning_and_death(api, game):
    """Verifies: AC-007 - Death-dust warning on turn 2, death on turn 3."""
    game_id = game["game_id"]
    responses = api.run(game_id, ROUTES["death_dust"])
    
    assert TEXT["dust_warning"] in responses[-2]["text"]
    assert responses[-2]["dead"] is False
    assert responses[-1]["dead"] is True
    assert DEAD_CHOICES == responses[-1]["choices"]
    assert TEXT["dust_death"] in responses[-1]["text"]


def test_t008_03_no_death_without_core(api, game):
    """Verifies: AC-007 - No death-dust if core not picked up."""
    game_id = game["game_id"]
    responses = api.run(game_id, ["wait", "wait", "wait"])
    
    for r in responses:
        assert r["dead"] is False
        assert TEXT["dust_warning"] not in r["text"]


def test_t008_04_leave_bone_yard_avoids_death(api, game):
    """Verifies: AC-007 - Leaving bone-yard avoids death-dust (replaced per review)."""
    game_id = game["game_id"]
    responses = api.run(game_id, ["take core", "go north", "wait", "wait", "wait"])
    
    for r in responses:
        assert r["dead"] is False
    
    assert responses[-1]["location"] == "watchtower"


def test_t008_05_death_remains_dead_with_choices(api, game):
    """Verifies: AC-007 - While dead, other commands keep dead true with continue/restart choices."""
    game_id = game["game_id"]
    api.run(game_id, ROUTES["death_dust"])
    r = api.cmd(game_id, "go north")
    
    assert r["dead"] is True
    assert DEAD_CHOICES == r["choices"]
    assert "continue" in r["text"].lower()
    assert "restart" in r["text"].lower()


def test_t008_06_continue_restores_checkpoint(api, game):
    """Verifies: AC-007 - continue from checkpoint restores dead=false, choices=[]."""
    game_id = game["game_id"]
    api.run(game_id, ROUTES["death_dust"])
    r = api.cmd(game_id, "continue")
    
    assert r["dead"] is False
    assert r["choices"] == []
    assert r["location"] == "bone-yard"
    assert "core" not in r["inventory"]


def test_t008_07_restart_resets_game(api, game):
    """Verifies: AC-007 - restart starts Act I again (bone-yard, inventory [], flags [], dead false)."""
    game_id = game["game_id"]
    api.run(game_id, ROUTES["death_dust"])
    r = api.cmd(game_id, "restart")
    
    assert r["dead"] is False
    assert r["location"] == "bone-yard"
    assert r["inventory"] == []
    assert api.state(game_id)["flags"] == []


def test_t008_08_state_dead_true_after_death(api, game):
    """Verifies: AC-007 - State dead is true after death, false after continue."""
    game_id = game["game_id"]
    api.run(game_id, ROUTES["death_dust"])
    
    state = api.state(game_id)
    assert state["dead"] is True
    
    api.cmd(game_id, "continue")
    state = api.state(game_id)
    assert state["dead"] is False
