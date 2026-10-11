"""Object interaction system for The Last Signal game server.

Handles take, drop, give, show, use commands with objects.
Manages object discovery and clue tracking.

Integration: Called from commands.py when object interaction commands execute.
"""

from typing import Dict, Any, Optional, List

from content.loader import get_objects, get_clues


class ObjectInteraction:
    """Handles object interaction logic."""
    
    def __init__(self, game_state: dict, objects: dict):
        self.game_state = game_state
        self.objects = objects
    
    def get_object(self, obj_id: str) -> Optional[dict]:
        """Get object data by ID."""
        return self.objects.get(obj_id)
    
    def has_object(self, obj_id: str) -> bool:
        """Check if player has object in inventory."""
        return obj_id in self.game_state.get("inventory", [])
    
    def add_object(self, obj_id: str) -> None:
        """Add object to player's inventory."""
        if "inventory" not in self.game_state:
            self.game_state["inventory"] = []
        if obj_id not in self.game_state["inventory"]:
            self.game_state["inventory"].append(obj_id)
    
    def remove_object(self, obj_id: str) -> None:
        """Remove object from player's inventory."""
        if obj_id in self.game_state.get("inventory", []):
            self.game_state["inventory"].remove(obj_id)
    
    def discover_object_clue(self, obj_id: str, game_state: dict) -> Optional[str]:
        """Discover clue from taking object.
        
        Returns clue_id if clue discovered, None otherwise.
        Updates game_state["clues"] if new clue found.
        """
        clues = get_clues()
        for clue_id, clue_data in clues.items():
            found_in = clue_data.get("found_in")
            if found_in == obj_id:
                # Add clue to game state
                if clue_id not in game_state.get("clues", []):
                    if "clues" not in game_state:
                        game_state["clues"] = []
                    game_state["clues"].append(clue_id)
                
                return clue_id
        
        return None
    
    def get_object_names(self, obj_id: str) -> List[str]:
        """Get all names/synonyms for an object."""
        obj_data = self.objects.get(obj_id, {})
        return obj_data.get("names", [obj_id])
    
    def get_object_description(self, obj_id: str) -> str:
        """Get object description."""
        obj_data = self.objects.get(obj_id, {})
        return obj_data.get("description", "")
