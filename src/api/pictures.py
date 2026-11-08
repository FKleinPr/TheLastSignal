"""Picture proxy for The Last Signal game server.

Handles GET /api/pictures/{name}/png endpoint:
- Checks if name is in the picture list from content
- Proxies to Pixel-Art Generator with 2s timeout
- Returns 404 for unknown name, generator error, or timeout

Integration: Imported and included in main.py as router for /api/pictures/{name}/png.
"""

import os
import httpx
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from content.loader import get_pictures

router = APIRouter()

PIXEL_ART_TIMEOUT_S = 2


@router.get("/api/pictures/{name}/png")
def get_picture_png(name: str):
    """Proxy image requests to the Pixel-Art Generator stub.
    
    Returns 404 if name is not in picture list, or if generator is down/returns 404.
    Returns 200 with image/png bytes if successful.
    
    Acceptance criteria:
    - AC-021: Stub generator holding bone-yard returns 200 with PNG signature
    - AC-025: Stub generator down returns 404 from proxy
    """
    # Check if name is in the picture list
    pictures_list = get_pictures()
    picture_names = [p["name"] for p in pictures_list]
    
    if name not in picture_names:
        raise HTTPException(status_code=404, detail=f"Picture {name} not in picture list")
    
    # Proxy to stub generator
    pixel_art_base_url = os.getenv("PIXEL_ART_BASE_URL", "http://stub-generator:8002")
    
    try:
        with httpx.Client(timeout=PIXEL_ART_TIMEOUT_S) as client:
            response = client.get(f"{pixel_art_base_url}/api/assets/{name}/png")
            if response.status_code == 200:
                return Response(content=response.content, media_type="image/png")
            raise HTTPException(status_code=404, detail="Generator returned 404")
    except (httpx.TimeoutException, httpx.ConnectError, Exception):
        raise HTTPException(status_code=404, detail="Generator unavailable")
