"""Character interaction system for The Last Signal game server.

Handles talk to, give, show, use commands with characters.
Manages character dialogue, conditional responses, and relationships.

Integration: Called from commands.py when character interaction commands execute.
"""

from typing import Dict, Any, Optional, List

from content.loader import get_characters, get_clues


class CharacterInteraction:
    """Handles character interaction logic."""
    
    def __init__(self, game_state: dict, characters: dict):
        self.game_state = game_state
        self.characters = characters
    
    def get_character(self, char_id: str) -> Optional[dict]:
        """Get character data by ID."""
        return self.characters.get(char_id)
    
    def get_character_lines(self, char_id: str, has_core: bool = False) -> List[str]:
        """Get character dialogue lines.
        
        Returns appropriate lines based on game state (e.g., has core).
        When condition is met, returns the conditional line (line 2).
        When condition is not met, returns the always line (line 1).
        """
        char_data = self.characters.get(char_id, {})
        lines = char_data.get("lines", [])
        
        if not lines:
            return [""]
        
        # Check if character has conditional lines based on game state
        # Line 1: Always shown
        # Line 2: Shown when condition is met (replaces line 1)
        if has_core and len(lines) > 1:
            # Return the conditional line (second line in spec 9.4)
            return [lines[1]]
        
        return [lines[0]]
    
    def get_character_faction(self, char_id: str) -> Optional[str]:
        """Get character's faction."""
        char_data = self.characters.get(char_id, {})
        return char_data.get("faction")
    
    def discover_character_clue(self, char_id: str, game_state: dict, has_core: bool = False) -> Optional[str]:
        """Discover clue from talking to character.
        
        Returns clue_id if clue discovered, None otherwise.
        Updates game_state["clues"] if new clue found.
        """
        # Check if character has a clue
        clues = get_clues()
        for clue_id, clue_data in clues.items():
            found_in = clue_data.get("found_in")
            if found_in == char_id:
                # Check if clue is conditional on having core
                conditional = clue_data.get("conditional")
                if conditional and not has_core:
                    return None
                
                # Add clue to game state
                if clue_id not in game_state.get("clues", []):
                    if "clues" not in game_state:
                        game_state["clues"] = []
                    game_state["clues"].append(clue_id)
                
                return clue_id
        
        return None
    
    def get_relationship(self, char_id: str) -> int:
        """Get relationship value with character.
        
        Returns integer value: positive = friendly, negative = hostile, 0 = neutral.
        """
        relationships = self.game_state.get("relationships", {})
        return relationships.get(char_id, 0)
    
    def update_relationship(self, char_id: str, change: int) -> None:
        """Update relationship value with character.
        
        Changes relationship by given amount.
        """
        if "relationships" not in self.game_state:
            self.game_state["relationships"] = {}
        
        current = self.game_state["relationships"].get(char_id, 0)
        self.game_state["relationships"][char_id] = current + change
    
    def get_character_wants(self, char_id: str) -> Optional[str]:
        """Get what character wants."""
        char_data = self.characters.get(char_id, {})
        return char_data.get("wants")
    
    def get_character_secret(self, char_id: str) -> Optional[str]:
        """Get character's secret."""
        char_data = self.characters.get(char_id, {})
        return char_data.get("secret")
