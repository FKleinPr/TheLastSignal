"""Problem system for The Last Signal game server.

Handles gate-locked problem: door to control-center is locked until solved by:
1. Using key (trade coolant-bottle to merchant-jex)
2. Picking lock (requires lock-pick)

Consequences:
- Pick lock lowers silencer-leader relationship
- Using key lowers merchant-jex relationship

Integration: Called from commands.py when gate-locked commands execute.
"""

from typing import Dict, Any, Optional, List

from content.loader import get_locations, get_characters, get_objects


def is_gate_locked(state: dict) -> bool:
    """Check if gate-locked problem is still active.
    
    Returns True if gate-locked-solved flag is not set.
    """
    flags = state.get("flags", [])
    return "gate-locked-solved" not in flags


def solve_gate_with_pick(state: dict, current_location: str) -> dict:
    """Solve gate-locked by picking the lock (requires lock-pick).
    
    Returns dict with:
    - text: description of picking
    - flag_added: "gate-locked-solved"
    - relationship_change: -1 for silencer-leader
    
    Raises ValueError if not in sanctum or no lock-pick.
    """
    if current_location != "sanctum":
        return {
            "text": "There's no locked door here to pick.",
            "flag_added": None,
            "relationship_change": 0,
        }
    
    if "lock-pick" not in state.get("inventory", []):
        return {
            "text": "That's not happening here. Try something less ambitious.",
            "flag_added": None,
            "relationship_change": 0,
        }
    
    # Add gate-locked-solved flag
    if "gate-locked-solved" not in state["flags"]:
        state["flags"].append("gate-locked-solved")
    
    # Lower silencer-leader relationship by 1 (sound of picking)
    relationships = state.get("relationships", {})
    current_rel = relationships.get("silencer-leader", 0)
    relationships["silencer-leader"] = current_rel - 1
    
    return {
        "text": "You pick the lock. The door to control-center clicks open.",
        "flag_added": "gate-locked-solved",
        "relationship_change": -1,
    }


def solve_gate_with_key(state: dict, current_location: str) -> dict:
    """Solve gate-locked by using key (requires key item).
    
    Returns dict with:
    - text: description of using key
    - flag_added: "gate-locked-solved"
    - relationship_change: -1 for merchant-jex (he remembers the deal)
    
    Raises ValueError if not in sanctum or no key.
    """
    if current_location != "sanctum":
        return {
            "text": "There's no locked door here to use the key on.",
            "flag_added": None,
            "relationship_change": 0,
        }
    
    if "key" not in state.get("inventory", []):
        return {
            "text": "You don't have a key to use.",
            "flag_added": None,
            "relationship_change": 0,
        }
    
    # Add gate-locked-solved flag
    if "gate-locked-solved" not in state["flags"]:
        state["flags"].append("gate-locked-solved")
    
    # Lower merchant-jex relationship by 1 (he remembers the deal)
    relationships = state.get("relationships", {})
    current_rel = relationships.get("merchant-jex", 0)
    relationships["merchant-jex"] = current_rel - 1
    
    # Remove key from inventory after use
    if "key" in state.get("inventory", []):
        state["inventory"].remove("key")
    
    return {
        "text": "You use the key on the locked door. It clicks open.",
        "flag_added": "gate-locked-solved",
        "relationship_change": -1,
    }


def check_gate_exit_blocked(current_location: str, state: dict) -> bool:
    """Check if gate exit (sanctum east) is blocked.
    
    Returns True if gate-locked-solved flag is not set.
    """
    if current_location != "sanctum":
        return False
    
    return is_gate_locked(state)


def get_gate_solved_text(state: dict) -> str:
    """Get text when gate is solved."""
    flags = state.get("flags", [])
    if "gate-locked-solved" in flags:
        return "The door to control-center is now open."
    return "The door is locked."


def trade_coolant_for_key(state: dict) -> dict:
    """Trade coolant-bottle to merchant-jex for key.
    
    Returns dict with:
    - text: merchant's response
    - item_added: "key"
    - item_removed: "coolant-bottle"
    - relationship_change: -1
    
    Raises ValueError if no coolant-bottle or not in scrap-market.
    """
    if "coolant-bottle" not in state.get("inventory", []):
        return {
            "text": "You don't have a coolant-bottle to trade.",
            "item_added": None,
            "item_removed": None,
            "relationship_change": 0,
        }
    
    # Remove coolant-bottle from inventory
    if "coolant-bottle" in state.get("inventory", []):
        state["inventory"].remove("coolant-bottle")
    
    # Add key to inventory
    if "key" not in state.get("inventory", []):
        state["inventory"].append("key")
    
    # Lower merchant-jex relationship by 1 (he remembers the deal)
    relationships = state.get("relationships", {})
    current_rel = relationships.get("merchant-jex", 0)
    relationships["merchant-jex"] = current_rel - 1
    
    return {
        "text": "I'll give you the key for that bottle. You can pick the lock yourself—that takes skill.",
        "item_added": "key",
        "item_removed": "coolant-bottle",
        "relationship_change": -1,
    }


def get_gate_exit_data(state: dict) -> Optional[dict]:
    """Get the gate exit data from sanctum.
    
    Returns exit dict with direction, target, blocked status, or None if not found.
    """
    from content.loader import get_locations
    
    locations = get_locations()
    sanctum_data = locations.get("sanctum", {})
    exits = sanctum_data.get("exits", [])
    
    for exit_info in exits:
        if exit_info.get("direction") == "east":
            # Update blocked status based on gate-locked-solved flag
            blocked = is_gate_locked(state)
            return {
                "direction": "east",
                "target": exit_info.get("target"),
                "blocked": blocked,
            }
    
    return None
