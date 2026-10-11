"""Recovery system for The Last Signal game server.

Handles "continue" and "restart" commands when dead.
"continue" restores the last checkpoint, "restart" resets to initial state.

Integration: Called from process_command_in_game in main.py to handle continue/restart.
"""

from typing import Dict, Any, Optional, List
import copy

from content.loader import get_start, get_locations


def continue_from_checkpoint(game_state: dict, checkpoint: Optional[dict]) -> dict:
    """Continue from the last checkpoint.
    
    Restores state from checkpoint, sets dead=False, choices=[].
    Returns new state dict.
    """
    if not checkpoint:
        return {
            "text": "No checkpoint available to continue from.",
            "dead": True,
            "choices": ["continue", "restart"],
        }
    
    # Restore state from checkpoint - use deep copy to avoid mutations
    restored_state = copy.deepcopy(checkpoint.get("state", {}))
    
    return {
        "text": "You have been restored from the last checkpoint. The ship has woken up, and it knows you're here.",
        "location": restored_state.get("player_location", "bone-yard"),
        "inventory": list(restored_state.get("inventory", [])),
        "flags": list(restored_state.get("flags", [])),
        "clues": list(restored_state.get("clues", [])),
        "dust_count": restored_state.get("dust_count", 0),
        "dead": False,
        "choices": [],
        "turn": restored_state.get("turns", 0),
    }


def restart_game(game_state: dict, start_data: dict) -> dict:
    """Restart Act I from the beginning.
    
    Resets to initial state: bone-yard, empty inventory, no flags, dead=False.
    Returns new state dict.
    """
    start_location = start_data.get("location", "bone-yard")
    start_text = start_data.get("text", "The red sand presses against your boots.")
    
    return {
        "text": start_text,
        "location": start_location,
        "inventory": [],
        "flags": [],
        "clues": [],
        "dead": False,
        "choices": [],
        "turn": 0,
        "ending": None,
    }


def create_checkpoint(game_state: dict) -> dict:
    """Create a checkpoint from current game state.
    
    Returns checkpoint dict with state snapshot.
    Stores a deep copy of state, excluding "last_checkpoint" field.
    """
    # Deep copy state, excluding "last_checkpoint" to avoid circular reference
    state_copy = copy.deepcopy(game_state)
    
    # Remove last_checkpoint from the checkpoint to avoid circular reference
    if "last_checkpoint" in state_copy:
        del state_copy["last_checkpoint"]
    
    return {
        "state": {
            "player_location": state_copy.get("player_location", "bone-yard"),
            "inventory": list(state_copy.get("inventory", [])),
            "flags": list(state_copy.get("flags", [])),
            "clues": list(state_copy.get("clues", [])),
            "relationships": dict(state_copy.get("relationships", {})),
            "turns": state_copy.get("turns", 0),
            "dead": False,
            "ending": None,
            "dust_count": state_copy.get("dust_count", 0),
        },
        "timestamp": None,  # Can be added for tracking
    }


def get_checkpoint(game_state: dict) -> Optional[dict]:
    """Get the last checkpoint from game state."""
    return game_state.get("last_checkpoint")


def set_checkpoint(game_state: dict, checkpoint: dict) -> None:
    """Set the last checkpoint in game state."""
    game_state["last_checkpoint"] = checkpoint
