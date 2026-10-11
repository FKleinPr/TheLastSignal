"""Stub Pixel-Art Generator for testing."""

import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException

# In-memory storage for pictures
_pictures: dict[str, str] = {}
_mode: str = "normal"  # "normal" or "down"

app = FastAPI(title="Stub Generator")


@app.get("/api/assets/{asset_id}/terminal")
def get_asset_terminal(asset_id: str):
    global _mode
    
    if _mode == "down":
        raise HTTPException(status_code=503, detail="Stub Generator is down")
    
    if asset_id in _pictures:
        return _pictures[asset_id]
    
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
