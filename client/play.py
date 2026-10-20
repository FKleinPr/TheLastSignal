#!/usr/bin/env python3
"""Terminal client for The Last Signal: Act I.

Interactive text adventure client using only Python standard library.
Connects to http://127.0.0.1:18003 and handles all game interactions.

Options:
  --url <base url>  - Game server URL (default: http://127.0.0.1:18003)
  --new             - Always start a new game

Usage: python3 client/play.py [--url http://127.0.0.1:18003] [--new]
"""

import json
import sys
import os
import argparse
import urllib.request
import urllib.error

GAME_ID_FILE = ".last-signal-game"


def make_request(endpoint: str, data: dict = None, method: str = "GET", url: str = None) -> dict:
    """Make HTTP request to game server.
    
    Returns parsed JSON response or raises error.
    """
    base = url if url else "http://127.0.0.1:18003"
    full_url = f"{base}{endpoint}"
    
    if data:
        body = json.dumps(data).encode('utf-8')
        req = urllib.request.Request(full_url, data=body, method=method)
        req.add_header('Content-Type', 'application/json')
    else:
        req = urllib.request.Request(full_url, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        if e.code == 404:
            raise ValueError("Game not found. Start a new game first.")
        raise ValueError(f"Server error: {e.code} - {e.reason}")
    except urllib.error.URLError as e:
        raise ConnectionError(f"Cannot reach the game server at {base}.")


def make_post_request(endpoint: str, data: dict = None, url: str = None) -> dict:
    """Make POST HTTP request to game server.
    
    Returns parsed JSON response or raises error.
    """
    return make_request(endpoint, data, method="POST", url=url)


def write_game_id(game_id: str) -> None:
    """Write game ID to .last-signal-game file."""
    with open(GAME_ID_FILE, "w", encoding="utf-8") as f:
        f.write(game_id)


def read_game_id() -> str:
    """Read game ID from .last-signal-game file."""
    if os.path.exists(GAME_ID_FILE):
        with open(GAME_ID_FILE, "r", encoding="utf-8") as f:
            return f.read().strip()
    return ""


def delete_game_id() -> None:
    """Delete .last-signal-game file."""
    if os.path.exists(GAME_ID_FILE):
        os.remove(GAME_ID_FILE)


def print_pictures(pictures: list) -> None:
    """Print pictures in order: the terminal text of an available picture, otherwise its placeholder."""
    for p in pictures or []:
        text = p.get("terminal") if p.get("available") else p.get("placeholder")
        if text:
            print()
            print(text)


def new_game(url: str) -> str:
    """Start a new game and return game_id."""
    print("\n" + "=" * 60)
    print("THE LAST SIGNAL: Act I")
    print("=" * 60)
    print("\nConnecting to game server...")
    
    response = make_post_request("/api/games", {}, url=url)
    game_id = response["game_id"]
    game_response = response["response"]
    
    print_response(game_response)
    
    return game_id


def get_game_state(game_id: str, url: str = None) -> dict:
    """Get current game state."""
    return make_request(f"/api/games/{game_id}", url=url)


def check_game_exists(game_id: str, url: str = None) -> bool:
    """Check if game exists by trying to get its state."""
    try:
        state = make_request(f"/api/games/{game_id}", url=url)
        return True
    except ValueError:
        return False


def send_command(game_id: str, text: str, url: str = None) -> dict:
    """Send a player command to the game."""
    return make_request(f"/api/games/{game_id}/commands", {"text": text}, method="POST", url=url)


def print_response(response: dict) -> None:
    """Display game response to player."""
    # Print pictures - location picture before text, others after
    pictures = response.get("pictures") or []
    print_pictures(pictures[:1])
    
    # Print text
    print(f"\n{response['text']}")
    print_pictures(pictures[1:])
    
    # Handle dead state
    if response.get("dead"):
        print("\n" + "!" * 60)
        print("YOU ARE DEAD")
        print("!" * 60)
        print("\nChoices:")
        print("  continue  - Restore from last checkpoint")
        print("  restart   - Restart Act I from beginning")
        print("!" * 60)
    
    # Handle ending
    if response.get("ending"):
        print("\n" + "=" * 60)
        print("ACT I COMPLETE")
        print("=" * 60)
        print("\n[ Your Act I journey has ended. ]")
        print("Type 'restart' to start again.")
        print("=" * 60)


def print_help() -> None:
    """Print help message locally (no server interaction)."""
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


def print_inventory(inventory: list) -> None:
    """Print inventory locally (no server interaction)."""
    if not inventory:
        print("\n[ Inventory: Empty ]")
        return
    print(f"\n[ Inventory: {', '.join(inventory)} ]")


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
        print("\n\nGoodbye.")
        sys.exit(0)


def main():
    """Main game loop."""
    parser = argparse.ArgumentParser(description="The Last Signal: Act I - Terminal Client")
    parser.add_argument("--url", default="http://127.0.0.1:18003", help="Game server URL")
    parser.add_argument("--new", action="store_true", help="Always start a new game")
    args = parser.parse_args()
    
    # Check for existing game
    game_id = None
    
    if not args.new:
        existing_id = read_game_id()
        if existing_id:
            try:
                state = make_request(f"/api/games/{existing_id}", url=args.url)
                game_id = existing_id
                print("Continuing your game.")
                print_response(send_command(game_id, "look", args.url))
            except ConnectionError:
                print("Cannot reach the game server at {}.".format(args.url))
                sys.exit(1)
            except ValueError:
                # Game not found, start new
                if os.path.exists(GAME_ID_FILE):
                    os.remove(GAME_ID_FILE)
    
    # Start new game if no game_id
    if not game_id:
        try:
            game_id = new_game(args.url)
            write_game_id(game_id)
        except ConnectionError as e:
            print(str(e))
            sys.exit(1)
    
    # Main game loop
    while True:
        try:
            player_input = get_player_input()
        except (EOFError, KeyboardInterrupt):
            print("\n\nGoodbye.")
            sys.exit(0)
        
        if not player_input:
            continue
        
        input_lower = player_input.lower().strip()
        
        # Handle local commands (no server interaction)
        if input_lower == "help":
            print_help()
            continue
        
        if input_lower == "inventory" or input_lower == "i":
            try:
                state = get_game_state(game_id, args.url)
                print_inventory(state.get("inventory", []))
            except ValueError:
                print("No game active.")
            continue
        
        # Handle quit
        if input_lower == "quit":
            print("\nGoodbye.")
            sys.exit(0)
        
        # Handle other commands (send to server)
        try:
            response = send_command(game_id, player_input, args.url)
            print_response(response)
            
            # Write game_id after successful command
            write_game_id(game_id)
            
            # Handle dead state
            if response.get("dead"):
                if input_lower == "continue":
                    # Continue from checkpoint
                    response = send_command(game_id, "continue", args.url)
                    print_response(response)
                    write_game_id(game_id)
                    continue
                if input_lower == "restart":
                    print("\n[ Restarting game... ]")
                    delete_game_id()
                    response = make_post_request("/api/games", url=args.url)
                    game_id = response["game_id"]
                    write_game_id(game_id)
                    if response.get("response"):
                        print_pictures(response["response"].get("pictures", []))
                        print(f"\n{response['response']['text']}")
                    continue
            
            # Handle ending
            if response.get("ending"):
                delete_game_id()
                continue
                
        except ConnectionError as e:
            print(str(e))
            sys.exit(1)
        except ValueError as e:
            if "Game not found" in str(e):
                print("\n[ No active game. Starting new game... ]")
                try:
                    response = make_post_request("/api/games", url=args.url)
                    game_id = response["game_id"]
                    write_game_id(game_id)
                    if response.get("response"):
                        print_pictures(response["response"].get("pictures", []))
                        print(f"\n{response['response']['text']}")
                except ConnectionError as ce:
                    print(str(ce))
                    sys.exit(1)
            else:
                print(f"Error: {e}")


if __name__ == "__main__":
    main()
