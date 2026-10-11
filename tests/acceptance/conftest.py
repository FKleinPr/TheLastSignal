"""Shared harness for The Last Signal acceptance tests (rewritten after test review 1).

Tests talk to the game only through the `api` fixture; the base URL comes from TEST_BASE_URL. Every test starts
with POST /api/test/reset (autouse fixture): it deletes all games and resets both stubs, so the stub model has no
script (it answers {"verb": null}) and the stub generator holds no pictures. Game facts (texts, routes, the
picture list) are in game_data.py.
"""
import os

import httpx
import pytest

TEST_BASE_URL = os.getenv("TEST_BASE_URL", "").rstrip("/")
if not TEST_BASE_URL:
    raise RuntimeError("TEST_BASE_URL is not set (expected e.g. http://127.0.0.1:18003)")


class Api:
    """Client for the planned interfaces. Methods ending in _raw return the unchecked httpx.Response; the others
    assert the success status and return the JSON body."""

    def __init__(self, client: httpx.Client):
        self.client = client

    def _ok(self, r: httpx.Response, status: int = 200):
        assert r.status_code == status, f"{r.request.method} {r.request.url}: {r.status_code} {r.text}"
        return r.json()

    # Games and commands (T-003, T-005)
    def new_game_raw(self) -> httpx.Response:
        return self.client.post(f"{TEST_BASE_URL}/api/games")

    def new_game(self) -> dict:
        return self._ok(self.new_game_raw(), 201)

    def state_raw(self, game_id: str) -> httpx.Response:
        return self.client.get(f"{TEST_BASE_URL}/api/games/{game_id}")

    def state(self, game_id: str) -> dict:
        return self._ok(self.state_raw(game_id))

    def command_raw(self, game_id: str, payload: dict) -> httpx.Response:
        return self.client.post(f"{TEST_BASE_URL}/api/games/{game_id}/commands", json=payload)

    def cmd(self, game_id: str, text: str) -> dict:
        return self._ok(self.command_raw(game_id, {"text": text}))

    def run(self, game_id: str, commands: list) -> list:
        return [self.cmd(game_id, text) for text in commands]

    # Picture list (T-004)
    def pictures(self) -> list:
        return self._ok(self.client.get(f"{TEST_BASE_URL}/api/pictures"))

    # Test endpoints (T-002)
    def reset_raw(self) -> httpx.Response:
        return self.client.post(f"{TEST_BASE_URL}/api/test/reset")

    def script_llm_raw(self, contents: list) -> httpx.Response:
        return self.client.post(f"{TEST_BASE_URL}/api/test/llm-script", json={"responses": contents})

    def script_llm(self, contents: list) -> None:
        assert self.script_llm_raw(contents).status_code == 200

    def llm_down_raw(self) -> httpx.Response:
        return self.client.post(f"{TEST_BASE_URL}/api/test/llm-script", json={"mode": "down"})

    def llm_down(self) -> None:
        assert self.llm_down_raw().status_code == 200

    def llm_requests_raw(self) -> httpx.Response:
        return self.client.get(f"{TEST_BASE_URL}/api/test/llm-requests")

    def llm_requests(self) -> list:
        return self._ok(self.llm_requests_raw())

    def set_pictures_raw(self, pictures: dict) -> httpx.Response:
        return self.client.post(f"{TEST_BASE_URL}/api/test/pictures", json={"pictures": pictures})

    def set_pictures(self, pictures: dict) -> None:
        assert self.set_pictures_raw(pictures).status_code == 200

    def generator_down_raw(self) -> httpx.Response:
        return self.client.post(f"{TEST_BASE_URL}/api/test/pictures", json={"mode": "down"})

    def generator_down(self) -> None:
        assert self.generator_down_raw().status_code == 200


@pytest.fixture(scope="session")
def http_client():
    with httpx.Client(timeout=20.0) as client:
        yield client


@pytest.fixture(scope="session")
def api(http_client) -> Api:
    return Api(http_client)


@pytest.fixture(autouse=True)
def reset_state(api):
    r = api.reset_raw()
    assert r.status_code == 200, f"POST /api/test/reset: {r.status_code} {r.text}"
    yield


@pytest.fixture
def game(api) -> dict:
    """A new game: {"game_id": ..., "response": <Response of POST /api/games>}."""
    return api.new_game()
