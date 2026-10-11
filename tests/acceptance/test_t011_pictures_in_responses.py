"""Acceptance tests for pictures in responses (T-011).

Verifies AC-008 and AC-010: responses include image or placeholder based on availability; game playable without
Pixel-Art Generator.

Uses only: api, game, game_data constants, and the allowed interfaces for this task.
"""
import pytest
from game_data import PICTURES, ROUTES, TEXT, placeholder


class TestPicturesInResponses:
    """Tests for picture inclusion in every Response."""

    def test_ac008_new_game_has_bone_yard_entry(self, game, api):
        """Verifies: AC-008. New game response includes bone-yard entry with correct metadata and no image."""
        r = game["response"]
        assert r["location"] == "bone-yard"
        pictures = r["pictures"]
        assert len(pictures) == 1
        entry = pictures[0]
        assert entry["name"] == "bone-yard"
        assert entry["type"] == "scene"
        assert entry["size"] == "160x90"
        assert entry["available"] is False
        assert entry["terminal"] is None
        assert entry["placeholder"] == placeholder("bone-yard")

    def test_ac008_set_pictures_makes_entry_available(self, game, api):
        """Verifies: AC-008. Setting a picture for watchtower makes that entry available with terminal text."""
        api.set_pictures({"watchtower": "WATCHTOWER-ART"})
        r = api.cmd(game["game_id"], "go north")
        pictures = r["pictures"]
        # Find the watchtower entry
        watchtower_entry = None
        for p in pictures:
            if p["name"] == "watchtower":
                watchtower_entry = p
                break
        assert watchtower_entry is not None
        assert watchtower_entry["available"] is True
        assert watchtower_entry["terminal"] == "WATCHTOWER-ART"
        assert watchtower_entry["placeholder"] is None

    def test_ac008_character_present_has_entry(self, game, api):
        """Verifies: AC-008. Moving to sanctum includes an entry for priest-voa who is present there."""
        # Move to sanctum (sanctum is reached via: north, east, south)
        # Note: sanctum east is blocked until gate-locked is solved, but we can enter from south.
        # Route: bone-yard -> watchtower (north) -> archives (east) -> sanctum (south)
        api.run(game["game_id"], ["go north", "go east", "go south"])
        r = api.cmd(game["game_id"], "look")
        pictures = r["pictures"]
        # Find priest-voa entry
        priest_entry = None
        for p in pictures:
            if p["name"] == "priest-voa":
                priest_entry = p
                break
        assert priest_entry is not None
        assert priest_entry["type"] == "character"
        assert "priest-voa" in priest_entry["name"]

    def test_ac008_take_item_has_entry(self, game, api):
        """Verifies: AC-008. Taking the core adds an entry for the core item."""
        r = api.cmd(game["game_id"], "take core")
        pictures = r["pictures"]
        core_entry = None
        for p in pictures:
            if p["name"] == "core":
                core_entry = p
                break
        assert core_entry is not None
        assert core_entry["type"] == "item"

    def test_ac010_generator_down_still_playable(self, game, api):
        """Verifies: AC-010. When generator is down, game is playable and all entries have placeholders."""
        api.generator_down()
        # Move to watchtower
        r = api.cmd(game["game_id"], "go north")
        assert r["location"] == "watchtower"
        pictures = r["pictures"]
        for p in pictures:
            assert p["available"] is False
            assert p["terminal"] is None
            assert p["placeholder"] == placeholder(p["name"])

    def test_ac010_gameplay_continues_without_generator(self, game, api):
        """Verifies: AC-010. Game continues to work with commands even when generator is down."""
        api.generator_down()
        # Attempt a sequence that would normally require pictures
        r = api.cmd(game["game_id"], "go north")
        assert r["location"] == "watchtower"
        # Try talking to a character in another location
        r = api.cmd(game["game_id"], "go east")
        r = api.cmd(game["game_id"], "go south")
        r = api.cmd(game["game_id"], "talk to priest-voa")
        assert TEXT["priest_always"] in r["text"]

    def test_ac008_scrap_market_entries_have_placeholders(self, game, api):
        """Verifies: AC-008. After moving to scrap-market, all entries (location, characters) have placeholders."""
        # Move to scrap-market: bone-yard -> east -> scrap-market
        api.run(game["game_id"], ["go east"])
        r = api.cmd(game["game_id"], "look")
        pictures = r["pictures"]
        # Should have entries for scrap-market, merchant-jex, child-echo
        names = [p["name"] for p in pictures]
        assert "scrap-market" in names
        assert "merchant-jex" in names
        assert "child-echo" in names
        for p in pictures:
            assert p["available"] is False
            assert p["terminal"] is None
            assert p["placeholder"] == placeholder(p["name"])
