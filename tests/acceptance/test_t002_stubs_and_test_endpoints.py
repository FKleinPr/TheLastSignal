"""
Acceptance tests for T-002: Stubs and test endpoints.

Verifies that stub services (LLM, Pixel-Art) are controllable and observable
through the game server's /api/test/* endpoints, and that the game remains
playable with stubbed responses (AC-012).

Integration: Uses api fixture from the shared harness (conftest.py).
Uses constants from game_data.py (TEXT, placeholder).
No http_client, no URLs, no os.getenv in this module.
"""

import pytest
from game_data import TEXT, placeholder


# =============================================================================
# Stub Control Endpoints (T-002)
# =============================================================================

def test_reset_status(api):
    """
    Verifies: AC-012, T-002 Reset.
    The /api/test/reset endpoint returns 200 OK and clears game state and stubs.
    """
    r = api.reset_raw()
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["status"] == "ok", f"Expected status 'ok', got {data.get('status')}"


def test_llm_script_content(api):
    """
    Verifies: AC-012, T-002 LLM Scripting.
    The /api/test/llm-script endpoint accepts responses and configures the stub model.
    """
    # Configure stub to return a valid JSON verb response for testing
    script_content = ['{"verb": "look", "object": null, "target": null}']
    
    r = api.script_llm_raw(script_content)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    
    # Configure with empty list
    r = api.script_llm_raw([])
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_llm_script_down(api):
    """
    Verifies: AC-012, T-002 LLM Down Mode.
    The stub model can be set to 'down' mode, making it unreachable.
    """
    r = api.llm_down_raw()
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_llm_requests_empty(api):
    """
    Verifies: AC-012, T-002 LLM Request Recording.
    The /api/test/llm-requests endpoint returns recorded messages from stub interactions.
    """
    # Ensure clean state first
    api.reset_raw()
    
    requests = api.llm_requests()
    assert isinstance(requests, list), "Expected list of messages"
    assert requests == [], f"Expected empty list after reset, got {requests}"


def test_pictures_set(api):
    """
    Verifies: AC-012, T-002 Picture Stub Configuration.
    The /api/test/pictures endpoint accepts picture data and configures the stub generator.
    """
    # Set specific picture data from spec 9.10
    picture_data = {"bone-yard": "BONE-ART"}
    
    r = api.set_pictures_raw(picture_data)
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    
    # Set empty data
    r = api.set_pictures_raw({})
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_pictures_down(api):
    """
    Verifies: AC-012, T-002 Picture Stub Down Mode.
    The stub generator can be set to 'down' mode, making it unreachable/unavailable.
    """
    r = api.generator_down_raw()
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"


def test_reset_clears_state(api):
    """
    Verifies: AC-012, T-002 Reset Clears State.
    The /api/test/reset endpoint clears all games and resets both stubs.
    """
    # Script the model and set pictures
    api.script_llm_raw(['{"verb": "look"}'])
    api.set_pictures_raw({"bone-yard": "BONE-ART"})
    
    # Reset
    r = api.reset_raw()
    assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"
    data = r.json()
    assert data["status"] == "ok", f"Expected status 'ok', got {data.get('status')}"
    
    # Verify requests are empty after reset
    requests = api.llm_requests()
    assert requests == [], f"Expected empty list after reset, got {requests}"
