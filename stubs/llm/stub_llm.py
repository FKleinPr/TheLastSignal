"""Stub LLM server for testing."""

import os
from typing import Any

import uvicorn
from fastapi import FastAPI, HTTPException

# In-memory storage for stub responses
_script_responses: list[str] = []
_script_index: int = 0
_mode: str = "normal"  # "normal" or "down"
_requests: list[dict] = []

app = FastAPI(title="Stub LLM")


@app.post("/v1/chat/completions")
def chat_completions(data: dict):
    global _script_index, _mode, _requests
    
    if _mode == "down":
        raise HTTPException(status_code=503, detail="Stub LLM is down")
    
    # Record the request
    _requests.append({"messages": data.get("messages", [])})
    
    # Return next scripted response or default
    if _script_responses and _script_index < len(_script_responses):
        content = _script_responses[_script_index]
        _script_index += 1
    else:
        content = '{"verb": null}'
    
    return {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": content,
                },
                "finish_reason": "stop",
            }
        ],
    }


@app.post("/control/script")
def control_script(data: dict):
    global _script_responses, _script_index, _mode
    
    if "responses" in data:
        _script_responses = data["responses"]
        _script_index = 0
    elif "mode" in data:
        _mode = data["mode"]
    else:
        _script_responses = []
        _script_index = 0
    
    return {"status": "ok"}


@app.get("/control/requests")
def control_requests():
    return _requests


@app.post("/control/reset")
def control_reset():
    global _script_responses, _script_index, _mode, _requests
    _script_responses = []
    _script_index = 0
    _mode = "normal"
    _requests = []
    return {"status": "ok"}


@app.post("/control/record")
def control_record(data: dict):
    """Record LLM request for testing."""
    global _requests
    messages = data.get("messages", [])
    _requests.append({"messages": messages})
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("stub_llm:app", host="0.0.0.0", port=8001)
