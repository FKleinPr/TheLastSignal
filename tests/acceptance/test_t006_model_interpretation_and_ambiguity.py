"""Verifies AC-003: Model interpretation and ambiguity handling.

Verifies: AC-003
"""
import pytest
from game_data import TEXT, ROUTES


class TestModelInterpretation:
    """Tests for natural language interpretation via LLM and fallback rules."""

    def test_01_model_takes_take_core(self, api, game):
        """Verifies: AC-003 (model intent used)."""
        script = '{"verb": "take", "object": "core", "target": null}'
        api.script_llm([script])
        r = api.cmd(game["game_id"], "grab the humming metal")
        assert "core" in r["inventory"]

    def test_02_model_takes_go_north(self, api, game):
        """Verifies: AC-003 (direction as object)."""
        script = '{"verb": "go", "object": "north", "target": null}'
        api.script_llm([script])
        r = api.cmd(game["game_id"], "walk towards the tower")
        assert r["location"] == "watchtower"

    def test_03_rule_parser_ignores_invalid_json(self, api, game):
        """Verifies: AC-003 (invalid JSON ignored, rule-based decides)."""
        api.script_llm(["this is not json"])
        r = api.cmd(game["game_id"], "take core")
        assert "core" in r["inventory"]

    def test_04_model_cannot_add_facts(self, api, game):
        """Verifies: AC-003 (model adds no facts, rule-based decides)."""
        script = '{"verb": "take", "object": "data-slate", "target": null}'
        api.script_llm([script])
        r = api.cmd(game["game_id"], "take core")
        assert r["inventory"] == ["core"]

    def test_05_model_down_uses_rules(self, api, game):
        """Verifies: AC-003 (model down, fallback rules work)."""
        api.llm_down()
        r = api.cmd(game["game_id"], "take core")
        assert "core" in r["inventory"]

    def test_06_llm_requests_recorded(self, api, game):
        """Verifies: AC-003 (requests logged)."""
        api.cmd(game["game_id"], "look around please")
        requests = api.llm_requests()
        assert len(requests) > 0
        last = requests[-1]
        assert "messages" in last
        assert any("look around please" in m["content"] for m in last["messages"])

    def test_07_ambiguity_no_state_change(self, api, game):
        """Verifies: AC-003 (ambiguity lists options, no state change)."""
        # Move to scrap-market first
        api.run(game["game_id"], ROUTES["to_scrap_market"])
        
        # Get state before ambiguous command
        state_before = api.state(game["game_id"])
        
        # Send ambiguous command
        r = api.cmd(game["game_id"], "talk to local")
        
        # Verify text contains ambiguity info
        assert TEXT["ambiguous"] in r["text"]
        assert "merchant-jex" in r["text"]
        assert "child-echo" in r["text"]
        
        # Verify state unchanged
        state_after = api.state(game["game_id"])
        assert state_after["location"] == state_before["location"]
        assert state_after["inventory"] == state_before["inventory"]
        assert state_after["flags"] == state_before["flags"]
        assert state_after["clues"] == state_before["clues"]
        assert state_after["relationships"] == state_before["relationships"]

    def test_08_unknown_command_fallback(self, api, game):
        """Verifies: AC-003 (unknown command, no state change)."""
        r = api.cmd(game["game_id"], "sing loudly to the sand")
        assert r["text"].startswith(TEXT["unknown"])
        assert r["location"] == "bone-yard"  # No movement
        assert r["inventory"] == []  # No items taken
