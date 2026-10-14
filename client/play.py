#!/usr/bin/env python3
"""Terminal client for The Last Signal: Act I.

Interactive text adventure client using only Python standard library.
Connects to http://127.0.0.1:18003 and handles all game interactions.

Usage: python3 client/play.py [--url http://127.0.0.1:18003]
"""

import json
import sys
import urllib.request
import urllib.parse
import urllib.error

BASE_URL = "http://127.0.0.1:18003"


def make_request(endpoint: str, data: dict = None) -> dict:
    """Make HTTP request to game server.
    
    Returns parsed JSON response or raises error.
    """
    url = f"{BASE_URL}{endpoint}"
    
    if data:
        body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(url, data=body, method='POST')
        req.add_header('Content-Type', 'application/json')
    else:
        req = urllib.request.Request(url, method='GET')
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError("Game not found. Start a new game first.")
        raise ValueError(f"Server error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot connect to server: {e.reason}")


def new_game() -> str:
    """Start a new game and return game_id."""
    print("\n" + "=" * 60)
    print("THE LAST SIGNAL: Act I")
    print("=" * 60)
    print("\nConnecting to game server...")
    
    response = make_request("/api/games")
    game_id = response["game_id"]
    game_response = response["response"]
    
    print(f"\n{game_response['text']}")
    
    if game_response.get("pictures"):
        print("\n[ Visual assets loading... ]")
    
    return game_id


def get_game_state(game_id: str) -> dict:
    """Get current game state."""
    return make_request(f"/api/games/{game_id}")


def send_command(game_id: str, text: str) -> dict:
    """Send a player command to the game."""
    return make_request(f"/api/games/{game_id}/commands", {"text": text})


def display_response(response: dict, is_new_game: bool = False) -> None:
    """Display game response to player."""
    if not is_new_game:
        print("\n" + "-" * 60)
    
    print(f"\n{response['text']}")
    
    if response.get("pictures"):
        print("\n[ Visual assets: " + str(len(response['pictures'])) + " loaded ]")
    
    if response.get("dead"):
        print("\n" + "!" * 60)
        print("YOU ARE DEAD")
        print("!" * 60)
        print("\nChoices:")
        print("  continue  - Restore from last checkpoint")
        print("  restart   - Restart Act I from beginning")
        print("!" * 60)
    
    if response.get("ending"):
        print("\n" + "=" * 60)
        print("ACT I COMPLETE")
        print("=" * 60)
        print(f"\n{response['text']}")
        print("\n[ Your Act I journey has ended. ]")
        print("Type 'restart' to start again.")
        print("=" * 60)


def show_inventory(inventory: list) -> None:
    """Show player's inventory."""
    if not inventory:
        print("\n[ Inventory: Empty ]")
        return
    
    print("\n[ Inventory: " + ", ".join(inventory) + " ]")


def show_help() -> None:
    """Show available commands."""
    help_text = """
Available Commands:
  go <direction>      - Move north, south, east, west (or n, s, e, w)
  look                - Look around current location
  take <object>       - Pick up an object
  drop <object>       - Drop an object from inventory
  give <object> to <target> - Give item to character
  show <object> to <target> - Show item to character
  use <object> on <target>  - Use item on something
  talk to <character> - Talk to a character
  ask <character> about <topic> - Ask character something
  pick-lock           - Pick a locked door (requires lock-pick)
  wait                - Wait a turn
  save                - Save game state
  load                - Load saved game state
  continue            - Continue from last checkpoint (when dead)
  restart             - Restart Act I from beginning
  inventory           - Show your inventory
  help                - Show this help message
  quit                - Exit the game
  """
    print(help_text)


def get_player_input() -> str:
    """Get input from player."""
    try:
        return input("\n> ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\n\nGoodbye!")
        sys.exit(0)


def main():
    """Main game loop."""
    game_id = None
    
    # Check if server is available
    try:
        with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=5) as response:
            if response.read() == b'{"status":"ok"}':
                print("Server is online.")
            else:
                print("Server responded unexpectedly.")
    except urllib.error.URLError as e:
        print(f"\nError: Cannot connect to game server at {BASE_URL}")
        print(f"Make sure the server is running: docker compose up -d")
        print(f"\nServer should be on http://127.0.0.1:18003")
        sys.exit(1)
    
    # Start new game
    try:
        game_id = new_game()
    except ValueError as e:
        print(f"\nError starting game: {e}")
        sys.exit(1)
    except ConnectionError as e:
        print(f"\nError connecting to server: {e}")
        sys.exit(1)
    
    # Main game loop
    while True:
        # Get player input
        player_input = get_player_input()
        
        if not player_input:
            continue
        
        input_lower = player_input.lower().strip()
        
        # Handle special commands
        if input_lower == "help":
            show_help()
            continue
        
        if input_lower == "inventory":
            try:
                state = get_game_state(game_id)
                show_inventory(state.get("inventory", []))
            except ValueError as e:
                print(f"Error getting state: {e}")
            continue
        
        if input_lower == "quit":
            print("\nGoodbye!")
            break
        
        if input_lower == "quit" or input_lower == "exit":
            print("\nGoodbye!")
            break
        
        # Send command to server
        try:
            if game_id:
                response = send_command(game_id, player_input)
                display_response(response)
                
                # Show inventory after command
                if response.get("inventory"):
                    show_inventory(response["inventory"])
                
                # Check if game ended
                if response.get("ending"):
                    print("\n[ Game ended. Type 'restart' to play again. ]")
                    game_id = None  # Reset game_id to force new game
                    continue
                
                # Check if dead and player chose to continue
                if response.get("dead") and player_input.lower() == "continue":
                    continue
                
                # Check if dead and player chose to restart
                if response.get("dead") and player_input.lower() == "restart":
                    print("\n[ Restarting game... ]")
                    game_id = new_game()
                    continue
                
            else:
                # Need to start new game first
                game_id = new_game()
                continue
                
        except ValueError as e:
            if "Game not found" in str(e):
                print("\n[ No active game. Starting new game... ]")
                game_id = new_game()
                continue
            print(f"\nError: {e}")
            continue
        except ConnectionError as e:
            print(f"\nError: {e}")
            print("[ Trying to reconnect... ]")
            try:
                with urllib.request.urlopen(f"{BASE_URL}/api/health", timeout=5):
                    print("Server is back online.")
                    game_id = None
            except:
                print("Server is still unavailable.")
                sys.exit(1)
            continue


if __name__ == "__main__":
    main()
