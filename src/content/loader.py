"""YAML content loader for The Last Signal game server.

Loads and parses content/act1.yaml with all spec section 9 content.
Exports: load_content(), get_pictures()
"""

import os

# Fixed: Use absolute path that matches Dockerfile COPY instruction
# Dockerfile copies content/ to /app/content/, so we use that path directly
CONTENT_PATH = "/app/content/act1.yaml"


def _load_yaml(path: str) -> dict:
    """Load YAML file from path."""
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_content() -> dict:
    """Load all content from act1.yaml.
    
    Returns the full parsed content dict with start, locations, objects,
    characters, factions, rules, deaths, endings, clues, narrator, pictures.
    """
    return _load_yaml(CONTENT_PATH)


def get_pictures() -> list[dict]:
    """Get the picture list from content.
    
    Returns the pictures list from act1.yaml (Section 9.10).
    """
    content = load_content()
    return content.get("pictures", [])


def get_locations() -> dict:
    """Get locations dict from content."""
    content = load_content()
    return content.get("locations", {})


def get_objects() -> dict:
    """Get objects dict from content."""
    content = load_content()
    return content.get("objects", {})


def get_characters() -> dict:
    """Get characters dict from content."""
    content = load_content()
    return content.get("characters", {})


def get_factions() -> dict:
    """Get factions dict from content."""
    content = load_content()
    return content.get("factions", {})


def get_rules() -> list[dict]:
    """Get rules list from content."""
    content = load_content()
    return content.get("rules", [])


def get_deaths() -> dict:
    """Get deaths dict from content."""
    content = load_content()
    return content.get("deaths", {})


def get_endings() -> dict:
    """Get endings dict from content."""
    content = load_content()
    return content.get("endings", {})


def get_clues() -> dict:
    """Get clues dict from content."""
    content = load_content()
    return content.get("clues", {})


def get_narrator() -> dict:
    """Get narrator dict from content."""
    content = load_content()
    return content.get("narrator", {})


def get_start() -> dict:
    """Get start dict from content."""
    content = load_content()
    return content.get("start", {})


def get_timers() -> list[dict]:
    """Get timers list from content."""
    content = load_content()
    return content.get("timers", [])
