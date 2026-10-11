"""Database schema for The Last Signal game server.

Creates SQLite tables for games and turn_log. Derives file path from DATABASE_URL.
"""

import os
import sqlite3

DB_URL = os.getenv("DATABASE_URL", "sqlite:////data/game.db")
DB_PATH = DB_URL[len("sqlite:///"):] if DB_URL.startswith("sqlite:///") else DB_URL

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


def init_db():
    """Initialize the database tables."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Games table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS games (
            game_id TEXT PRIMARY KEY,
            player_location TEXT NOT NULL,
            inventory TEXT NOT NULL,
            flags TEXT NOT NULL,
            relationships TEXT NOT NULL,
            clues TEXT NOT NULL,
            events TEXT NOT NULL,
            turns INTEGER NOT NULL,
            dead INTEGER NOT NULL,
            ending TEXT,
            has_checkpoint INTEGER NOT NULL,
            has_save INTEGER NOT NULL,
            last_checkpoint_id TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    """)
    
    # Turn log table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS turn_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            game_id TEXT NOT NULL,
            turn INTEGER NOT NULL,
            input TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (game_id) REFERENCES games(game_id)
        )
    """)
    
    # Checkpoints table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS checkpoints (
            id TEXT PRIMARY KEY,
            game_id TEXT NOT NULL,
            state_snapshot TEXT NOT NULL,
            created_at TEXT NOT NULL,
            FOREIGN KEY (game_id) REFERENCES games(game_id)
        )
    """)
    
    conn.commit()
    conn.close()


def get_connection():
    """Get a new database connection."""
    return sqlite3.connect(DB_PATH)
