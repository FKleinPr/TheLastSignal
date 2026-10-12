"""Timer system for The Last Signal game server.

Handles turn-based timers: death-dust, death-humming, death-awakening, etc.
Tracks dust_count for death-dust: warning at count 2, death at count 3.

Integration: Called from process_command_in_game in main.py after engine.execute_command().
"""

from typing import Dict, Any, Optional, List

from content.loader import get_locations, get_deaths


def update_dust_timer(game_state: dict, previous_location: str = "") -> dict:
    """Update dust timer and return changes to apply.
    
    When dust-active flag is set:
    - Increment dust_count if in bone-yard and previous_location was bone-yard
    - Reset dust_count to 0 if leaving bone-yard or first command after signal event
    - At count 2: add warning text
    - At count 3: trigger death-dust
    
    Returns dict with:
    - dust_count: current dust count
    - text: warning or death text if triggered
    - dead: True if death triggered
    """
    flags = game_state.get("flags", [])
    
    # Only apply dust timer if dust-active flag is set
    if "dust-active" not in flags:
        return {}
    
    current_location = game_state.get("player_location", "")
    
    # Get or initialize dust_count
    dust_count = game_state.get("dust_count", 0)
    
    # Increment dust_count only if current and previous location are both bone-yard
    # This means we stay in bone-yard for another turn
    if current_location == "bone-yard" and previous_location == "bone-yard":
        dust_count += 1
    else:
        # Reset dust_count when leaving bone-yard or first command after signal event
        dust_count = 0
    
    # Update game_state with new dust_count
    game_state["dust_count"] = dust_count
    
    # Check for warning at count 2
    if dust_count == 2:
        warning_text = "You coughed. The sand is getting thicker around your boots."
        return {
            "dust_count": dust_count,
            "text": warning_text,
            "dead": False,
        }
    
    # Check for death at count 3
    if dust_count == 3:
        death_text = "You are now part of the bone-yard's collection. It is not a selective collection."
        return {
            "dust_count": dust_count,
            "text": death_text,
            "dead": True,
        }
    
    return {
        "dust_count": dust_count,
        "dead": False,
    }


def get_death_warning(location: str, game_state: dict) -> Optional[str]:
    """Get death warning text for current location.
    
    Returns warning text if player should be warned about impending death, None otherwise.
    """
    if location == "bone-yard" and "dust-active" in game_state.get("flags", []):
        dust_count = game_state.get("dust_count", 0)
        if dust_count == 2:
            return "You coughed. The sand is getting thicker around your boots."
    
    return None


def reset_dust_timer(game_state: dict) -> None:
    """Reset dust timer when player leaves bone-yard."""
    current_location = game_state.get("player_location", "")
    
    if current_location != "bone-yard" and "dust-active" in game_state.get("flags", []):
        game_state["dust_count"] = 0


def check_all_timers(game_state: dict, previous_location: str = "") -> dict:
    """Check all timers after a command; the single call point (main.py).

    The core choice comes first: an ending wins over the death timers (test review 1, P-17). Then death-dust,
    death-humming and death-faction. Returns {"text", "dead", "ending"} as far as triggered; warnings are joined.
    """
    from game_engine.endings import check_core_choice, check_death_faction, check_death_humming

    texts = []
    r = check_core_choice(game_state, previous_location)
    if r.get("ending") or r.get("dead"):
        return r
    if r.get("text"):
        texts.append(r["text"])
    for check in (update_dust_timer, check_death_humming, check_death_faction):
        r = check(game_state, previous_location)
        if r.get("dead"):
            return {"dead": True, "text": r.get("text", "")}
        if r.get("text"):
            texts.append(r["text"])
    return {"text": " ".join(texts)} if texts else {}
