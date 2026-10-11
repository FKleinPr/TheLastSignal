"""Checkpoint system for The Last Signal game server.

Creates and manages auto-checkpoints on location entry and before danger.
Stores checkpoints in game state for recovery when dead.

Integration: Called from main.py during command processing to create auto-checkpoints.
"""

from typing import Dict, Any, Optional, List
import copy


def create_auto_checkpoint(game_state: dict) -> dict:
    """Create an auto-checkpoint from current game state.
    
    Called when player enters a new location or before dangerous situations.
    Returns checkpoint dict with state snapshot.
    """
    # Deep copy state, excluding "last_checkpoint" to avoid circular reference
    state_copy = copy.deepcopy(game_state)
    
    # Remove last_checkpoint from the checkpoint to avoid circular reference
    if "last_checkpoint" in state_copy:
        del state_copy["last_checkpoint"]
    
    # Remove location_history from checkpoint to save space
    if "location_history" in state_copy:
        del state_copy["location_history"]
    
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
        "timestamp": None,
    }


def set_last_checkpoint(game_state: dict, checkpoint: dict) -> None:
    """Set the last checkpoint in game state."""
    game_state["last_checkpoint"] = checkpoint


def get_last_checkpoint(game_state: dict) -> Optional[dict]:
    """Get the last checkpoint from game state."""
    return game_state.get("last_checkpoint")


def create_checkpoint_on_location_change(
    current_location: str,
    previous_location: str,
    game_state: dict
) -> bool:
    """Create auto-checkpoint when entering a new location.
    
    Returns True if checkpoint was created, False if already in same location.
    """
    if current_location == previous_location:
        return False
    
    # Create checkpoint for new location
    checkpoint = create_auto_checkpoint(game_state)
    set_last_checkpoint(game_state, checkpoint)
    
    return True


def create_checkpoint_before_danger(
    location: str,
    game_state: dict,
    flags: list
) -> bool:
    """Create auto-checkpoint before dangerous situations.
    
    Returns True if checkpoint was created.
    Dangerous locations: bone-yard (when dust-active), deep-ribs, control-center.
    """
    # Check if we're in a dangerous location
    dangerous_locations = ["bone-yard", "deep-ribs", "control-center"]
    
    if location not in dangerous_locations:
        return False
    
    # Check if dust-active flag is set (bone-yard danger)
    if location == "bone-yard" and "dust-active" in flags:
        checkpoint = create_auto_checkpoint(game_state)
        set_last_checkpoint(game_state, checkpoint)
        return True
    
    # Check if we're entering deep-ribs (humming death danger)
    if location == "deep-ribs":
        checkpoint = create_auto_checkpoint(game_state)
        set_last_checkpoint(game_state, checkpoint)
        return True
    
    # Check if we're entering control-center with core (faction death danger)
    if location == "control-center" and "core" in flags:
        checkpoint = create_auto_checkpoint(game_state)
        set_last_checkpoint(game_state, checkpoint)
        return True
    
    return False


def save_game_to_slot(game_state: dict) -> dict:
    """Save current game state to save slot.
    
    Returns save slot dict with state snapshot.
    """
    # Deep copy state
    state_copy = copy.deepcopy(game_state)
    
    # Remove location_history to save space
    if "location_history" in state_copy:
        del state_copy["location_history"]
    
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
        "timestamp": None,
    }


def load_game_from_slot(game_state: dict, save_slot: dict) -> dict:
    """Load game state from save slot.
    
    Returns restored state dict.
    """
    if not save_slot:
        return {}
    
    restored_state = save_slot.get("state", {})
    
    return {
        "player_location": restored_state.get("player_location", "bone-yard"),
        "inventory": list(restored_state.get("inventory", [])),
        "flags": list(restored_state.get("flags", [])),
        "clues": list(restored_state.get("clues", [])),
        "relationships": dict(restored_state.get("relationships", {})),
        "turns": restored_state.get("turns", 0),
        "dead": False,
        "ending": None,
        "dust_count": restored_state.get("dust_count", 0),
    }
