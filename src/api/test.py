"""Test endpoints for The Last Signal game server.

Controls stub services (LLM, Pixel-Art Generator) through the game server's /api/test/* endpoints.
Also manages game state reset.

Integration: Uses httpx to talk to stub services (stub-llm:8001, stub-generator:8002).
"""

from fastapi import APIRouter, HTTPException
import httpx

router = APIRouter()

_games_store = None  # Will be set by main.py


def set_games_store(games: dict):
    """Set the games store reference so this router can clear it."""
    global _games_store
    _games_store = games


@router.post("/api/test/reset")
def reset_test():
    """Reset all games and stub services.

    Clears the games dict and calls stub control endpoints to reset stub state.
    """
    global _games_store
    if _games_store is None:
        raise HTTPException(status_code=500, detail="Games store not initialized")
    
    _games_store.clear()
    
    # Reset stub services
    try:
        with httpx.Client(timeout=5.0) as client:
            # Reset LLM stub
            client.post("http://stub-llm:8001/control/reset")
            # Reset Generator stub
            client.post("http://stub-generator:8002/control/reset")
    except Exception:
        pass  # Stub services might be down, that's okay
    
    return {"status": "ok"}


@router.post("/api/test/llm-script")
def script_llm(data: dict):
    """Configure the LLM stub with scripted responses.

    Accepts {"responses": [...]} to script specific responses, or {"mode": "down"} to make it unreachable.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            if "responses" in data:
                return client.post("http://stub-llm:8001/control/script", json={"responses": data["responses"]}).json()
            elif "mode" in data:
                return client.post("http://stub-llm:8001/control/script", json={"mode": data["mode"]}).json()
            else:
                return client.post("http://stub-llm:8001/control/script", json={}).json()
    except Exception:
        raise HTTPException(status_code=503, detail="Stub LLM is down")


@router.get("/api/test/llm-requests")
def get_llm_requests():
    """Return recorded LLM requests from the stub.

    Returns list of message objects for inspection.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            return client.get("http://stub-llm:8001/control/requests").json()
    except Exception:
        return []


@router.post("/api/test/pictures")
def set_pictures(data: dict):
    """Configure the Pixel-Art Generator stub with terminal text.

    Accepts {"pictures": {...}} to set picture terminal text, or {"mode": "down"} to make it unreachable.
    """
    try:
        with httpx.Client(timeout=5.0) as client:
            if "pictures" in data:
                return client.post("http://stub-generator:8002/control/pictures", json={"pictures": data["pictures"]}).json()
            elif "mode" in data:
                return client.post("http://stub-generator:8002/control/pictures", json={"mode": data["mode"]}).json()
            else:
                return client.post("http://stub-generator:8002/control/pictures", json={}).json()
    except Exception:
        raise HTTPException(status_code=503, detail="Stub Generator is down")
