"""Acceptance tests for T-009: Checkpoints and save/load.

Verifies AC-013: save command stores state to save_slot, load command restores from save_slot,
auto-checkpoints on entering location and before danger.

Uses only api and game fixtures, game_data.py constants, and the interfaces listed for T-009.
"""

import pytest

from game_data import TEXT, ROUTES


class TestAutoCheckpoints:
    """Verifies AC-013: auto-checkpoints on entering location and before danger."""

    def test_new_game_has_checkpoint(self, api, game):
        """Verifies: AC-013. A new game has has_checkpoint true and has_save false."""
        game_id = game["game_id"]
        s = api.state(game_id)
        assert s["has_checkpoint"] is True, "New game must have has_checkpoint true"
        assert s["has_save"] is False, "New game must have has_save false"


class TestSaveCommand:
    """Verifies AC-013: save command stores state to save_slot."""

    def test_save_sets_has_save_true(self, api, game):
        """Verifies: AC-013. save command stores state to save_slot."""
        game_id = game["game_id"]
        s = api.state(game_id)
        assert s["has_save"] is False, "Initial state must have has_save false"

        api.cmd(game_id, "save")
        s = api.state(game_id)
        assert s["has_save"] is True, "Save command must set has_save true"

    def test_save_overwrites_previous(self, api, game):
        """Verifies: AC-013. One slot: second save overwrites first."""
        game_id = game["game_id"]

        api.cmd(game_id, "save")
        api.cmd(game_id, "go north")
        api.cmd(game_id, "save")
        api.cmd(game_id, "load")

        s = api.state(game_id)
        assert s["location"] == "watchtower", "Second save should overwrite first slot"


class TestLoadCommand:
    """Verifies AC-013: load command restores from save_slot."""

    def test_load_restores_state(self, api, game):
        """Verifies: AC-013. load command restores from save_slot."""
        game_id = game["game_id"]

        api.cmd(game_id, "go north")
        api.cmd(game_id, "take lock-pick")
        api.cmd(game_id, "save")
        api.cmd(game_id, "go south")
        api.cmd(game_id, "load")

        s = api.state(game_id)
        assert s["location"] == "watchtower", "Load must restore location"
        assert "lock-pick" in s["inventory"], "Load must restore inventory"

    def test_load_without_save_changes_nothing(self, api, game):
        """Verifies: AC-013. load without a save changes nothing."""
        game_id = game["game_id"]

        initial_location = "bone-yard"
        initial_inventory = []

        api.cmd(game_id, "load")

        s = api.state(game_id)
        assert s["location"] == initial_location, "Load without save must not change location"
        assert s["inventory"] == initial_inventory, "Load without save must not change inventory"

    def test_load_preserves_has_save(self, api, game):
        """Verifies: AC-013. has_save stays true after later commands."""
        game_id = game["game_id"]

        api.cmd(game_id, "save")
        api.cmd(game_id, "go north")
        api.cmd(game_id, "go south")

        s = api.state(game_id)
        assert s["has_save"] is True, "has_save must stay true after commands"


class TestCheckpointRecovery:
    """Verifies AC-013: continue restores the last checkpoint after death."""

    def test_continue_restores_checkpoint(self, api, game):
        """Verifies: AC-013. continue restores the last checkpoint (dead false, choices [])."""
        game_id = game["game_id"]

        # Navigate to get checkpoint, then die
        responses = api.run(game_id, ["go north", "take lock-pick", "go south", "take core", "wait", "wait", "wait"])

        # Last response should be dead
        assert responses[-1]["dead"] is True, "Must be dead after dust"

        # Continue should restore the checkpoint (bone-yard with lock-pick)
        r = api.cmd(game_id, "continue")
        assert r["dead"] is False, "Continue must set dead false"
        assert r["choices"] == [], "Continue must set choices empty"
        assert r["location"] == "bone-yard", "Continue must restore location to bone-yard"
        assert "lock-pick" in r["inventory"], "Continue must restore inventory from checkpoint"
        assert "core" not in r["inventory"], "Continue must not restore core (dust kills player, core left behind)"
