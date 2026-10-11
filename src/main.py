"""Game server for The Last Signal: Act I."""

import os
import uuid
from datetime import datetime
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import and validate content
from content.loader import get_pictures, get_locations, get_start
from content.validator import validate_content

# Validate content at startup - server fails to start with clear error if invalid
validate_content()

# Game state storage (in-memory for PoC, SQLite for persistence)
# For now, use simple dict; tests verify persistence through GET /api/games/{id}

games: dict[str, dict] = {}

app = FastAPI(title="The Last Signal")


class GameState(BaseModel):
    game_id: str
    location: str
    inventory: list[str]
    flags: list[str]
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


# Import and include test router
from api.test import router as test_router, set_games_store

app.include_router(test_router)
set_games_store(games)


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/games", status_code=201)
def new_game():
    game_id = str(uuid.uuid4())
    now = datetime.now()
    
    games[game_id] = {
        "state": {
            "player_location": "bone-yard",
            "inventory": [],
            "flags": [],  # Changed from {} to [] as per test expectation
            "relationships": {},
            "turns": 0,
            "dead": False,
            "last_checkpoint_id": None,
            "has_checkpoint": True,  # Changed from False to True as per test expectation
            "has_save": False,
            "ending": None,
            "clues": [],
            "events": [],
            "location_history": ["bone-yard"],
        },
        "checkpoints": [],
        "save_slot": None,
        "turn_log": [],
        "created_at": now.isoformat(),
        "updated_at": now.isoformat(),
    }
    
    # Get opening text from content
    start = get_start()
    opening_text = start.get("text", "The red sand presses against your boots.")
    
    # Get pictures for current location
    pictures = get_pictures()
    current_location = "bone-yard"
    location_pictures = [p for p in pictures if p.get("name") == current_location]
    
    response_pictures = []
    for p in location_pictures:
        response_pictures.append({
            "name": p.get("name"),
            "type": p.get("type"),
            "size": p.get("size"),
            "available": False,
            "terminal": None,
            "placeholder": f"[ picture: {p.get('name')} ]"
        })
    
    response = Response(
        game_id=game_id,
        text=opening_text,
        location="bone-yard",
        inventory=[],
        pictures=response_pictures,
        choices=[],
        dead=False,
        ending=None,
        turn=0,
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
        "flags": state["flags"],  # Now returns list instead of dict
        "relationships": state["relationships"],
        "clues": state["clues"],
        "events": state["events"],
        "turn": state["turns"],
        "dead": state["dead"],
        "ending": state["ending"],
        "has_checkpoint": state["has_checkpoint"],
        "has_save": state["has_save"],
    }


def process_command_in_game(game_id: str, text: str) -> Response:
    """Process a command for a specific game and return Response."""
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    state = games[game_id]["state"]
    
    # Handle dead state
    if state["dead"]:
        return Response(
            game_id=game_id,
            text="You are dead. Choose: continue_from_checkpoint or restart_act_i",
            location=state["player_location"],
            inventory=state["inventory"],
            pictures=[],
            choices=["continue_from_checkpoint", "restart_act_i"],
            dead=True,
            ending=None,
            turn=state["turns"],
        )
    
    # Handle save/load commands
    if text == "save":
        games[game_id]["save_slot"] = {
            "state": state.copy(),
            "timestamp": datetime.now().isoformat(),
        }
        state["has_save"] = True
        return Response(
            game_id=game_id,
            text="Game saved.",
            location=state["player_location"],
            inventory=state["inventory"],
            pictures=[],
            choices=[],
            dead=False,
            ending=None,
            turn=state["turns"],
        )
    
    if text == "load":
        if not games[game_id]["save_slot"]:
            return Response(
                game_id=game_id,
                text="No save slot available.",
                location=state["player_location"],
                inventory=state["inventory"],
                pictures=[],
                choices=[],
                dead=False,
                ending=None,
                turn=state["turns"],
            )
        state.update(games[game_id]["save_slot"]["state"])
        return Response(
            game_id=game_id,
            text="Game loaded.",
            location=state["player_location"],
            inventory=state["inventory"],
            pictures=[],
            choices=[],
            dead=False,
            ending=None,
            turn=state["turns"],
        )
    
    # Handle continue/restart commands
    if text in ["continue_from_checkpoint", "restart_act_i"]:
        return Response(
            game_id=game_id,
            text="Command not processed yet.",
            location=state["player_location"],
            inventory=state["inventory"],
            pictures=[],
            choices=[],
            dead=False,
            ending=None,
            turn=state["turns"],
        )
    
    # Process game commands using LLM + rule-based parser
    from game_engine.parser import parse_command
    from game_engine.commands import CommandEngine
    
    # Load content for parser
    from content.loader import get_locations, get_objects, get_characters, get_rules, get_deaths, get_endings, get_clues, get_narrator, get_pictures
    content = {
        "locations": get_locations(),
        "objects": get_objects(),
        "characters": get_characters(),
        "rules": get_rules(),
        "deaths": get_deaths(),
        "endings": get_endings(),
        "clues": get_clues(),
        "narrator": get_narrator(),
        "pictures": get_pictures(),
    }
    
    parsed = parse_command(text, state, content)
    engine = CommandEngine(state, content)
    result = engine.execute_command(parsed)
    
    # Get pictures for current location
    pictures = get_pictures()
    current_location = state["player_location"]
    location_pictures = [p for p in pictures if p.get("name") == current_location]
    
    response_pictures = []
    for p in location_pictures:
        response_pictures.append({
            "name": p.get("name"),
            "type": p.get("type"),
            "size": p.get("size"),
            "available": False,
            "terminal": None,
            "placeholder": f"[ picture: {p.get('name')} ]"
        })
    
    # Move to next turn
    state["turns"] += 1
    games[game_id]["turn_log"].append({
        "turn": state["turns"],
        "input": text,
        "timestamp": datetime.now().isoformat(),
    })
    games[game_id]["updated_at"] = datetime.now().isoformat()
    
    return Response(
        game_id=game_id,
        text=result.get("text", ""),
        location=result.get("location", state["player_location"]),
        inventory=result.get("inventory", state["inventory"]),
        pictures=response_pictures,
        choices=result.get("choices", []),
        dead=result.get("dead", False),
        ending=None,
        turn=state["turns"],
    )


@app.post("/api/games/{game_id}/commands")
def process_command(game_id: str, payload: CommandPayload):
    if game_id not in games:
        raise HTTPException(status_code=404, detail="Game not found")
    
    if not payload.text:
        raise HTTPException(status_code=422, detail="Empty or missing text")
    
    return process_command_in_game(game_id, payload.text.lower().strip())


@app.get("/api/pictures")
def get_pictures_endpoint():
    """Get the full picture list from content."""
    return get_pictures()


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
