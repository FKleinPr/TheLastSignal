"""Game facts for the acceptance tests: spec section 9, design 6.7/6.8 and the decisions of test review 1.
Tests import texts, routes and the picture list from here instead of writing them out.

CR-002 updates:
- Added CHARACTER_NAMES mapping for synonyms (e.g., `jex`, `merchant`).
- Added CORE_REACTIONS with specific reaction texts for the core choice (Awakeners, Silencers, Flee).
- Added CLIENT_OUTPUT for client-generated strings (Goodbye, Continuing your game, etc.).
- Updated TEXT to include core reaction texts and client output strings.
- Added WEB_PAGE_CONTENT expectations for AC-020 checks.
- Added STUB_MODEL_SCRIPTING examples for AC-023 checks.

CR-003 updates:
- Added EXITS_LIST to verify the system message contains exits (e.g., `exit north -> watchtower`).
- Added VALID_JSON_EXAMPLE to verify the system message contains valid JSON with double quotes.
- Added MODEL_MAPPING_LOGIC to verify name-to-ID mapping for `go` and `take` commands.
- Added INVALID_MODEL_RESPONSE to verify fallback to rule-based parser.

CR-004 updates:
- Added EXPECTED_SYSTEM_MESSAGE_INSTRUCTIONS to verify the exact system message text sent to the model.
- Added EXPECTED_RENDER_JS_SIZES to verify web/js/render.js sets width/height for pictures (640, 360, 128, 64).
- Updated STUB_MODEL_SCRIPTING to include the new answer shapes accepted by the game:
  - `talk` and `ask`: character in `object` or `target`.
  - `go`: direction or destination id in `object` or `target`.
  - Name mapping (e.g., `signal` -> `core`).
- Updated MODEL_MAPPING_LOGIC to reflect the specific mappings required by CR-004.
"""

LOCATIONS = ["bone-yard", "watchtower", "scrap-market", "edge-of-town", "archives", "sanctum",
             "control-center", "deep-ribs"]
TALKABLE = ["priest-voa", "child-echo", "merchant-jex", "archivist-lira", "silencer-leader"]

# Spec 9.11 as (from, direction, to). sanctum east is blocked until gate-locked is solved.
EXITS = [
    ("bone-yard", "north", "watchtower"), ("watchtower", "south", "bone-yard"),
    ("bone-yard", "east", "scrap-market"), ("scrap-market", "west", "bone-yard"),
    ("scrap-market", "north", "edge-of-town"), ("edge-of-town", "south", "scrap-market"),
    ("watchtower", "east", "archives"), ("archives", "west", "watchtower"),
    ("archives", "south", "sanctum"), ("sanctum", "north", "archives"),
    ("sanctum", "east", "control-center"), ("control-center", "west", "sanctum"),
    ("control-center", "north", "deep-ribs"), ("deep-ribs", "south", "control-center"),
]

# Spec 9.10: name -> (type, size, description); entity_id equals the name.
PICTURES = {
    "bone-yard": ("scene", "160x90", "Red sand rusted ship ribs with holy signs painted."),
    "watchtower": ("scene", "160x90", "Satellite dish painted like a holy sign."),
    "scrap-market": ("scene", "160x90", "Piles of coolant bottles and scrap metal."),
    "archives": ("scene", "160x90", "Leather-bound data-slates glowing in dim light."),
    "sanctum": ("scene", "160x90", "Awakeners hiding in ribs, shadows and ozone."),
    "control-center": ("scene", "160x90", "Silencers with locked door and humming."),
    "edge-of-town": ("scene", "160x90", "Broken fence and escape route."),
    "deep-ribs": ("scene", "160x90", "Inside hull, dark, humming air, blue light."),
    "player": ("character", "32x32", "Ordinary individual with core in hand."),
    "priest-voa": ("character", "32x32", "Guard with robe, touches hull."),
    "child-echo": ("character", "32x32",
                   "Small child with closed eyes, ear pressed to red sand, ragged orange scarf."),
    "merchant-jex": ("character", "32x32", "Trader smelling items, dark clothes."),
    "archivist-lira": ("character", "32x32", "Scholar reading glowing slates."),
    "silencer-leader": ("character", "32x32", "Silencer in dark uniform, hand on weapon."),
    "core": ("item", "16x16", "Glowing metal object, signal source."),
    "key": ("tool", "16x16", "Metal key for locked door."),
    "data-slate": ("item", "16x16", "Leather-bound book with glowing text."),
    "lock-pick": ("tool", "16x16", "Bent antenna wire, works as pick."),
    "coolant-bottle": ("item", "16x16", "Bottle of blue liquid, god's blood."),
}

# Character names/synonyms mapping (CR-001, FR-030).
# Updated per review: correct order and additions (local, trader, etc.)
CHARACTER_NAMES = {
    "priest-voa": ["priest-voa", "priest", "voa"],
    "child-echo": ["child-echo", "echo", "child", "local"],
    "merchant-jex": ["merchant-jex", "jex", "merchant", "trader", "local"],
    "archivist-lira": ["archivist-lira", "archivist", "lira"],
    "silencer-leader": ["silencer-leader", "silencer", "leader"],
}

# Core choice reaction texts (CR-001, FR-032, Spec 9.6).
CORE_REACTIONS = {
    "awakeners": "Lira's hands shake as she takes the core. \"It's waking. The town won't survive this - get to the edge of town, or into the deep ribs. Now.\"",
    "silencers": "The Silencer-Leader snatches the core. \"Now get out of my sight. When the ribs start moving, be somewhere safe - the deep ribs, or beyond the fence.\"",
    "flee": "The fence creaks behind you. The hum rises - the ship knows you are leaving. Stay here, and in a few moments you're gone.",
}

# Client output strings (CR-001, FR-025, FR-026, FR-027, FR-028).
CLIENT_OUTPUT = {
    "continuing_your_game": "Continuing your game.",
    "goodbye": "Goodbye.",
    "cannot_reach": "Cannot reach the game server at {url}.",
    "act_i_complete": "ACT I COMPLETE",
}

TEXT = {
    "opening": "The red sand presses against your boots.",
    "signal": "The ship has woken up, and it knows you're here.",
    "impossible": "That's not happening here. Try something less ambitious.",
    "unknown": "I'm not sure what you're trying to do.",
    "ambiguous": "Which",
    "blocked": "locked",
    "dust_warning": "You coughed. The sand is getting thicker around your boots.",
    "dust_death": "You are now part of the bone-yard's collection.",
    "humming_warning": "The hum is getting louder. Your ears are bleeding.",
    "humming_death": "The ship decided you were cargo. You did not fit.",
    "faction_warning": "Silencer-Leader is looking at you.",
    "faction_death": "Trust is a luxury this town cannot afford.",
    "awakening_warning": "The ribs are moving. You can hear them grinding against each other.",
    "awakening_death": "The ship's awakening finished without you.",
    "priest_always": "The hull breathes when you stand still.",
    "priest_core": "The ship knows you have it.",
    "child_always": "It sings in the red dust.",
    "child_core": "The ship sings when you hold it. It wants to wake up.",
    "jex_always": "Coolant tastes like the sky.",
    "lira_always": "The books say they flew.",
    "lira_core": "The Awakeners will help you.",
    "silencer_always": "Control is the only path to survival.",
    "ending-awakeners": "The Awakeners took the core and woke the ship.",
    "ending-silencers": "The Silencers took the core and controlled the ship.",
    "ending-escape": "You ran to the edge of town and fled before the ship destroyed everything.",
    # Core choice reaction texts (CR-001, Spec 9.6)
    "awakeners_reaction": CORE_REACTIONS["awakeners"],
    "silencers_reaction": CORE_REACTIONS["silencers"],
    "flee_reaction": CORE_REACTIONS["flee"],
}

DEAD_CHOICES = ["continue", "restart"]

# Command lists from a new game. Where each one ends is in the comment.
ROUTES = {
    "to_sanctum": ["go north", "go east", "go south"],                     # sanctum, door locked
    "to_scrap_market": ["go east"],                                       # scrap-market
    "to_archives": ["go north", "go east"],                               # archives
    "gate_by_pick": ["go north", "take lock-pick", "go east", "go south", "pick lock"],  # sanctum, door open
    "gate_by_key": ["take core", "go north", "go east", "go south", "show core to priest-voa",
                    "go north", "go west", "go south", "go east", "give coolant-bottle to merchant-jex",
                    "go west", "go north", "go east", "go south", "use key on door"],  # sanctum, door open
    "death_dust": ["take core", "wait", "wait", "wait"],                  # [-2] warning, [-1] dead
    "death_humming": ["go north", "take lock-pick", "go east", "go south", "pick lock", "go east",
                      "go north", "wait", "wait"],                        # [-3] enters with warning, [-1] dead
    "death_faction": ["take core", "go north", "take lock-pick", "go east", "go south", "pick lock",
                      "go east", "wait", "wait"],                         # [-2] warning, [-1] dead
    "death_awakening": ["take core", "go north", "go east", "give core to archivist-lira",
                        "wait", "wait", "wait"],                          # [-2] warning, [-1] dead
    "ending_awakeners": ["take core", "go north", "take lock-pick", "go east", "go south", "pick lock",
                         "go north", "give core to archivist-lira", "go south", "go east", "go north"],
    "ending_silencers": ["take core", "go north", "take lock-pick", "go east", "go south", "pick lock",
                         "go east", "give core to silencer-leader", "wait", "wait", "go north"],
    "ending_escape": ["take core", "go east", "go north", "wait", "wait", "wait"],
}

# Web page content expectations (CR-002, AC-020, AC-037).
WEB_PAGE_CONTENT = {
    "required_ids": ["story", "command", "new-game"],
    "required_texts": ["The Last Signal: Act I", "ACT I COMPLETE"],
    "required_api_paths": ["/api/games", "/api/pictures/"],
    "required_local_storage": "last-signal-game",
    "forbidden_urls": ["http://", "https://"],
    "max_lines_per_file": 250,
}

# Expected system message instructions (CR-004, AC-033).
EXPECTED_SYSTEM_MESSAGE_INSTRUCTIONS = "Use only ids from the list below"  # AC-033 checks this part only

# Expected render.js sizes (CR-004, AC-037).
# The width and height strings that must appear in web/js/render.js.
EXPECTED_RENDER_JS_SIZES = ["640", "360", "128", "64"]

# Stub model scripting examples (CR-002, CR-003, CR-004, AC-022, AC-023, AC-026, AC-027, AC-028, AC-029, AC-033, AC-034, AC-035, AC-036).
# These Python dicts are serialized to JSON and sent to the stub model, which returns them to the game server.
STUB_MODEL_SCRIPTING = {
    "default_response": {"verb": None},
    "scripted_take_core": {"verb": "take", "object": "core", "target": None},
    "scripted_give_core": {"verb": "give", "object": "core", "target": "archivist-lira"},
    # CR-003: Valid JSON example with double quotes
    "valid_json_example": '{"verb": "take", "object": "core", "target": null}',
    # CR-003: Exits list example
    "exits_list_example": "exit north -> watchtower\nexit east -> scrap-market",
    # CR-003: Model response mapping for `go`
    "go_to_scrap_market": {"verb": "go", "object": "scrap-market", "target": None},
    # CR-003/CR-004: Model response mapping for `take` with name
    "take_metal": {"verb": "take", "object": "metal", "target": None},
    # CR-003/CR-004: Invalid model response (name not present)
    "invalid_response": {"verb": "take", "object": "shiny thing", "target": None},
    # CR-004: Name mapping (signal -> core)
    "take_signal": {"verb": "take", "object": "signal", "target": None},
    # CR-004: Character in `object` for `talk`
    "talk_merchant_in_object": {"verb": "talk", "object": "merchant-jex", "target": None},
    # CR-004: Direction/destination in `target` for `go`
    "go_bone_yard_in_target": {"verb": "go", "object": None, "target": "bone-yard"},
}

# Commands to verify model request content (AC-022, AC-026).
MODEL_VERBS_TO_CHECK = ["take", "give", "talk"]
MODEL_ENTITY_ID_TO_CHECK = "core"
# CR-003: Expected exits in system message
EXPECTED_EXITS = [
    "exit north -> watchtower",
    "exit east -> scrap-market",
]
# CR-003: Expected valid JSON structure in system message
EXPECTED_JSON_STRUCTURE = '"verb"'

# Mapping logic for `go` and `take` (CR-003, CR-004).
# `go` object can be a direction or a location ID; both map to the exit's direction.
# `take` object can be a name or id; maps to the entity's id.
# CR-004: `talk` and `ask` accept character in `object` or `target`.
# CR-004: `go` accepts direction/destination in `object` or `target`.
MODEL_MAPPING_LOGIC = {
    "go_directions": ["north", "south", "east", "west", "n", "s", "e", "w"],
    "go_location_ids": ["watchtower", "scrap-market", "edge-of-town", "archives", "sanctum", "control-center", "deep-ribs"],
    "go_destination_ids": ["bone-yard", "watchtower", "scrap-market", "edge-of-town", "archives", "sanctum", "control-center", "deep-ribs"],
    "take_names": ["core", "metal", "glinting metal", "signal"],
    "take_ids": ["core"],
    "talk_targets": ["merchant-jex", "archivist-lira", "priest-voa", "silencer-leader", "child-echo"],
}

# Invalid model response (CR-003, CR-004).
# When the model returns an object that is not present, the game ignores the response and falls back to the rule-based parser.
INVALID_MODEL_RESPONSE = {
    "verb": "take",
    "object": "shiny thing",
    "target": None,
}

def placeholder(name: str) -> str:
    return f"[ picture: {name} ]"
