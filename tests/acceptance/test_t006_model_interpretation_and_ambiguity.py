"""Verifies AC-003, AC-022, AC-023: Model interpretation and ambiguity handling.

Verifies: AC-003 (model intent used, fallback rules), AC-022 (request includes verbs/names), AC-023 (Markdown fence, scripted responses).
"""
import pytest
from game_data import TEXT, ROUTES, MODEL_VERBS_TO_CHECK, MODEL_ENTITY_ID_TO_CHECK


class TestModelInterpretation:
    """Tests for natural language interpretation via LLM and fallback rules."""

    def test_01_model_takes_take_core(self, api, game):
        """Verifies: AC-003 (model intent used)."""
        # Script the stub model to accept the sentence "grab the humming metal" -> take core
        script = '{"verb": "take", "object": "core", "target": null}'
        api.script_llm([script])
        r = api.cmd(game["game_id"], "grab the humming metal")
        assert "core" in r["inventory"]
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

    def test_02_model_takes_go_north(self, api, game):
        """Verifies: AC-003 (direction as object)."""
        script = '{"verb": "go", "object": "north", "target": null}'
        api.script_llm([script])
        r = api.cmd(game["game_id"], "walk towards the tower")
        assert r["location"] == "watchtower"
        # Verify request context
        requests = api.llm_requests()
        last_request = requests[-1]
        assert "messages" in last_request
        content = " ".join([m["content"] for m in last_request["messages"]])
        assert "go" in content

    def test_03_rule_parser_ignores_invalid_json(self, api, game):
        """Verifies: AC-003 (invalid JSON ignored, rule-based decides)."""
        api.script_llm(["this is not json"])
        r = api.cmd(game["game_id"], "take core")
        assert "core" in r["inventory"]
        # Verify request still made to stub (even if response invalid)
        requests = api.llm_requests()
        assert len(requests) > 0

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

    def test_06_markdown_fence_stripping(self, api, game):
        """Verifies: AC-023 (Markdown code fence accepted and stripped)."""
        script = "```json\n{\"verb\": \"take\", \"object\": \"core\", \"target\": null}\n```"
        api.script_llm([script])
        r = api.cmd(game["game_id"], "grab the humming metal")
        assert "core" in r["inventory"]

    def test_07_llm_requests_recorded(self, api, game):
        """Verifies: AC-022 (requests logged with verbs and names)."""
        r = api.cmd(game["game_id"], "take core")
        requests = api.llm_requests()
        assert len(requests) > 0
        last = requests[-1]
        assert "messages" in last
        content = " ".join([m["content"] for m in last["messages"]])
        for verb in MODEL_VERBS_TO_CHECK:
            assert verb in content, f"Verb {verb} missing from request"
        assert MODEL_ENTITY_ID_TO_CHECK in content, f"Entity ID {MODEL_ENTITY_ID_TO_CHECK} missing from request"

    def test_08_ambiguity_no_state_change(self, api, game):
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

    def test_09_unknown_command_fallback(self, api, game):
        """Verifies: AC-003 (unknown command, no state change)."""
        r = api.cmd(game["game_id"], "sing loudly to the sand")
        assert r["text"].startswith(TEXT["unknown"])
        assert r["location"] == "bone-yard"  # No movement
        assert r["inventory"] == []  # No items taken
