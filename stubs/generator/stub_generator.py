"""Stub Pixel-Art Generator for testing."""

import os
from typing import Any
import zlib
import struct

import uvicorn
from fastapi import FastAPI, HTTPException, Response

# In-memory storage for pictures
_pictures: dict[str, str] = {}
_mode: str = "normal"  # "normal" or "down"

app = FastAPI(title="Stub Generator")


# Minimal valid 1x1 pixel PNG data (blue pixel)
def _make_minimal_png() -> bytes:
    """Generate a minimal valid PNG file in memory."""
    # PNG signature
    signature = b'\x89PNG\r\n\x1a\n'
    
    # IHDR chunk (image header)
    width = struct.pack('>I', 1)
    height = struct.pack('>I', 1)
    bit_depth = b'\x08'  # 8-bit
    color_type = b'\x02'  # RGB
    compression = b'\x00'
    filter_method = b'\x00'
    interlace = b'\x00'
    ihdr_data = width + height + bit_depth + color_type + compression + filter_method + interlace
    ihdr_crc = zlib.crc32(b'IHDR' + ihdr_data)
    ihdr_crc = struct.pack('>I', ihdr_crc & 0xFFFFFFFF)
    ihdr_chunk = b'IHDR' + ihdr_data + ihdr_crc
    
    # IDAT chunk (image data) - 1x1 RGB pixel (blue)
    filter_byte = b'\x00'
    pixel_data = b'\x00\x00\x00\xff'  # filter + blue pixel (0,0,255)
    idat_crc = zlib.crc32(b'IDAT' + pixel_data)
    idat_crc = struct.pack('>I', idat_crc & 0xFFFFFFFF)
    idat_chunk = b'IDAT' + pixel_data + idat_crc
    
    # IEND chunk
    iend_crc = zlib.crc32(b'IEND')
    iend_crc = struct.pack('>I', iend_crc & 0xFFFFFFFF)
    iend_chunk = b'IEND' + iend_crc
    
    return signature + ihdr_chunk + idat_chunk + iend_chunk


_MINIMAL_PNG = _make_minimal_png()


@app.get("/api/assets/{asset_id}/terminal")
def get_asset_terminal(asset_id: str):
    global _mode
    
    if _mode == "down":
        raise HTTPException(status_code=503, detail="Stub Generator is down")
    
    if asset_id in _pictures:
        return Response(content=_pictures[asset_id], media_type="text/plain")
    
    raise HTTPException(status_code=404, detail=f"Picture {asset_id} not found")


@app.get("/api/assets/{asset_id}/png")
def get_asset_png(asset_id: str):
    global _mode
    
    if _mode == "down":
        raise HTTPException(status_code=503, detail="Stub Generator is down")
    
    if asset_id in _pictures:
        return Response(content=_MINIMAL_PNG, media_type="image/png")
    
    raise HTTPException(status_code=404, detail=f"Picture {asset_id} not found")


@app.post("/control/pictures")
def control_pictures(data: dict):
    global _pictures, _mode
    
    if "pictures" in data:
        _pictures = data["pictures"]
    elif "mode" in data:
        _mode = data["mode"]
    else:
        _pictures = {}
    
    return {"status": "ok"}


@app.post("/control/reset")
def control_reset():
    global _pictures, _mode
    _pictures = {}
    _mode = "normal"
    return {"status": "ok"}


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("stub_generator:app", host="0.0.0.0", port=8002)
