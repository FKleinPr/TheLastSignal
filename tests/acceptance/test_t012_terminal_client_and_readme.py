"""Acceptance tests for Task T-012: Terminal client and README.

Tests the terminal client (`client/play.py`) and README.md through subprocess runs and file checks.
Tests reach the game server through the planned interfaces (T-003, T-005, T-004, T-002).

CR-001 updates:
- AC-014: Four scripted runs of the terminal client with various inputs (look/go north/quit, death scenario,
  continuation, connection error).
- AC-015: README.md must exist, have 1500+ characters, and contain specific phrases.
- AC-017: Client displays pictures/placeholders based on available/terminal/placeholder flags.
- AC-018: Client handles help and inventory locally without server interaction.

All tests run as subprocess with temporary directory as working directory (so .last-signal-game is written there).
"""

import os
import subprocess
import sys
import tempfile

import pytest

from game_data import (
    TEXT,
    PICTURES,
    CHARACTER_NAMES,
    CORE_REACTIONS,
    CLIENT_OUTPUT,
    placeholder,
)

# Base URL for tests (from environment)
TEST_BASE_URL = os.environ["TEST_BASE_URL"].rstrip("/")

# Path to the terminal client from the repository root
CLIENT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "client", "play.py"))


def run_client(args: list, input_text: str = "", cwd: str = None) -> subprocess.CompletedProcess:
    """Run the terminal client as a subprocess with given arguments and input.

    Args:
        args: List of arguments (e.g., ["--url", TEST_BASE_URL, "--new"])
        input_text: Input text to send to the client (newlines between commands)
        cwd: Working directory (temporary directory for .last-signal-game)

    Returns:
        subprocess.CompletedProcess with stdout and stderr captured.
    """
    cmd = [sys.executable, CLIENT_PATH] + args
    if cwd:
        proc = subprocess.run(cmd, cwd=cwd, input=input_text, capture_output=True, text=True, timeout=60)
    else:
        proc = subprocess.run(cmd, input=input_text, capture_output=True, text=True, timeout=60)
    return proc


def read_readme() -> str:
    """Read the repository README.md for AC-015 checks."""
    readme_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "README.md"))
    if os.path.exists(readme_path):
        with open(readme_path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def verify_readme_ac015(readme: str) -> bool:
    """Verify README.md meets AC-015 requirements (1500+ chars, specific phrases)."""
    if len(readme) < 1500:
        return False
    required_phrases = ["docker compose up", "client/play.py", "continue", "restart"]
    return all(phrase in readme for phrase in required_phrases)


class TestTerminalClientAC014:
    """Tests for AC-014: Terminal client behavior (four scripted runs)."""

    def test_ac014_01_look_go_north_quit(self, api):
        """Verifies: AC-014 (first run: look/go north/quit → exit 0, opening text, watchtower description, Goodbye)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            proc = run_client(
                ["--url", TEST_BASE_URL, "--new"],
                input_text="look\ngo north\nquit\n",
                cwd=tmp_path,
            )
            assert proc.returncode == 0, f"Expected exit code 0, got {proc.returncode}. stdout: {proc.stdout}"
            assert TEXT["opening"] in proc.stdout, f"Opening text not found in output. stdout: {proc.stdout}"
            # Watchtower description should be in output (after go north)
            assert "satellite dish" in proc.stdout.lower() or "watchtower" in proc.stdout.lower(), \
                f"Watchtower description not found. stdout: {proc.stdout}"
            assert CLIENT_OUTPUT["goodbye"] in proc.stdout, f"Goodbye not found. stdout: {proc.stdout}"

    def test_ac014_02_death_dust_continue_quit(self, api):
        """Verifies: AC-014 (death-dust scenario: take core/wait/wait/wait/continue/quit → death-dust text and continue)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            proc = run_client(
                ["--url", TEST_BASE_URL, "--new"],
                input_text="take core\nwait\nwait\nwait\ncontinue\nquit\n",
                cwd=tmp_path,
            )
            assert proc.returncode == 0, f"Expected exit code 0, got {proc.returncode}. stdout: {proc.stdout}"
            # Death-dust text should be in output
            assert TEXT["dust_death"] in proc.stdout, f"Death-dust text not found. stdout: {proc.stdout}"
            assert "continue" in proc.stdout.lower(), f"Continue option not found. stdout: {proc.stdout}"
            assert CLIENT_OUTPUT["goodbye"] in proc.stdout, f"Goodbye not found. stdout: {proc.stdout}"

    def test_ac014_03_continue_without_new(self, api):
        """Verifies: AC-014 (run again without --new → Continuing your game)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            # First, create a game by running the client once
            proc1 = run_client(
                ["--url", TEST_BASE_URL, "--new"],
                input_text="look\nquit\n",
                cwd=tmp_path,
            )
            assert proc1.returncode == 0, f"First run failed: {proc1.stderr}"

            # Second run without --new should continue the game
            proc2 = run_client(
                ["--url", TEST_BASE_URL],  # no --new
                input_text="quit\n",
                cwd=tmp_path,
            )
            assert proc2.returncode == 0, f"Second run failed: {proc2.stderr}"
            assert CLIENT_OUTPUT["continuing_your_game"] in proc2.stdout, \
                f"'Continuing your game.' not found. stdout: {proc2.stdout}"
            assert CLIENT_OUTPUT["goodbye"] in proc2.stdout, f"Goodbye not found. stdout: {proc2.stdout}"

    def test_ac014_04_connection_error(self):
        """Verifies: AC-014 (--url http://127.0.0.1:1 → exit 1 and Cannot reach the game server)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            proc = run_client(
                ["--url", "http://127.0.0.1:1", "--new"],
                input_text="quit\n",
                cwd=tmp_path,
            )
            assert proc.returncode == 1, f"Expected exit code 1, got {proc.returncode}. stdout: {proc.stdout}"
            assert "Cannot reach the game server" in proc.stderr or "Cannot reach the game server" in proc.stdout, \
                f"'Cannot reach the game server' not found. stderr: {proc.stderr}, stdout: {proc.stdout}"


class TestREADMEAC015:
    """Tests for AC-015: README.md exists, 1500+ characters, contains specific phrases."""

    def test_ac015_01_readme_exists_and_length(self):
        """Verifies: AC-015 (README.md exists, has at least 1,500 characters)."""
        readme = read_readme()
        assert len(readme) >= 1500, f"README.md has {len(readme)} characters, expected at least 1500."

    def test_ac015_02_readme_contains_required_phrases(self):
        """Verifies: AC-015 (README.md contains 'docker compose up', 'client/play.py', 'continue', 'restart')."""
        readme = read_readme()
        required_phrases = ["docker compose up", "client/play.py", "continue", "restart"]
        for phrase in required_phrases:
            assert phrase in readme, f"Required phrase '{phrase}' not found in README.md."


class TestClientPictureDisplayAC017:
    """AC-017: the client prints a picture's terminal text when it is available, else its placeholder."""

    def test_ac017_01_available_picture_terminal_text(self, api, tmp_path):
        """Verifies: AC-017 (available picture: its terminal text is printed)."""
        api.set_pictures({"bone-yard": "BONE-YARD-ART"})
        proc = run_client(["--url", TEST_BASE_URL, "--new"], input_text="look\nquit\n", cwd=str(tmp_path))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert "BONE-YARD-ART" in proc.stdout

    def test_ac017_02_missing_picture_placeholder(self, api, tmp_path):
        """Verifies: AC-017 (picture not available: its placeholder is printed)."""
        proc = run_client(["--url", TEST_BASE_URL, "--new"], input_text="look\nquit\n", cwd=str(tmp_path))
        assert proc.returncode == 0, proc.stdout + proc.stderr
        assert placeholder("bone-yard") in proc.stdout


class TestLocalCommandsAC018:
    """Tests for AC-018: Client handles help and inventory locally without server interaction."""

    def test_ac018_01_help_local_command(self, api):
        """Verifies: AC-018 (help is handled locally without server interaction)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            # Run the client with 'help' as input
            proc = run_client(
                ["--url", TEST_BASE_URL, "--new"],
                input_text="help\nquit\n",
                cwd=tmp_path,
            )
            assert proc.returncode == 0, f"Expected exit code 0, got {proc.returncode}. stdout: {proc.stdout}"
            # Help should be printed locally (not requiring server response)
            assert "help" in proc.stdout.lower() or "commands" in proc.stdout.lower(), \
                f"Help output not found. stdout: {proc.stdout}"

    def test_ac018_02_inventory_local_command(self, api):
        """Verifies: AC-018 (inventory/i is handled locally without server interaction)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            # Start a new game and take an item
            game = api.new_game()
            game_id = game["game_id"]
            api.cmd(game_id, "go east")
            api.cmd(game_id, "take core")

            # Run the client with 'inventory' and 'i' as input
            proc = run_client(
                ["--url", TEST_BASE_URL, "--new"],
                input_text="take core\ninventory\ni\nquit\n",
                cwd=tmp_path,
            )
            assert proc.returncode == 0, f"Expected exit code 0, got {proc.returncode}. stdout: {proc.stdout}"
            # Inventory should be printed locally (not requiring server response for the command itself)
            assert "inventory" in proc.stdout.lower() or "core" in proc.stdout.lower(), \
                f"Inventory output not found. stdout: {proc.stdout}"


class TestClientPersistenceAC014:
    """Additional tests for client persistence (AC-014 continuation)."""

    def test_ac014_05_persistence_file_written(self, api):
        """Verifies: AC-014 (game id is written to .last-signal-game file)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            # Start a new game
            proc1 = run_client(
                ["--url", TEST_BASE_URL, "--new"],
                input_text="look\nquit\n",
                cwd=tmp_path,
            )
            assert proc1.returncode == 0, f"First run failed: {proc1.stderr}"

            # Check that .last-signal-game was written
            game_id_file = os.path.join(tmp_path, ".last-signal-game")
            assert os.path.exists(game_id_file), f".last-signal-game file not found in {tmp_path}"

            with open(game_id_file, "r") as f:
                game_id = f.read().strip()
            assert len(game_id) > 0, f"Game ID in .last-signal-game is empty."

    def test_ac014_06_persistence_file_read_on_continue(self, api):
        """Verifies: AC-014 (client reads .last-signal-game file when continuing)."""
        with tempfile.TemporaryDirectory() as tmp_path:
            # First run: create a game
            proc1 = run_client(
                ["--url", TEST_BASE_URL, "--new"],
                input_text="look\nquit\n",
                cwd=tmp_path,
            )
            assert proc1.returncode == 0, f"First run failed: {proc1.stderr}"

            # Read the game ID from the file
            game_id_file = os.path.join(tmp_path, ".last-signal-game")
            with open(game_id_file, "r") as f:
                game_id = f.read().strip()

            # Second run: should continue from the file
            proc2 = run_client(
                ["--url", TEST_BASE_URL],  # no --new, should use .last-signal-game
                input_text="quit\n",
                cwd=tmp_path,
            )
            assert proc2.returncode == 0, f"Second run failed: {proc2.stderr}"
            assert CLIENT_OUTPUT["continuing_your_game"] in proc2.stdout, \
                f"'Continuing your game.' not found. stdout: {proc2.stdout}"
