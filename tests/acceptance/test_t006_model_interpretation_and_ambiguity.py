"""Verifies AC-003, AC-022, AC-023, AC-026, AC-027, AC-028, AC-029: Model interpretation and ambiguity handling.

Verifies: AC-003 (model intent used, fallback rules), AC-022 (request includes verbs/names), AC-023 (Markdown fence, scripted responses), AC-026 (exits and valid JSON in request), AC-027 (go mapping), AC-028 (take mapping), AC-029 (fallback unknown).

CR-003 updates:
- Added checks for `EXPECTED_EXITS` (exit north -> watchtower) and `EXPECTED_JSON_STRUCTURE` ("verb") in the system message.
- Added tests for `go` mapping (location ID to direction) and `take` mapping (name to ID).
- Added test for fallback when model names non-existent entity.
- Updated existing tests to verify system message content (exits, JSON example).
"""
import pytest
from game_data import (
    TEXT, ROUTES, MODEL_VERBS_TO_CHECK, MODEL_ENTITY_ID_TO_CHECK,
    EXPECTED_EXITS, EXPECTED_JSON_STRUCTURE
)


class TestModelInterpretation:
    """Tests for natural language interpretation via LLM and fallback rules."""

    def test_01_model_takes_core_with_system_message_exits(self, api, game):
        """Verifies: AC-003, AC-022, AC-026 (model takes core, system message contains exits)."""
        # Script the stub model to accept "grab the humming metal" -> take core
        script = '{"verb": "take", "object": "core", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "grab the humming metal")
        assert "core" in r["inventory"], "Core should be in inventory"

        # Verify request was sent to stub
        requests = api.llm_requests()
        assert len(requests) > 0
        
        # Verify request contains expected verbs/names (AC-022)
        last_request = requests[-1]
        assert "messages" in last_request
        content = " ".join([m["content"] for m in last_request["messages"]])
        
        for verb in MODEL_VERBS_TO_CHECK:
            assert verb in content, f"Verb {verb} not in request"
        assert MODEL_ENTITY_ID_TO_CHECK in content, f"Entity ID {MODEL_ENTITY_ID_TO_CHECK} not in request"
        
        # Verify request contains exits (AC-026)
        for expected_exit in EXPECTED_EXITS:
            assert expected_exit in content, f"Expected exit {expected_exit} not in request"

    def test_02_model_maps_go_location_to_direction(self, api, game):
        """Verifies: AC-027 (go maps location ID to direction)."""
        # Script the stub model to accept "head over to the market" -> go scrap-market
        script = '{"verb": "go", "object": "scrap-market", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "head over to the market")
        assert r["location"] == "scrap-market", f"Expected location scrap-market, got {r['location']}"

    def test_03_model_maps_take_name_to_id(self, api, game):
        """Verifies: AC-028 (take maps name 'metal' to ID 'core')."""
        # Script the stub model to accept "snatch it" -> take core (object: metal)
        script = '{"verb": "take", "object": "metal", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "snatch it")
        assert "core" in r["inventory"], f"Expected core in inventory, got {r['inventory']}"

    def test_04_fallback_when_unknown_entity(self, api, game):
        """Verifies: AC-029 (fallback when model names non-existent entity)."""
        # Script the stub model to accept "snatch it" -> take "shiny thing" (not present)
        script = '{"verb": "take", "object": "shiny thing", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "snatch it")
        assert "core" not in r["inventory"], "Inventory should be empty"
        assert TEXT["unknown"] in r["text"], f"Expected unknown text, got {r['text']}"

    def test_05_invalid_json_ignored(self, api, game):
        """Verifies: AC-003 (invalid JSON ignored, rule-based decides)."""
        api.script_llm(["this is not json"])
        r = api.cmd(game["game_id"], "take core")
        assert "core" in r["inventory"], "Core should be taken by rule-based parser"
        # Verify request still made to stub (even if response invalid)
        requests = api.llm_requests()
        assert len(requests) > 0

    def test_06_model_cannot_add_facts(self, api, game):
        """Verifies: AC-003 (model adds no facts, rule-based decides)."""
        script = '{"verb": "take", "object": "data-slate", "target": null}'
        api.script_llm([script])
        r = api.cmd(game["game_id"], "take core")
        assert r["inventory"] == ["core"], f"Expected only core in inventory, got {r['inventory']}"

    def test_07_model_down_uses_rules(self, api, game):
        """Verifies: AC-003 (model down, fallback rules work)."""
        api.llm_down()
        r = api.cmd(game["game_id"], "take core")
        assert "core" in r["inventory"], "Core should be taken when model is down"

    def test_08_markdown_fence_stripping(self, api, game):
        """Verifies: AC-023 (Markdown code fence accepted and stripped)."""
        script = "```json\n{\"verb\": \"take\", \"object\": \"core\", \"target\": null}\n```"
        api.script_llm([script])
        r = api.cmd(game["game_id"], "grab the humming metal")
        assert "core" in r["inventory"], "Core should be taken after Markdown stripping"

    def test_09_ambiguity_no_state_change(self, api, game):
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

    def test_10_unknown_command_fallback(self, api, game):
        """Verifies: AC-003 (unknown command, no state change)."""
        r = api.cmd(game["game_id"], "sing loudly to the sand")
        assert r["text"].startswith(TEXT["unknown"])
        assert r["location"] == "bone-yard", "No movement on unknown command"
        assert r["inventory"] == [], "No items taken on unknown command"

    def test_11_system_message_contains_valid_json_example(self, api, game):
        """Verifies: AC-026 (system message contains valid JSON example with double quotes)."""
        r = api.cmd(game["game_id"], "take core")
        requests = api.llm_requests()
        assert len(requests) > 0
        
        last_request = requests[-1]
        assert "messages" in last_request
        
        # System message is usually the first message in the list
        system_message = next((m for m in last_request["messages"] if m["role"] == "system"), None)
        assert system_message is not None, "System message not found in request"
        
        content = system_message["content"]
        # Check for double quotes in JSON example (AC-026)
        assert EXPECTED_JSON_STRUCTURE in content, f"Expected JSON structure '{EXPECTED_JSON_STRUCTURE}' not in system message"
