"""Picture handling for The Last Signal game server.

Handles fetching terminal text from Pixel-Art Generator stub, building picture lists for responses,
and handling generator being down/timeout with placeholders.

Integration: Called from main.py to build picture lists for all responses (new game, commands, state).
"""

import os
import httpx

PIXEL_ART_BASE_URL = os.getenv("PIXEL_ART_BASE_URL", "http://stub-generator:8002")
PICTURE_TIMEOUT_S = 2


def get_picture_list_from_content() -> list[dict]:
    """Get the picture list from content/act1.yaml.
    
    Returns the pictures list from Section 9.10 with name, entity_id, type, size, description.
    """
    from content.loader import get_pictures
    return get_pictures()


def fetch_terminal_text(name: str) -> tuple[bool, str | None]:
    """Fetch terminal text from stub generator.
    
    Returns (available, terminal_text) tuple:
    - available: True if 200 OK, False if 404/timeout/error
    - terminal_text: The terminal text if available, None otherwise
    
    Uses httpx with 2-second timeout. If generator is down or returns 404, returns (False, None).
    """
    try:
        with httpx.Client(timeout=PICTURE_TIMEOUT_S) as client:
            response = client.get(f"{PIXEL_ART_BASE_URL}/api/assets/{name}/terminal")
            if response.status_code == 200:
                return (True, response.text)
            return (False, None)
    except (httpx.TimeoutException, httpx.ConnectError, Exception):
        return (False, None)


def build_picture_entry(name: str, picture_list: list[dict]) -> dict:
    """Build a picture entry for response.
    
    Returns dict with name, type, size, available, terminal, placeholder.
    Looks up picture metadata from picture_list, fetches terminal text, creates placeholder if not available.
    """
    # Find picture metadata
    picture_meta = None
    for p in picture_list:
        if p.get("name") == name:
            picture_meta = p
            break
    
    if not picture_meta:
        # Unknown picture - return minimal entry
        return {
            "name": name,
            "type": "unknown",
            "size": "unknown",
            "available": False,
            "terminal": None,
            "placeholder": f"[ picture: {name} ]"
        }
    
    # Fetch terminal text from stub generator
    available, terminal = fetch_terminal_text(name)
    
    # Build placeholder if not available
    placeholder = None
    if not available:
        placeholder = f"[ picture: {name} ]"
    
    return {
        "name": name,
        "type": picture_meta.get("type", "unknown"),
        "size": picture_meta.get("size", "unknown"),
        "available": available,
        "terminal": terminal,
        "placeholder": placeholder
    }


def build_location_pictures(location_id: str, picture_list: list[dict]) -> list[dict]:
    """Build picture list for a location.
    
    Returns list of picture entries for:
    - The location itself (as scene)
    - Any characters present in the location (as character)
    - Any objects in the location or inventory (as item/tool)
    """
    pictures = []
    
    # Add location picture
    pictures.append(build_picture_entry(location_id, picture_list))
    
    # Get characters in location
    from content.loader import get_locations, get_characters
    locations = get_locations()
    location_data = locations.get(location_id, {})
    characters_here = location_data.get("characters", [])
    
    # Add character pictures for characters present
    for char_id in characters_here:
        pictures.append(build_picture_entry(char_id, picture_list))
    
    return pictures


def build_item_pictures(item_ids: list[str], picture_list: list[dict]) -> list[dict]:
    """Build picture list for items.
    
    Returns list of picture entries for the given item IDs.
    Used when player takes items or when items are present.
    """
    pictures = []
    for item_id in item_ids:
        pictures.append(build_picture_entry(item_id, picture_list))
    return pictures


def build_response_pictures(location_id: str, inventory: list[str], characters_here: list[str], picture_list: list[dict]) -> list[dict]:
    """Build complete picture list for a response.
    
    Returns list of picture entries for:
    - Current location (as scene)
    - Characters present in location (as character)
    - Items in inventory (as item/tool)
    
    All entries include available, terminal, placeholder fields.
    """
    pictures = []
    
    # Add location picture
    pictures.append(build_picture_entry(location_id, picture_list))
    
    # Add character pictures for characters present
    for char_id in characters_here:
        pictures.append(build_picture_entry(char_id, picture_list))
    
    # Add item pictures for items in inventory
    for item_id in inventory:
        pictures.append(build_picture_entry(item_id, picture_list))
    
    return pictures


def set_pictures_for_stub(pictures: dict) -> None:
    """Configure stub generator with picture terminal text.
    
    Called via /api/test/pictures endpoint to set picture terminal text for testing.
    pictures: dict mapping picture name to terminal text.
    """
    # This is called by the test endpoint in src/api/test.py
    # The actual stub generator state is managed in stubs/generator/stub_generator.py
    pass


def get_placeholder(name: str) -> str:
    """Get placeholder text for a picture name."""
    return f"[ picture: {name} ]"
