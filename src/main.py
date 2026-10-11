"""Game server for The Last Signal: Act I."""

import os
import uuid
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Game state storage (in-memory for PoC, SQLite for persistence)
# For now, use simple dict; tests verify persistence through GET /api/games/{id}

games: dict[str, dict] = {}

app = FastAPI(title="The Last Signal")


class GameState(BaseModel):
    game_id: str
    location: str
    inventory: list[str]
    flags: dict
    relationships: dict
    clues: list[str]
    events: list[str]
    turn: int
    dead: bool
    ending: Optional[str]
    has_checkpoint: bool
    has_save: bool


class Response(BaseModel):
    game_id: str
    text: str
    location: str
    inventory: list[str]
    pictures: list[dict]
    choices: list[str]
    dead: bool
    ending: Optional[str]
    turn: int


class CommandPayload(BaseModel):
    text: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/games")
def new_game():
    game_id = str(uuid.uuid4())
    now = datetime.now()
    
    games[game_id] = {
        "state": {
            "player_location": "bone-yard",
            "inventory": [],
            "flags": {},
            "relationships": {},
            "turns": 0,
            "dead": False,
            "last_checkpoint_id": None,
            "has_checkpoint": False,
            "has_save": False,
            "ending": None,
            "clues": [],
            "events": [],
            "relationships": {},
            "location_history": ["bone-yard"],
        },
        "checkpoints": [],
        "save_slot": None,
        "turn_log": [],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    response = Response(
        game_id=game_id,
        text="The red sand presses against your boots. Ribs of rusted metal jut from the earth like the bones of fallen gods, their curved spines casting long shadows across the wasteland.",
        location="bone-yard",
        inventory=[],
        pictures=[
            {
                "name": "bone-yard",
                "type": "scene",
                "size": "160x90",
                "available": False,
                "terminal": None,
                "placeholder": "[ picture: bone-yard ]"
            }
        ],
        choices=[],
        dead=False,
        ending=None,
        turn=1,
    )
    
    return {"game_id": game_id, "response": response}


@app.get("/api/games/{game_id}")
def get_game_state(game_id: str):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    state = games[game_id]["state"]
    
    return {
        "game_id": game_id,
        "location": state["player_location"],
        "inventory": state["inventory"],
        "flags": state["flags"],
        "relationships": state["relationships"],
        "clues": state["clues"],
        "events": state["events"],
        "turn": state["turns"],
        "dead": state["dead"],
        "ending": state["ending"],
        "has_checkpoint": state["has_checkpoint"],
        "has_save": state["has_save"],
    }


@app.post("/api/games/{game_id}/commands")
def process_command(game_id: str, payload: CommandPayload):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not payload.text:
        raise HTTPException(status_code=422, detail="Empty or missing text")
    
    state = games[game_id]["state"]
    text = payload.text.lower().strip()
    
    # Handle dead state
    if state["dead"]:
        return JSONResponse(
            status_code=200,
            content={
                "game_id": game_id,
                "text": "You are dead. Choose: continue_from_checkpoint or restart_act_i",
                "location": state["player_location"],
                "inventory": state["inventory"],
                "pictures": [],
                "choices": ["continue_from_checkpoint", "restart_act_i"],
                "dead": True,
                "ending": None,
                "turn": state["turns"],
            }
        )
    
    # Handle save/load commands
    if text == "save":
        games[game_id]["save_slot"] = {
            "state": state.copy(),
            "timestamp": datetime.now().isoformat(),
        }
        state["has_save"] = True
        return JSONResponse(
            status_code=200,
            content={
                "game_id": game_id,
                "text": "Game saved.",
                "location": state["player_location"],
                "inventory": state["inventory"],
                "pictures": [],
                "choices": [],
                "dead": False,
                "ending": None,
                "turn": state["turns"],
            }
        )
    
    if text == "load":
        if not games[game_id]["save_slot"]:
            return JSONResponse(
                status_code=200,
                content={
                    "game_id": game_id,
                    "text": "No save slot available.",
                    "location": state["player_location"],
                    "inventory": state["inventory"],
                    "pictures": [],
                    "choices": [],
                    "dead": False,
                    "ending": None,
                    "turn": state["turns"],
                }
            )
        state.update(games[game_id]["save_slot"]["state"])
        return JSONResponse(
            status_code=200,
            content={
                "game_id": game_id,
                "text": "Game loaded.",
                "location": state["player_location"],
                "inventory": state["inventory"],
                "pictures": [],
                "choices": [],
                "dead": False,
                "ending": None,
                "turn": state["turns"],
            }
        )
    
    # Handle continue/restart commands
    if text in ["continue_from_checkpoint", "restart_act_i"]:
        return JSONResponse(
            status_code=200,
            content={
                "game_id": game_id,
                "text": "Command not processed yet.",
                "location": state["player_location"],
                "inventory": state["inventory"],
                "pictures": [],
                "choices": [],
                "dead": False,
                "ending": None,
                "turn": state["turns"],
            }
        )
    
    # Process game commands
    # Default response for unknown commands
    game_text = "I'm not sure what you're trying to do. What do you want to do here?"
    
    # Move to next turn
    state["turns"] += 1
    games[game_id]["turn_log"].append({
        "turn": state["turns"],
        "input": text,
        "timestamp": datetime.now().isoformat(),
    })
    games[game_id]["updated_at"] = datetime.now().isoformat()
    
    return JSONResponse(
        status_code=200,
        content={
            "game_id": game_id,
            "text": game_text,
            "location": state["player_location"],
            "inventory": state["inventory"],
            "pictures": [],
            "choices": [],
            "dead": False,
            "ending": None,
            "turn": state["turns"],
        }
    )


@app.get("/api/pictures")
def get_pictures():
    return [
        {
            "name": "bone-yard",
            "entity_id": "bone-yard",
            "type": "scene",
            "size": "160x90",
            "description": "Red sand rusted ship ribs with holy signs painted.",
        },
        {
            "name": "watchtower",
            "entity_id": "watchtower",
            "type": "scene",
            "size": "160x90",
            "description": "Satellite dish painted like a holy sign.",
        },
        {
            "name": "scrap-market",
            "entity_id": "scrap-market",
            "type": "scene",
            "size": "160x90",
            "description": "Piles of coolant bottles and scrap metal.",
        },
        {
            "name": "edge-of-town",
            "entity_id": "edge-of-town",
            "type": "scene",
            "size": "160x90",
            "description": "Broken fence and escape route.",
        },
        {
            "name": "archives",
            "entity_id": "archives",
            "type": "scene",
            "size": "160x90",
            "description": "Leather-bound data-slates glowing in dim light.",
        },
        {
            "name": "sanctum",
            "entity_id": "sanctum",
            "type": "scene",
            "size": "160x90",
            "description": "Awakeners hiding in ribs, shadows and ozone.",
        },
        {
            "name": "control-center",
            "entity_id": "control-center",
            "type": "scene",
            "size": "160x90",
            "description": "Silencers with locked door and humming.",
        },
        {
            "name": "deep-ribs",
            "entity_id": "deep-ribs",
            "type": "scene",
            "size": "160x90",
            "description": "Inside hull, dark, humming air, blue light.",
        },
        {
            "name": "player",
            "entity_id": "player",
            "type": "character",
            "size": "32x32",
            "description": "Ordinary individual with core in hand.",
        },
        {
            "name": "priest-voa",
            "entity_id": "priest-voa",
            "type": "character",
            "size": "32x32",
            "description": "Guard with robe, touches hull.",
        },
        {
            "name": "child-echo",
            "entity_id": "child-echo",
            "type": "character",
            "size": "32x32",
            "description": "Small child with closed eyes, ear pressed to red sand, ragged orange scarf.",
        },
        {
            "name": "merchant-jex",
            "entity_id": "merchant-jex",
            "type": "character",
            "size": "32x32",
            "description": "Trader smelling items, dark clothes.",
        },
        {
            "name": "archivist-lira",
            "entity_id": "archivist-lira",
            "type": "character",
            "size": "32x32",
            "description": "Scholar reading glowing slates.",
        },
        {
            "name": "silencer-leader",
            "entity_id": "silencer-leader",
            "type": "character",
            "size": "32x32",
            "description": "Silencer in dark uniform, hand on weapon.",
        },
        {
            "name": "core",
            "entity_id": "core",
            "type": "item",
            "size": "16x16",
            "description": "Glowing metal object, signal source.",
        },
        {
            "name": "key",
            "entity_id": "key",
            "type": "tool",
            "size": "16x16",
            "description": "Metal key for locked door.",
        },
        {
            "name": "data-slate",
            "entity_id": "data-slate",
            "type": "item",
            "size": "16x16",
            "description": "Leather-bound book with glowing text.",
        },
        {
            "name": "lock-pick",
            "entity_id": "lock-pick",
            "type": "tool",
            "size": "16x16",
            "description": "Bent antenna wire, works as pick.",
        },
        {
            "name": "coolant-bottle",
            "entity_id": "coolant-bottle",
            "type": "item",
            "size": "16x16",
            "description": "Bottle of blue liquid, god's blood.",
        },
    ]


@app.post("/api/test/reset")
def reset_test():
    global games
    games = {}
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
