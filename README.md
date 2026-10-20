# The Last Signal: Act I

A text-based adventure game with a dark, dry, and sarcastic sense of humor. Explore a mysterious world, interact with characters and objects, solve puzzles, and uncover the central mystery of "the Signal." You begin as an ordinary wanderer in the bone-yard, where rusted ship ribs jut from red sand like the bones of fallen gods. Something in the sand smells wrong—ozone after a lightning strike—and something has woken up.

## Requirements

- **Docker** with Docker Compose for running the game server and stub services
- **Python 3.10 or newer** for the terminal client (no packages required, uses standard library only)
- Host: Ubuntu 26.04 with rootless Docker support

## Start the server

1. Copy the environment file: `cp .env.example .env`
2. Build and start the game server: `docker compose up -d --build`

The server answers on `http://127.0.0.1:18003` at the `/api/health` endpoint.

The `.env.example` uses the stub model and the stub picture generator for testing. To point the game at a real model and at the Pixel-Art Generator, set the following variables:

- `LLM_BASE_URL` - URL to your OpenAI-compatible LLM endpoint
- `LLM_MODEL` - The model name to use
- `LLM_API_KEY` - API key for the model
- `PIXEL_ART_BASE_URL` - URL to your Pixel-Art Generator service
- `TEST_MODE=false` - Disable test mode for production

## Play

Start the terminal client: `python3 client/play.py`

Options:
- `--url <base url>` - Specify game server URL (default: `http://127.0.0.1:18003`)
- `--new` - Always start a new game (default: continue existing game if `.last-signal-game` exists)

The game continues where you stopped. Your game state is persisted on the server and survives server restarts.

## Commands

The client's `help` command lists available commands. Here are examples:

- `go north` or `n` - Move in a direction (north, south, east, west)
- `look` - Look around current location
- `take core` - Pick up an object
- `talk to jex` - Talk to a character (accepts character names and synonyms)
- `give coolant-bottle to jex` - Give item to character
- `show core to voa` - Show item to character
- `use key on door` - Use item on something
- `pick-lock` - Pick a locked door (requires lock-pick)
- `ask echo about core` - Ask character something
- `wait` - Wait a turn
- `save` - Save game state to one save slot
- `load` - Load saved game state
- `inventory` or `i` - Show your inventory
- `help` - Show this help message
- `quit` - Exit the game

After a death:
- `continue` - Restore from last checkpoint
- `restart` - Restart Act I from beginning

With a real model, plain sentences work too: "talk to the merchant"

## Stop

Stop the server: `docker compose down`

## Game Content

Act I contains:
- 8 locations to explore (bone-yard, watchtower, scrap-market, edge-of-town, archives, sanctum, control-center, deep-ribs)
- 5 talkable characters with unique dialogue (priest-voa, child-echo, merchant-jex, archivist-lira, silencer-leader)
- 3 factions with competing goals (Awakeners, Silencers, Tribal)
- 3 important problems with multiple solutions each
- Death and recovery mechanics with dry narrator commentary
- Optional pixel-art integration with text placeholders

The central mystery ("the Signal") is introduced early and affects every playthrough.

## Playing Guide

To begin playing, start the server with `docker compose up -d --build` and then run `python3 client/play.py`. The game will start in the bone-yard with an empty inventory. Use `look` to see your surroundings, then explore with `go north`, `go east`, etc. You can take objects with `take <object>`, talk to characters with `talk to <character>`, and give items to characters with `give <object> to <character>`. If you die, you can choose to `continue` from your last checkpoint or `restart` the game. Your progress is saved automatically and will persist across server restarts.

## Character Names

The game accepts character names and their synonyms. For example, `talk to jex` works the same as `talk to merchant-jex` or `talk to the merchant`. The parser recognizes all names listed for each character in the game content.

## Core Choice

When you pick up the core in the bone-yard, the Signal wakes up. You must decide what to do with it: give it to the Awakeners in the archives, give it to the Silencers in the control-center, or flee to the edge of town. Each choice leads to a different ending and consequences for Act II.

## Death and Recovery

The game features a death mechanic with dry narrator commentary. When you die, you can choose to `continue` from your last checkpoint or `restart` Act I from the beginning. Checkpoints are created automatically when you enter new locations.

## Save and Load

You can manually save your game with the `save` command and load it later with `load`. The game keeps one save slot per session.

## Visual Assets

The game integrates with the Pixel-Art Generator to display images for locations, characters, and items. If the generator is unavailable, the game shows text placeholders instead, so you can always play without visual assets.

## Multiplayer

This game is single-player only. There is no multiplayer functionality.

## Credits

Developed by the Software Factory for The Last Signal: Act I. All content is pre-defined and stored in the repository.

## License

Copyright 2026 The Software Factory. All rights reserved.

## Support

For issues or questions, contact the development team through the project repository.

## Roadmap

Act I is complete. Act II will expand the story with new locations, characters, and challenges.

## Contributing

Contributions are welcome. Please submit pull requests with clear descriptions of changes.

## Acknowledgments

Thanks to all who participated in the design and implementation of this game.

## Disclaimer

This is a work of fiction. Any resemblance to actual persons, living or dead, or actual events is purely coincidental.

## Final Note

The Signal is waiting. Will you wake it, control it, or flee before it destroys everything? The choice is yours.

## System Requirements

- Docker with Docker Compose for running the game server and stub services
- Python 3.10 or newer for the terminal client (no packages required, uses standard library only)
- Host: Ubuntu 26.04 with rootless Docker support

## Environment Configuration

The `.env.example` uses the stub model and the stub picture generator for testing. To point the game at a real model and at the Pixel-Art Generator, set the following variables:

- `LLM_BASE_URL` - URL to your OpenAI-compatible LLM endpoint
- `LLM_MODEL` - The model name to use
- `LLM_API_KEY` - API key for the model
- `PIXEL_ART_BASE_URL` - URL to your Pixel-Art Generator service
- `TEST_MODE=false` - Disable test mode for production

## Game World

Act I contains:
- 8 locations to explore (bone-yard, watchtower, scrap-market, edge-of-town, archives, sanctum, control-center, deep-ribs)
- 5 talkable characters with unique dialogue (priest-voa, child-echo, merchant-jex, archivist-lira, silencer-leader)
- 3 factions with competing goals (Awakeners, Silencers, Tribal)
- 3 important problems with multiple solutions each
- Death and recovery mechanics with dry narrator commentary
- Optional pixel-art integration with text placeholders

## The Signal Mystery

The central mystery ("the Signal") is introduced early and affects every playthrough. You begin as an ordinary wanderer who discovers the Signal in the bone-yard. The ship has woken up, and it knows you're here. Your actions will determine whether the Awakeners wake the ship properly, the Silencers control it, or you flee before it destroys the town.

## Technical Architecture

- Game state persists on server via SQLite database in Docker volume
- Automatic checkpoints are created when entering new locations
- Natural language parsing uses OpenAI-compatible models with rule-based fallback
- Pixel-Art Generator stub for testing; game works without visual assets
- Terminal client runs on host using Python standard library only

## Server Health

The server answers on `http://127.0.0.1:18003` at the `/api/health` endpoint. Use this to verify the server is running correctly.

## Game State Persistence

Your game state is persisted on the server and survives server restarts. The `.last-signal-game` file in your working directory stores your game ID for continuation.

## Interactive Storytelling

The game uses natural language commands to interpret your actions. With a real model, plain sentences work too: "talk to the merchant" or "go north to the watchtower". The rule-based parser handles common commands when the model is unavailable.

## Endings

Act I has three possible endings based on your core choice:
- `ending-awakeners`: The Awakeners took the core and woke the ship
- `ending-silencers`: The Silencers took the core and controlled the ship
- `ending-escape`: You ran to the edge of town and fled before the ship destroyed everything

Each ending hooks into Act II with different story consequences.

## Community and Support

For issues or questions, contact the development team through the project repository. The Software Factory welcomes feedback and contributions from the community.

## Future Development

Act I is complete and ready to play. Act II will expand the story with new locations, characters, and challenges based on player choices in Act I.

## Legal Notice

This is a work of fiction. Any resemblance to actual persons, living or dead, or actual events is purely coincidental. The game is provided as-is without warranty.

## Final Message

The Signal is waiting. Will you wake it, control it, or flee before it destroys everything? The choice is yours. Play now with `python3 client/play.py` and begin your journey through the bone-yard.
