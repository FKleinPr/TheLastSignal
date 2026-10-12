"""Endings system for The Last Signal game server.

Handles core choice (give core to archivist-lira, silencer-leader, or flee).
Tracks choice_count (0 when choosing, increments per command).
At count 2: add "The ribs are moving..." warning.
At count 3: check location and set ending (ending-awakeners, ending-silencers, ending-escape, death-awakening).

Integration: Called from main.py process_command_in_game after timer checks.
"""

from typing import Dict, Any, Optional, List

from content.loader import get_locations, get_endings, get_deaths


def get_core_choice(state: dict) -> Optional[str]:
    """Get the player's core choice (awakeners, silencers, flee).
    
    Returns None if no choice made yet.
    """
    return state.get("core_choice", None)


def set_core_choice(state: dict, choice: str) -> None:
    """Set the player's core choice.
    
    choice: "awakeners", "silencers", or "flee"
    """
    state["core_choice"] = choice
    state["choice_count"] = 0


def increment_choice_count(state: dict) -> int:
    """Increment choice_count and return new value.
    
    choice_count starts at 0 when choosing command executes.
    Each subsequent command adds 1.
    """
    if "choice_count" not in state:
        state["choice_count"] = 1
    else:
        state["choice_count"] += 1
    
    return state["choice_count"]


def check_core_choice_ending(state: dict) -> dict:
    """Check if core choice has reached ending conditions.
    
    Returns dict with:
    - text: ending text or death text
    - dead: True if death-awakening
    - ending: ending id if ending reached, None otherwise
    
    At choice_count 2: add warning "The ribs are moving..."
    At choice_count 3: check location and set ending or death.
    """
    choice_count = state.get("choice_count", 0)
    
    # At count 2: add warning text
    if choice_count == 2:
        return {
            "text": "The ribs are moving. You can hear them grinding against each other.",
            "dead": False,
            "ending": None,
        }
    
    # At count 3+: check location and set ending or death
    if choice_count >= 3:
        current_location = state.get("player_location", "")
        core_choice = state.get("core_choice", None)
        
        if core_choice == "awakeners":
            # Give core to archivist-lira in archives -> ending-awakeners
            if current_location in ["edge-of-town", "deep-ribs"]:
                endings = get_endings()
                ending_text = endings.get("ending-awakeners", {}).get("text", "")
                return {
                    "text": ending_text,
                    "dead": False,
                    "ending": "ending-awakeners",
                }
        
        elif core_choice == "silencers":
            # Give core to silencer-leader in control-center -> ending-silencers
            if current_location in ["edge-of-town", "deep-ribs"]:
                endings = get_endings()
                ending_text = endings.get("ending-silencers", {}).get("text", "")
                return {
                    "text": ending_text,
                    "dead": False,
                    "ending": "ending-silencers",
                }
        
        elif core_choice == "flee":
            # Keep core and go to edge-of-town -> ending-escape
            if current_location == "edge-of-town":
                endings = get_endings()
                ending_text = endings.get("ending-escape", {}).get("text", "")
                return {
                    "text": ending_text,
                    "dead": False,
                    "ending": "ending-escape",
                }
        
        # If not in correct location for ending, trigger death-awakening
        if current_location not in ["edge-of-town", "deep-ribs"]:
            deaths = get_deaths()
            death_text = deaths.get("death-awakening", {}).get("text", "You are part of the wreckage now.")
            return {
                "text": death_text,
                "dead": True,
                "ending": None,
            }
    
    return {
        "text": "",
        "dead": False,
        "ending": None,
    }


def apply_core_choice(state: dict, result: dict, parsed: Optional[dict]) -> None:
    """Apply core choice logic to result dict.
    
    Called when player gives core to archivist-lira (archives) or silencer-leader (control-center).
    Sets core_choice and choice_count based on where and to whom core is given.
    
    Updates result["text"] with warning at count 2, or ending/death text at count 3.
    """
    if not parsed:
        return
    
    verb = parsed.get("verb")
    object_name = parsed.get("object")
    target = parsed.get("target")
    current_location = state.get("player_location", "")
    
    # Check if player is giving core to archivist-lira in archives
    if verb == "give" and object_name == "core" and target == "archivist-lira" and current_location == "archives":
        set_core_choice(state, "awakeners")
        result["text"] = "The Awakeners took the core and woke the ship. The town was destroyed, but you escaped. The ship's systems activated, and now it's hunting you across the wasteland. Act II: Can you survive the ship's pursuit, or will you let it consume everything you love?"
        result["ending"] = "ending-awakeners"
        return
    
    # Check if player is giving core to silencer-leader in control-center
    if verb == "give" and object_name == "core" and target == "silencer-leader" and current_location == "control-center":
        set_core_choice(state, "silencers")
        result["text"] = "The Silencers took the core and controlled the ship. They imprisoned you, but the town was saved. Now you must break out and take back what you started. Act II: Can you escape the Silencers' prison and reclaim the core, or will you become one of their tools?"
        result["ending"] = "ending-silencers"
        return
    
    # Check if player is giving core to archivist-lira with core in inventory (show command)
    if verb == "show" and object_name == "core" and target == "archivist-lira" and current_location == "archives":
        set_core_choice(state, "awakeners")
        result["text"] = "The Awakeners took the core and woke the ship. The town was destroyed, but you escaped. The ship's systems activated, and now it's hunting you across the wasteland. Act II: Can you survive the ship's pursuit, or will you let it consume everything you love?"
        result["ending"] = "ending-awakeners"
        return
    
    # Check if player is giving core to silencer-leader with core in inventory (show command)
    if verb == "show" and object_name == "core" and target == "silencer-leader" and current_location == "control-center":
        set_core_choice(state, "silencers")
        result["text"] = "The Silencers took the core and controlled the ship. They imprisoned you, but the town was saved. Now you must break out and take back what you started. Act II: Can you escape the Silencers' prison and reclaim the core, or will you become one of their tools?"
        result["ending"] = "ending-silencers"
        return
    
    # If we have a core_choice and increment choice_count, check for ending/death
    if state.get("core_choice"):
        new_count = increment_choice_count(state)
        
        choice_result = check_core_choice_ending(state)
        
        if choice_result.get("text"):
            result["text"] = result.get("text", "") + " " + choice_result.get("text", "")
        
        if choice_result.get("dead"):
            result["dead"] = True
            result["choices"] = ["continue", "restart"]
            state["dead"] = True
        
        if choice_result.get("ending"):
            state["ending"] = choice_result.get("ending")
            result["ending"] = choice_result.get("ending")


def check_core_choice(state: dict, previous_location: str) -> dict:
    """Count the commands after the core choice (test review 1, P-17).

    The choosing command counts as 0: giving the core to archivist-lira in archives ("awakeners") or to
    silencer-leader in control-center ("silencers"), or entering edge-of-town with the core ("flee"). The 2nd command
    after it adds the awakening warning; on the 3rd the player is in edge-of-town or deep-ribs (the ending of the
    choice) or dies (death-awakening).
    """
    if state.pop("choice_made_turn", False):
        return {}
    location = state.get("player_location", "")
    if (not state.get("core_choice") and location == "edge-of-town" and previous_location != "edge-of-town"
            and "core" in state.get("inventory", [])):
        set_core_choice(state, "flee")
        return {}
    if not state.get("core_choice") or state.get("ending"):
        return {}
    count = increment_choice_count(state)
    deaths = get_deaths()
    if count == 2:
        return {"text": deaths.get("death-awakening", {}).get(
            "warning", "The ribs are moving. You can hear them grinding against each other.")}
    if count == 3:
        if location in ("edge-of-town", "deep-ribs"):
            ending = {"awakeners": "ending-awakeners", "silencers": "ending-silencers",
                      "flee": "ending-escape"}[state["core_choice"]]
            state["ending"] = ending
            return {"ending": ending, "text": get_endings().get(ending, {}).get("text", "")}
        return {"dead": True, "text": deaths.get("death-awakening", {}).get(
            "text", "The ship's awakening finished without you. You are part of the wreckage now.")}
    return {}


def check_death_humming(state: dict, previous_location: str) -> dict:
    """death-humming in deep-ribs: the entering command adds the warning (count 0), every further command in
    deep-ribs adds 1, and at 2 the player dies."""
    if state.get("player_location") != "deep-ribs":
        state.pop("humming_count", None)
        return {}
    death = get_deaths().get("death-humming", {})
    if previous_location != "deep-ribs":
        state["humming_count"] = 0
        return {"text": death.get("warning", "The hum is getting louder. Your ears are bleeding.")}
    state["humming_count"] = state.get("humming_count", 0) + 1
    if state["humming_count"] >= 2:
        return {"dead": True, "text": death.get("text", "The ship decided you were cargo. You did not fit.")}
    return {}


def check_death_faction(state: dict, previous_location: str) -> dict:
    """death-faction in control-center while carrying the core: entering does not count; the 1st command after it
    that neither gives the core to silencer-leader nor leaves adds the warning, the 2nd is death."""
    if state.get("player_location") != "control-center" or "core" not in state.get("inventory", []):
        state.pop("refusal_count", None)
        return {}
    if previous_location != "control-center":
        state["refusal_count"] = 0
        return {}
    death = get_deaths().get("death-faction", {})
    state["refusal_count"] = state.get("refusal_count", 0) + 1
    if state["refusal_count"] == 1:
        return {"text": death.get("warning", "Silencer-Leader is looking at you. He doesn't like your refusal.")}
    return {"dead": True, "text": death.get("text", "Trust is a luxury this town cannot afford.")}


def reset_death_timers(state: dict) -> None:
    """Reset death timers when leaving dangerous locations.
    
    Clears humming_count, refusal_count, dust_count.
    """
    current_location = state.get("player_location", "")
    
    if current_location != "deep-ribs" and "humming_count" in state:
        del state["humming_count"]
    
    if current_location != "control-center" and "refusal_count" in state:
        del state["refusal_count"]
    
    if current_location != "bone-yard" and "dust_count" in state:
        del state["dust_count"]
