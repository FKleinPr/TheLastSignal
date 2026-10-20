"""Game server for The Last Signal: Act I."""

import copy
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

# Counters of the core choice and the death timers (T-010); cleared by continue and restart
TIMER_KEYS = ("core_choice", "choice_count", "choice_made_turn", "humming_count", "refusal_count", "dust_count")

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

# Load core_choice from content for reaction texts
from content.loader import get_core_choice

def get_core_choice_from_content() -> list[dict]:
    """Get core_choice section from content."""
    return get_core_choice()


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
            "dust_count": 0,
            "last_checkpoint": None,
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
    
    # Get pictures for current location using pictures module
    from game_engine.pictures import build_response_pictures, get_picture_list_from_content
    
    pictures_list = get_picture_list_from_content()
    current_location = "bone-yard"
    
    # Get characters present in current location
    locations = get_locations()
    location_data = locations.get(current_location, {})
    characters_here = location_data.get("characters", [])
    
    # Build complete picture list with location, characters, and inventory items
    response_pictures = build_response_pictures(current_location, [], characters_here, pictures_list)
    
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
    
    # Act I has ended: every command except "restart" answers the ending again (proxy edit P-21, T-010)
    if state.get("ending") and text.strip().lower() != "restart":
        from content.loader import get_endings
        return Response(
            game_id=game_id,
            text=get_endings().get(state["ending"], {}).get("text", ""),
            location=state["player_location"],
            inventory=state["inventory"],
            pictures=[],
            choices=[],
            dead=False,
            ending=state["ending"],
            turn=state["turns"],
        )
    
    # Handle save/load commands first (before dead check)
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
    
    # Handle dead state - but allow continue/restart to be processed
    if state["dead"] and text not in ["continue", "restart"]:
        return Response(
            game_id=game_id,
            text="You are dead. Choose: continue or restart",
            location=state["player_location"],
            inventory=state["inventory"],
            pictures=[],
            choices=["continue", "restart"],
            dead=True,
            ending=None,
            turn=state["turns"],
        )
    
    # Handle continue/restart commands (changed from continue_from_checkpoint/restart_act_i)
    if text in ["continue", "restart"]:
        from game_engine.recovery import continue_from_checkpoint, restart_game, get_checkpoint
        
        if text == "continue":
            # Continue from checkpoint
            checkpoint = get_checkpoint(state)
            recovery_result = continue_from_checkpoint(state, checkpoint)
            
            # Update game state from recovery
            state["player_location"] = recovery_result.get("location", state["player_location"])
            state["inventory"] = recovery_result.get("inventory", state["inventory"])
            state["flags"] = recovery_result.get("flags", state["flags"])
            state["clues"] = recovery_result.get("clues", state["clues"])
            state["dead"] = False
            state["turns"] = recovery_result.get("turn", state["turns"])
            state["last_checkpoint"] = None
            for key in TIMER_KEYS:  # the checkpoint lies before the core choice and the death timers
                state.pop(key, None)
            
            return Response(
                game_id=game_id,
                text=recovery_result.get("text", "You have been restored from the last checkpoint."),
                location=state["player_location"],
                inventory=state["inventory"],
                pictures=[],
                choices=[],
                dead=False,
                ending=None,
                turn=state["turns"],
            )
        
        if text == "restart":
            # Restart game from beginning
            start = get_start()
            recovery_result = restart_game(state, start)
            
            # Update game state from recovery
            state["player_location"] = recovery_result.get("location", "bone-yard")
            state["inventory"] = []
            state["flags"] = []
            state["clues"] = []
            state["dead"] = False
            state["turns"] = 0
            state["ending"] = None
            state["last_checkpoint"] = None
            state["relationships"] = {}
            for key in TIMER_KEYS:
                state.pop(key, None)
            
            return Response(
                game_id=game_id,
                text=recovery_result.get("text", "Game restarted."),
                location=state["player_location"],
                inventory=[],
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
    from content.loader import get_locations, get_objects, get_characters, get_rules, get_deaths, get_endings, get_clues, get_narrator, get_pictures, get_core_choice
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
        "core_choice": get_core_choice(),
    }
    
    # Track previous location before executing command (for dust timer)
    previous_location = state["player_location"]
    
    # Save state BEFORE any command processing for checkpoint
    state_before = copy.deepcopy(state)
    
    parsed = parse_command(text, state, content)
    engine = CommandEngine(state, content)
    result = engine.execute_command(parsed)
    
    # Apply signal event if triggered (take core in bone-yard)
    from game_engine.signal_event import trigger_signal_event, get_signal_text
    
    # Get action verb from parsed command
    action_verb = parsed.get("verb") if parsed else None
    action_object = parsed.get("object") if parsed else None
    
    signal_result = trigger_signal_event(state, state["player_location"], state["inventory"], action_verb or "")
    
    # Create checkpoint from state_before (before any modifications)
    if signal_result.get("create_checkpoint"):
        from game_engine.recovery import create_checkpoint
        state["last_checkpoint"] = create_checkpoint(state_before)
    
    # Apply signal flags
    for flag in signal_result.get("set_flags", []):
        if flag not in state["flags"]:
            state["flags"].append(flag)
    
    # Apply signal dust_count (set to 0 when signal event fires)
    if "set_dust_count" in signal_result:
        state["dust_count"] = signal_result["set_dust_count"]
    
    # Apply signal text if present
    if signal_result.get("signal_text"):
        result["text"] = signal_result.get("signal_text", result.get("text", ""))
    
    # Apply timers and death handling - call check_all_timers() only once (fix duplicate call)
    from game_engine.timers import check_all_timers
    from game_engine.death import trigger_death
    
    # Only call timers when signal event did not fire in this command
    if "set_dust_count" in signal_result:
        death_result = {}
    else:
        death_result = check_all_timers(state, previous_location)
    
    if death_result.get("dead"):
        death_text = death_result.get("text", "You have died.")
        result["text"] = death_text
        result["dead"] = True
        result["choices"] = ["continue", "restart"]
        state["dead"] = True  # Update state for next command
    elif death_result.get("text"):
        # Add warning text to result text
        result["text"] = result.get("text", "") + " " + death_result.get("text", "")
    
    # Get pictures for current location using pictures module
    from game_engine.pictures import build_response_pictures, get_picture_list_from_content
    
    pictures_list = get_picture_list_from_content()
    current_location = state["player_location"]
    
    # Get characters present in current location
    locations = get_locations()
    location_data = locations.get(current_location, {})
    characters_here = location_data.get("characters", [])
    
    # Build complete picture list with location, characters, and inventory items
    response_pictures = build_response_pictures(current_location, state["inventory"], characters_here, pictures_list)
    
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
        ending=state.get("ending"),
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
