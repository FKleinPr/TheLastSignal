"""Game command engine for The Last Signal.

Executes parsed commands and applies effects from rules.
Handles movement, item management, character interaction, and game state changes.

Integration: Called from api/commands.py to process player commands.
"""

from typing import Dict, Any, Optional, List
from content.loader import get_locations, get_objects, get_characters, get_rules, get_narrator, get_clues
from game_engine.ambiguity import check_ambiguity, get_present_thing_names
from game_engine.characters import CharacterInteraction
from game_engine.objects import ObjectInteraction
from game_engine.clues import discover_clue, check_location_clue, check_object_clue, check_character_clue
from game_engine.problems import is_gate_locked, solve_gate_with_pick, solve_gate_with_key, check_gate_exit_blocked
from game_engine.endings import set_core_choice


class CommandEngine:
    """Executes game commands and applies effects."""
    
    def __init__(self, game_state: dict, content: dict):
        self.game_state = game_state
        self.content = content
        self.locations = get_locations()
        self.objects = get_objects()
        self.characters = get_characters()
        self.rules = get_rules()
        self.narrator = get_narrator()
        self.character_interaction = CharacterInteraction(game_state, self.characters)
        self.object_interaction = ObjectInteraction(game_state, self.objects)
    
    def execute_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parsed command and return response.
        
        Returns dict with: text, location, inventory, dead, choices, pictures, ending
        """
        verb = parsed.get("verb")
        
        if verb is None:
            # No intent detected - return unknown command message
            return self._handle_unknown_command()
        
        # Handle ambiguous response from parser
        if verb == "ambiguous":
            return self._handle_ambiguity(parsed)
        
        # Handle special commands
        if verb in ["save", "load"]:
            return self._handle_save_load(verb)
        
        if verb in ["continue_from_checkpoint", "restart_act_i"]:
            return self._handle_continue_restart(verb)
        
        if verb == "look":
            return self._handle_look()
        
        # Handle movement
        if verb == "go":
            direction = parsed.get("direction")
            if direction:
                return self._handle_move(direction)
        
        # Handle item operations
        if verb == "take":
            object_name = parsed.get("object")
            if object_name:
                return self._handle_take(object_name)
        
        if verb == "drop":
            object_name = parsed.get("object")
            if object_name:
                return self._handle_drop(object_name)
        
        # Handle character interaction
        if verb == "talk":
            target = parsed.get("target")
            if target:
                return self._handle_talk(target)
        
        if verb == "give":
            object_name = parsed.get("object")
            target = parsed.get("target")
            if object_name and target:
                return self._handle_give(object_name, target)
        
        if verb == "show":
            object_name = parsed.get("object")
            target = parsed.get("target")
            if object_name and target:
                return self._handle_show(object_name, target)
        
        if verb == "use":
            object_name = parsed.get("object")
            target = parsed.get("target")
            if object_name and target:
                return self._handle_use(object_name, target)
        
        if verb == "pick-lock":
            return self._handle_pick_lock()
        
        if verb == "wait":
            return self._handle_wait()
        
        # No matching rule - return impossible action
        return self._handle_impossible_action()
    
    def _result(self, text: str) -> Dict[str, Any]:
        """A response that leaves location and death state as they are."""
        return {
            "text": text,
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }

    def _handle_unknown_command(self) -> Dict[str, Any]:
        """Handle commands with no intent detected."""
        game_text = self.narrator.get("unknown", "I'm not sure what you're trying to do. What do you want to do here?")
        
        return {
            "text": game_text,
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_ambiguity(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ambiguous command response.
        
        Returns ambiguity message without changing state.
        """
        return {
            "text": parsed.get("text", "Which option do you mean?"),
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_impossible_action(self) -> Dict[str, Any]:
        """Handle commands that are not possible in current context."""
        game_text = self.narrator.get("impossible", "That's not happening here. Try something less ambitious.")
        
        return {
            "text": game_text,
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_move(self, direction: str) -> Dict[str, Any]:
        """Handle movement command."""
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        exits = location_data.get("exits", [])
        
        # Find matching exit
        target_location = None
        exit_data = None
        
        for exit_info in exits:
            if exit_info.get("direction") == direction:
                target_location = exit_info.get("target")
                exit_data = exit_info
                break
        
        if not target_location:
            # Direction not available
            return {
                "text": f"You can't go {direction} from here.",
                "location": current_location,
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        # Check if blocked (dynamic blocking for gate-locked)
        if exit_data and exit_data.get("blocked"):
            # Check if this is the gate-locked exit from sanctum
            if current_location == "sanctum" and direction == "east":
                if is_gate_locked(self.game_state):
                    blocked_text = self.narrator.get("blocked", "locked")
                    return {
                        "text": f"The exit to {target_location} is {blocked_text}.",
                        "location": current_location,
                        "inventory": self.game_state["inventory"],
                        "dead": self.game_state["dead"],
                        "ending": self.game_state.get("ending"),
                        "choices": [],
                    }
            elif exit_data.get("blocked"):
                blocked_text = self.narrator.get("blocked", "locked")
                return {
                    "text": f"The exit to {target_location} is {blocked_text}.",
                    "location": current_location,
                    "inventory": self.game_state["inventory"],
                    "dead": self.game_state["dead"],
                    "ending": self.game_state.get("ending"),
                    "choices": [],
                }
        
        # Move to target
        self.game_state["player_location"] = target_location
        
        # Get location description
        target_location_data = self.locations.get(target_location, {})
        description = target_location_data.get("description", "")
        
        # Check for flee choice reaction when entering edge-of-town with core
        inventory = self.game_state.get("inventory", [])
        if target_location == "edge-of-town" and "core" in inventory:
            from content.loader import get_core_choice
            core_choice_list = get_core_choice()
            reaction_text = ""
            for choice_data in core_choice_list:
                if choice_data.get("location") == "edge-of-town":
                    reaction_text = choice_data.get("text", "")
                    break
            
            if reaction_text:
                description = f"{description} {reaction_text}"
        
        # Check for location clue when entering new location
        location_clue_id = check_location_clue(target_location)
        if location_clue_id:
            discover_clue(location_clue_id, self.game_state)
        
        return {
            "text": description,
            "location": target_location,
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_look(self) -> Dict[str, Any]:
        """Handle look command.
        
        Returns location description and discovers location clue if present.
        """
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        description = location_data.get("description", "")
        
        # Discover location clue when looking at the location
        location_clue_id = check_location_clue(current_location)
        if location_clue_id:
            discover_clue(location_clue_id, self.game_state)
        
        # Add clue text to description if discovered
        from content.loader import get_clues
        clues = get_clues()
        if location_clue_id and location_clue_id in clues:
            clue_text = clues[location_clue_id].get("text", "")
            description = f"{description}\n\n{clue_text}"
        
        return {
            "text": description,
            "location": current_location,
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_take(self, object_name: str) -> Dict[str, Any]:
        """Handle take command."""
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        available_objects = location_data.get("objects", [])
        
        # Find matching object
        found = False
        for obj_id in available_objects:
            if obj_id == object_name or self._object_matches(obj_id, object_name):
                found = True
                if obj_id not in self.game_state["inventory"]:
                    self.game_state["inventory"].append(obj_id)
                
                # Discover clue from taking object
                clue_id = check_object_clue(obj_id)
                if clue_id:
                    discover_clue(clue_id, self.game_state)
                
                break
        
        if not found:
            return {
                "text": "There's nothing here to take.",
                "location": current_location,
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        # Get object description
        obj_data = self.objects.get(object_name, {})
        description = obj_data.get("description", "")
        
        return {
            "text": f"You take the {object_name}. {description}",
            "location": current_location,
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_drop(self, object_name: str) -> Dict[str, Any]:
        """Handle drop command."""
        if object_name in self.game_state["inventory"]:
            self.game_state["inventory"].remove(object_name)
        
        return {
            "text": f"You drop the {object_name}.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_talk(self, target: str) -> Dict[str, Any]:
        """Handle talk to command."""
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        characters_here = location_data.get("characters", [])
        
        # Check for ambiguity first - only check character matches, not objects
        narrator_ambiguous = self.narrator.get("ambiguous", "Which")
        ambiguity_response = self._check_ambiguity_for_talk(target, current_location, characters_here, narrator_ambiguous)
        if ambiguity_response:
            return ambiguity_response
        
        # Find matching character
        found = False
        for char_id in characters_here:
            if char_id == target or self._character_matches(char_id, target):
                found = True
                char_data = self.characters.get(char_id, {})
                lines = char_data.get("lines", [])
                
                # Check if player has core for conditional dialogue
                has_core = "core" in self.game_state.get("inventory", [])
                
                # Get appropriate lines based on game state
                character_lines = self.character_interaction.get_character_lines(char_id, has_core)
                text = character_lines[0]
                
                # Discover clue from talking to character
                clue_id = check_character_clue(char_id, has_core)
                if clue_id:
                    discover_clue(clue_id, self.game_state)
                
                return {
                    "text": text,
                    "location": current_location,
                    "inventory": self.game_state["inventory"],
                    "dead": self.game_state["dead"],
                    "ending": self.game_state.get("ending"),
                    "choices": [],
                }
        
        if not found:
            # Check if target is an object (not a character)
            # If so, return impossible message (can't talk to objects)
            if self._object_matches_any(target):
                return self._handle_impossible_action()
            
            # If target is neither character nor object, return no one here
            return {
                "text": "There's no one here to talk to.",
                "location": current_location,
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        return {
            "text": "There's no one here to talk to.",
            "location": current_location,
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _check_ambiguity_for_talk(self, target: str, current_location: str, characters_here: list, narrator_ambiguous: str) -> Optional[Dict[str, Any]]:
        """Check if talk target is ambiguous and return ambiguity response.
        
        Returns dict with ambiguity text or None if no ambiguity.
        Does not modify state.
        Only checks character matches, not objects.
        """
        # Check if target matches multiple present characters
        matches = []
        for char_id in characters_here:
            if char_id == target or self._character_matches(char_id, target):
                matches.append(char_id)
        
        if len(matches) > 1:
            # Ambiguity found - return message with narrator.ambiguous text
            options = ", ".join(sorted(matches))
            return {
                "text": f"{narrator_ambiguous} {target}? Options: {options}.",
                "location": current_location,
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        return None
    
    def _handle_give(self, object_name: str, target: str) -> Dict[str, Any]:
        """Handle give command."""
        # Check if player has the object
        if object_name not in self.game_state["inventory"]:
            return {
                "text": "You don't have that item.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        # Find matching character
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        characters_here = location_data.get("characters", [])
        
        found = False
        for char_id in characters_here:
            if char_id == target or self._character_matches(char_id, target):
                found = True
                inventory = self.game_state["inventory"]
                # gate-locked: merchant-jex trades the key for the priest's coolant bottle and remembers the deal
                if object_name == "coolant-bottle" and char_id == "merchant-jex":
                    inventory.remove("coolant-bottle")
                    if "key" not in inventory:
                        inventory.append("key")
                    self.character_interaction.update_relationship("merchant-jex", -1)
                    return self._result("I'll give you the key for that bottle. "
                                        "You can pick the lock yourself—that takes skill.")
                # core-wake: giving the core is the choice for a faction (the endings count from this command)
                choice = {("archivist-lira", "archives"): "awakeners",
                          ("silencer-leader", "control-center"): "silencers"}.get((char_id, current_location))
                if object_name == "core" and choice:
                    inventory.remove("core")
                    set_core_choice(self.game_state, choice)
                    self.game_state["choice_made_turn"] = True
                    
                    # Get reaction text from core_choice content
                    from content.loader import get_core_choice
                    core_choice_list = get_core_choice()
                    reaction_text = ""
                    for choice_data in core_choice_list:
                        if choice_data.get("target") == char_id and choice_data.get("location") == current_location:
                            reaction_text = choice_data.get("text", "")
                            break
                    
                    if reaction_text:
                        return self._result(reaction_text)
                    
                    return self._result(f"You give the core to {char_id}.")
                
                # Remove from inventory
                if object_name in inventory:
                    inventory.remove(object_name)
                
                # Update relationship
                self.character_interaction.update_relationship(char_id, 1)
                
                return {
                    "text": f"You give the {object_name} to {target}.",
                    "location": current_location,
                    "inventory": self.game_state["inventory"],
                    "dead": self.game_state["dead"],
                    "ending": self.game_state.get("ending"),
                    "choices": [],
                }
        
        if not found:
            return {
                "text": "There's no one here to give it to.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        return {
            "text": "There's no one here to give it to.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_show(self, object_name: str, target: str) -> Dict[str, Any]:
        """Handle show command."""
        # Check if player has the object
        if object_name not in self.game_state["inventory"]:
            return {
                "text": "You don't have that item to show.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        # Find matching character
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        characters_here = location_data.get("characters", [])
        
        found = False
        for char_id in characters_here:
            if char_id == target or self._character_matches(char_id, target):
                found = True
                char_data = self.characters.get(char_id, {})
                lines = char_data.get("lines", [])
                
                # Special case: show core to priest-voa gives coolant-bottle
                if object_name == "core" and char_id == "priest-voa":
                    # Give coolant-bottle to player
                    if "coolant-bottle" not in self.game_state["inventory"]:
                        self.game_state["inventory"].append("coolant-bottle")
                    
                    return {
                        "text": "The ship knows you have it. The Awakeners will want it. The Silencers will kill for it.",
                        "location": current_location,
                        "inventory": self.game_state["inventory"],
                        "dead": self.game_state["dead"],
                        "ending": self.game_state.get("ending"),
                        "choices": [],
                    }
                
                # Check if player has core for conditional dialogue
                has_core = "core" in self.game_state.get("inventory", [])
                
                # Get appropriate lines based on game state
                character_lines = self.character_interaction.get_character_lines(char_id, has_core)
                text = character_lines[0]
                
                # Discover clue from showing object to character
                clue_id = check_character_clue(char_id, has_core)
                if clue_id:
                    discover_clue(clue_id, self.game_state)
                
                return {
                    "text": text,
                    "location": current_location,
                    "inventory": self.game_state["inventory"],
                    "dead": self.game_state["dead"],
                    "ending": self.game_state.get("ending"),
                    "choices": [],
                }
        
        if not found:
            return {
                "text": "There's no one here to show it to.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        return {
            "text": "There's no one here to show it to.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_use(self, object_name: str, target: str) -> Dict[str, Any]:
        """Handle use command."""
        # Check if player has the object
        if object_name not in self.game_state["inventory"]:
            return {
                "text": "You don't have that item to use.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        # Find matching target
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        
        # gate-locked: the key opens the door from sanctum to control-center
        if object_name == "key" and target in ("door", "gate", "lock"):
            return self._result(solve_gate_with_key(self.game_state, current_location)["text"])

        # Check if target is a character or location
        characters_here = location_data.get("characters", [])
        found = False
        
        for char_id in characters_here:
            if char_id == target or self._character_matches(char_id, target):
                found = True
                return {
                    "text": f"You try to use the {object_name} on {target}, but it doesn't work.",
                    "location": current_location,
                    "inventory": self.game_state["inventory"],
                    "dead": self.game_state["dead"],
                    "ending": self.game_state.get("ending"),
                    "choices": [],
                }
        
        if not found:
            return {
                "text": "There's nothing here to use it on.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        return {
            "text": "There's nothing here to use it on.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_pick_lock(self) -> Dict[str, Any]:
        """Handle pick-lock command."""
        # Check if player has lock-pick
        if "lock-pick" not in self.game_state["inventory"]:
            return {
                "text": "That's not happening here. Try something less ambitious.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        # gate-locked: picking the lock opens the door and lowers silencer-leader (they hear it)
        return self._result(solve_gate_with_pick(self.game_state, self.game_state["player_location"])["text"])

    def _handle_wait(self) -> Dict[str, Any]:
        """Handle wait command."""
        return {
            "text": "You wait...",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_save_load(self, verb: str) -> Dict[str, Any]:
        """Handle save/load commands."""
        if verb == "save":
            return {
                "text": "Game saved.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        if verb == "load":
            return {
                "text": "Game loaded.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "ending": self.game_state.get("ending"),
                "choices": [],
            }
        
        return {
            "text": "Command not processed.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _handle_continue_restart(self, verb: str) -> Dict[str, Any]:
        """Handle continue/restart commands."""
        return {
            "text": "Command not processed.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "ending": self.game_state.get("ending"),
            "choices": [],
        }
    
    def _object_matches(self, obj_id: str, name: str) -> bool:
        """Check if object name matches object ID."""
        if obj_id == name:
            return True
        obj_data = self.objects.get(obj_id, {})
        names = obj_data.get("names", [])
        return name.lower() in names
    
    def _object_matches_any(self, name: str) -> bool:
        """Check if any object matches the given name."""
        for obj_id in self.objects.keys():
            if self._object_matches(obj_id, name):
                return True
        return False
    
    def _character_matches(self, char_id: str, name: str) -> bool:
        """Check if character name matches character ID."""
        if char_id == name:
            return True
        char_data = self.characters.get(char_id, {})
        names = char_data.get("names", [])
        return name.lower() in names
