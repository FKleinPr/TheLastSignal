"""Acceptance tests for T-007: Characters, objects and clues.

Verifies AC-004 (entities exist) and AC-005 (3+ clues, optional clue, relationships).
Tests use only the planned interfaces: api, game, api.cmd, api.run, api.state.
Game facts are imported from game_data; no application imports.
"""
import pytest

from game_data import (
    TEXT, ROUTES, DEAD_CHOICES,
)


def test_t007_01_talk_to_child_always(api, game):
    """Verifies: AC-005 (clue-character, character dialogue)."""
    g_id = game["game_id"]
    api.run(g_id, ROUTES["to_scrap_market"])
    resp = api.cmd(g_id, "talk to child-echo")
    assert TEXT["child_always"] in resp["text"]
    st = api.state(g_id)
    assert "clue-character" in st["clues"]


def test_t007_02_talk_to_child_with_core(api, game):
    """Verifies: AC-005 (conditional dialogue when player has core)."""
    g_id = game["game_id"]
    api.run(g_id, ["take core"] + ROUTES["to_scrap_market"])
    resp = api.cmd(g_id, "talk to child-echo")
    assert TEXT["child_core"] in resp["text"]


def test_t007_03_look_clue_location(api, game):
    """Verifies: AC-005 (clue-location discoverable from start)."""
    g_id = game["game_id"]
    api.cmd(g_id, "look")
    st = api.state(g_id)
    assert "clue-location" in st["clues"]


def test_t007_04_take_data_slate_clue_object(api, game):
    """Verifies: AC-005 (clue-object discoverable via object interaction)."""
    g_id = game["game_id"]
    api.run(g_id, ROUTES["to_archives"])
    resp = api.cmd(g_id, "take data-slate")
    st = api.state(g_id)
    assert "data-slate" in st["inventory"]
    assert "clue-object" in st["clues"]


def test_t007_05_optional_clue_not_discovered(api, game):
    """Verifies: AC-005 (clue-object is optional and not present if not taken)."""
    g_id = game["game_id"]
    api.run(g_id, ROUTES["to_archives"])
    api.cmd(g_id, "go west")  # Leave archives without taking slate
    st = api.state(g_id)
    assert "clue-object" not in st["clues"]


def test_t007_06_talk_to_all_characters(api, game):
    """Verifies: AC-004 (4-6 talkable characters exist and speak)."""
    g_id = game["game_id"]
    api.run(g_id, ROUTES["to_sanctum"])
    priest_resp = api.cmd(g_id, "talk to priest-voa")

    g2 = api.new_game()
    g2_id = g2["game_id"]
    api.run(g2_id, ROUTES["to_scrap_market"])
    jex_resp = api.cmd(g2_id, "talk to merchant-jex")

    g3 = api.new_game()
    g3_id = g3["game_id"]
    api.run(g3_id, ROUTES["to_archives"])
    lira_resp = api.cmd(g3_id, "talk to archivist-lira")

    assert TEXT["priest_always"] in priest_resp["text"]
    assert TEXT["jex_always"] in jex_resp["text"]
    assert TEXT["lira_always"] in lira_resp["text"]


def test_t007_07_talk_to_archivist_with_core(api, game):
    """Verifies: AC-005 (conditional dialogue with Archivist when holding core)."""
    g_id = game["game_id"]
    api.run(g_id, ["take core"] + ROUTES["to_archives"])
    resp = api.cmd(g_id, "talk to archivist-lira")
    assert TEXT["lira_core"] in resp["text"]


def test_t007_08_talk_to_priest_with_core(api, game):
    """Verifies: AC-005 (conditional dialogue with Priest when holding core)."""
    g_id = game["game_id"]
    api.run(g_id, ["take core"] + ROUTES["to_sanctum"])
    resp = api.cmd(g_id, "talk to priest-voa")
    assert TEXT["priest_core"] in resp["text"]


def test_t007_09_trade_core_for_coolant(api, game):
    """Verifies: AC-004/AC-005 (trade mechanic: show core to get coolant-bottle)."""
    g_id = game["game_id"]
    api.run(g_id, ["take core"] + ROUTES["to_sanctum"])
    resp = api.cmd(g_id, "show core to priest-voa")
    st = api.state(g_id)
    assert "core" in st["inventory"]
    assert "coolant-bottle" in st["inventory"]
