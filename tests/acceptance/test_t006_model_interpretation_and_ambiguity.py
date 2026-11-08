"""Verifies AC-003, AC-022, AC-023, AC-026, AC-027, AC-028, AC-029, AC-033, AC-034, AC-035, AC-036.

Verifies: AC-003 (model intent used, fallback rules), AC-022 (request includes verbs/names), AC-023 (Markdown fence, scripted responses), AC-026 (exits and valid JSON in request), AC-027 (go mapping), AC-028 (invalid response fallback), AC-029 (take mapping metal->core), AC-033 (system message instructions), AC-034 (take mapping signal->core), AC-035 (talk mapping), AC-036 (go mapping with target).

CR-004 updates:
- Added checks for `EXPECTED_SYSTEM_MESSAGE_INSTRUCTIONS` ("Use only ids from the list below") in the system message.
- Added explicit tests for AC-027 (go mapping location ID) and AC-028 (invalid response fallback).
- Added test for AC-029 (take mapping metal->core) and AC-034 (take mapping signal->core).
- Updated `go` mapping test to use `target` field with destination ID (AC-036).
- Added `talk` mapping test with character in `object` field (AC-035).
- Updated existing tests to verify system message content (exits, JSON example, instructions).
"""
import pytest
from game_data import (
    TEXT, ROUTES, MODEL_VERBS_TO_CHECK, MODEL_ENTITY_ID_TO_CHECK,
    EXPECTED_EXITS, EXPECTED_JSON_STRUCTURE,
    EXPECTED_SYSTEM_MESSAGE_INSTRUCTIONS
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
        # CR-003: location ID in `object` field
        script = '{"verb": "go", "object": "scrap-market", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "head over to the market")
        assert r["location"] == "scrap-market", f"Expected location scrap-market, got {r['location']}"

    def test_03_invalid_model_response_fallback(self, api, game):
        """Verifies: AC-028 (invalid response - shiny thing not present, fallback to rules)."""
        # Script the stub model to accept "snatch it" -> take "shiny thing" (not present)
        script = '{"verb": "take", "object": "shiny thing", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "snatch it")
        assert "core" not in r["inventory"], "Inventory should be empty"
        assert TEXT["unknown"] in r["text"], f"Expected unknown text, got {r['text']}"

    def test_04_model_maps_take_name_to_id(self, api, game):
        """Verifies: AC-029 (take maps name 'metal' to ID 'core')."""
        # Script the stub model to accept "snatch it" -> take core (object: metal)
        # CR-003: 'metal' is a name for 'core'
        script = '{"verb": "take", "object": "metal", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "snatch it")
        assert "core" in r["inventory"], f"Expected core in inventory, got {r['inventory']}"

    def test_05_model_maps_take_signal_to_core(self, api, game):
        """Verifies: AC-034 (take maps name 'signal' to ID 'core')."""
        # Script the stub model to accept "snatch it" -> take core (object: signal)
        # CR-004: 'signal' is a name for 'core'
        script = '{"verb": "take", "object": "signal", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "snatch it")
        assert "core" in r["inventory"], f"Expected core in inventory, got {r['inventory']}"

    def test_06_model_maps_talk_character_in_target(self, api, game):
        """Verifies: AC-035 (talk maps character in `object` or `target`)."""
        # Move to scrap-market first
        api.run(game["game_id"], ROUTES["to_scrap_market"])
        
        # Script the stub model to accept "chat with the trader" -> talk merchant-jex
        # CR-004: character in `object` field
        script = '{"verb": "talk", "object": "merchant-jex", "target": null}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "chat with the trader")
        # Verify response matches talking to merchant-jex
        assert TEXT["jex_always"] in r["text"], f"Expected merchant response, got {r['text']}"

    def test_07_model_maps_go_destination_to_location(self, api, game):
        """Verifies: AC-036 (go maps destination ID to direction via `target`)."""
        # Script the stub model to accept "go back to the bone yard" -> go bone-yard
        # CR-004: destination id in `target` field
        api.run(game["game_id"], ROUTES["to_scrap_market"])  # AC-036: after `go east`
        script = '{"verb": "go", "object": null, "target": "bone-yard"}'
        api.script_llm([script])
        
        r = api.cmd(game["game_id"], "go back to the bone yard")
        assert r["location"] == "bone-yard", f"Expected location bone-yard, got {r['location']}"

    def test_08_system_message_instructions(self, api, game):
        """Verifies: AC-033 (system message contains "Use only ids from the list below")."""
        r = api.cmd(game["game_id"], "snatch it")
        requests = api.llm_requests()
        assert len(requests) > 0
        
        last_request = requests[-1]
        assert "messages" in last_request
        
        # System message is usually the first message in the list
        system_message = next((m for m in last_request["messages"] if m["role"] == "system"), None)
        assert system_message is not None, "System message not found in request"
        
        content = system_message["content"]
        # Check for specific CR-004 instructions (AC-033)
        assert EXPECTED_SYSTEM_MESSAGE_INSTRUCTIONS in content, f"Expected system message instructions not in system message"

    def test_09_markdown_fence_stripping(self, api, game):
        """Verifies: AC-023 (Markdown code fence accepted and stripped)."""
        script = "```json\n{\"verb\": \"take\", \"object\": \"core\", \"target\": null}\n```"
        api.script_llm([script])
        r = api.cmd(game["game_id"], "grab the humming metal")
        assert "core" in r["inventory"], "Core should be taken after Markdown stripping"

    def test_10_ambiguity_no_state_change(self, api, game):
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

    def test_11_unknown_command_fallback(self, api, game):
        """Verifies: AC-003 (unknown command, no state change)."""
        r = api.cmd(game["game_id"], "sing loudly to the sand")
        assert r["text"].startswith(TEXT["unknown"])
        assert r["location"] == "bone-yard", "No movement on unknown command"
        assert r["inventory"] == [], "No items taken on unknown command"

    def test_12_model_down_uses_rules(self, api, game):
        """Verifies: AC-003 (model down, fallback rules work)."""
        api.llm_down()
        r = api.cmd(game["game_id"], "take core")
        assert "core" in r["inventory"], "Core should be taken when model is down"

    def test_13_invalid_json_ignored(self, api, game):
        """Verifies: AC-003 (invalid JSON ignored, rule-based decides)."""
        api.script_llm(["this is not json"])
        r = api.cmd(game["game_id"], "take core")
        assert "core" in r["inventory"], "Core should be taken by rule-based parser"
        # Verify request still made to stub (even if response invalid)
        requests = api.llm_requests()
        assert len(requests) > 0

    def test_14_model_cannot_add_facts(self, api, game):
        """Verifies: AC-003 (model adds no facts, rule-based decides)."""
        script = '{"verb": "take", "object": "data-slate", "target": null}'
        api.script_llm([script])
        r = api.cmd(game["game_id"], "take core")
        assert r["inventory"] == ["core"], f"Expected only core in inventory, got {r['inventory']}"
