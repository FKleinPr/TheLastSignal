"""Game command engine for The Last Signal.

Executes parsed commands and applies effects from rules.
Handles movement, item management, character interaction, and game state changes.

Integration: Called from api/commands.py to process player commands.
"""

from typing import Dict, Any, Optional, List
from content.loader import get_locations, get_objects, get_characters, get_rules, get_narrator


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
    
    def execute_command(self, parsed: Dict[str, Any]) -> Dict[str, Any]:
        """Execute parsed command and return response.
        
        Returns dict with: text, location, inventory, dead, choices, pictures
        """
        verb = parsed.get("verb")
        
        if verb is None:
            # No intent detected - return unknown command message
            return self._handle_unknown_command()
        
        # Handle special commands
        if verb in ["save", "load"]:
            return self._handle_save_load(verb)
        
        if verb in ["continue_from_checkpoint", "restart_act_i"]:
            return self._handle_continue_restart(verb)
        
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
    
    def _handle_unknown_command(self) -> Dict[str, Any]:
        """Handle commands with no intent detected."""
        game_text = self.narrator.get("unknown", "I'm not sure what you're trying to do. What do you want to do here?")
        
        return {
            "text": game_text,
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
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
                "choices": [],
            }
        
        # Check if blocked
        if exit_data and exit_data.get("blocked"):
            blocked_text = self.narrator.get("blocked", "locked")
            return {
                "text": f"The exit to {target_location} is {blocked_text}.",
                "location": current_location,
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "choices": [],
            }
        
        # Move to target
        self.game_state["player_location"] = target_location
        
        # Get location description
        target_location_data = self.locations.get(target_location, {})
        description = target_location_data.get("description", "")
        
        return {
            "text": description,
            "location": target_location,
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
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
                break
        
        if not found:
            return {
                "text": "There's nothing here to take.",
                "location": current_location,
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
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
            "choices": [],
        }
    
    def _handle_talk(self, target: str) -> Dict[str, Any]:
        """Handle talk to command."""
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        characters_here = location_data.get("characters", [])
        
        # Find matching character
        found = False
        for char_id in characters_here:
            if char_id == target or self._character_matches(char_id, target):
                found = True
                char_data = self.characters.get(char_id, {})
                lines = char_data.get("lines", [])
                if lines:
                    text = lines[0]
                else:
                    text = "You talk to them, but they don't say anything."
                
                return {
                    "text": text,
                    "location": current_location,
                    "inventory": self.game_state["inventory"],
                    "dead": self.game_state["dead"],
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
                "choices": [],
            }
        
        return {
            "text": "There's no one here to talk to.",
            "location": current_location,
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "choices": [],
        }
    
    def _handle_give(self, object_name: str, target: str) -> Dict[str, Any]:
        """Handle give command."""
        # Check if player has the object
        if object_name not in self.game_state["inventory"]:
            return {
                "text": "You don't have that item.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
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
                # Remove from inventory
                if object_name in self.game_state["inventory"]:
                    self.game_state["inventory"].remove(object_name)
                
                return {
                    "text": f"You give the {object_name} to {target}.",
                    "location": current_location,
                    "inventory": self.game_state["inventory"],
                    "dead": self.game_state["dead"],
                    "choices": [],
                }
        
        if not found:
            return {
                "text": "There's no one here to give it to.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "choices": [],
            }
        
        return {
            "text": "There's no one here to give it to.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
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
                
                # Check if this is the core showing to priest-voa (special case)
                if object_name == "core" and char_id == "priest-voa":
                    return {
                        "text": "The ship knows you have it. The Awakeners will want it. The Silencers will kill for it.",
                        "location": current_location,
                        "inventory": self.game_state["inventory"],
                        "dead": self.game_state["dead"],
                        "choices": [],
                    }
                
                if lines:
                    text = lines[0]
                else:
                    text = f"You show the {object_name} to {target}, but they don't react."
                
                return {
                    "text": text,
                    "location": current_location,
                    "inventory": self.game_state["inventory"],
                    "dead": self.game_state["dead"],
                    "choices": [],
                }
        
        if not found:
            return {
                "text": "There's no one here to show it to.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "choices": [],
            }
        
        return {
            "text": "There's no one here to show it to.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
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
                "choices": [],
            }
        
        # Find matching target
        current_location = self.game_state["player_location"]
        location_data = self.locations.get(current_location, {})
        
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
                    "choices": [],
                }
        
        if not found:
            return {
                "text": "There's nothing here to use it on.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "choices": [],
            }
        
        return {
            "text": "There's nothing here to use it on.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "choices": [],
        }
    
    def _handle_pick_lock(self) -> Dict[str, Any]:
        """Handle pick-lock command."""
        # Check if player has lock-pick
        if "lock-pick" not in self.game_state["inventory"]:
            return {
                "text": "You don't have a lock-pick to use.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "choices": [],
            }
        
        # Check if we're in sanctum (where the locked door is)
        if self.game_state["player_location"] != "sanctum":
            return {
                "text": "There's no locked door here to pick.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "choices": [],
            }
        
        # Unlock the exit to control-center
        # This is a special case - we'll mark it in game state
        self.game_state["flags"].append("gate-locked-solved")
        
        return {
            "text": "You pick the lock. The door to control-center clicks open.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "choices": [],
        }
    
    def _handle_wait(self) -> Dict[str, Any]:
        """Handle wait command."""
        return {
            "text": "You wait...",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
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
                "choices": [],
            }
        
        if verb == "load":
            return {
                "text": "Game loaded.",
                "location": self.game_state["player_location"],
                "inventory": self.game_state["inventory"],
                "dead": self.game_state["dead"],
                "choices": [],
            }
        
        return {
            "text": "Command not processed.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
            "choices": [],
        }
    
    def _handle_continue_restart(self, verb: str) -> Dict[str, Any]:
        """Handle continue/restart commands."""
        return {
            "text": "Command not processed.",
            "location": self.game_state["player_location"],
            "inventory": self.game_state["inventory"],
            "dead": self.game_state["dead"],
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
        return char_id == name
