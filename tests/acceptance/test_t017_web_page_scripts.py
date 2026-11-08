"""Acceptance tests for task T-017: Web page scripts (CR-002, CR-003, CR-004).

There is no browser in the CI: the page is tested through HTTP (GET / and GET /web/...) and the text of its files;
the JavaScript is not executed (design AD-034).

Verifies: AC-020, AC-030, AC-031, AC-032, AC-037
"""
import json
import re

from game_data import WEB_PAGE_CONTENT, EXPECTED_RENDER_JS_SIZES


WEB_FILES = ["index.html", "style.css", "js/api.js", "js/state.js", "js/render.js", "js/main.js",
             "chapters/index.json", "chapters/act1/chapter.json"]
CODE_FILES = ["index.html", "js/api.js", "js/state.js", "js/render.js", "js/main.js"]


def _file(api, path: str) -> str:
    r = api.get_web_file_raw(path)
    assert r.status_code == 200, f"GET /web/{path}: {r.status_code}"
    return r.text


def test_index_page(api):
    """Verifies: AC-020 (GET /: 200 text/html with id="story", id="command", id="new-game" and type="module")."""
    r = api.get_index_raw()
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/html")
    for element_id in WEB_PAGE_CONTENT["required_ids"]:
        assert f'id="{element_id}"' in r.text, f'id="{element_id}" missing'
    assert 'type="module"' in r.text


def test_scripts_are_javascript_and_name_the_api(api):
    """Verifies: AC-020 (api.js is text/javascript with /api/games; state.js has last-signal-game; render.js has
    /api/pictures/ and textContent, no innerHTML)."""
    r = api.get_web_file_raw("js/api.js")
    assert r.status_code == 200
    assert r.headers.get("content-type", "").startswith("text/javascript")
    assert "/api/games" in r.text
    assert "last-signal-game" in _file(api, "js/state.js")
    render = _file(api, "js/render.js")
    assert "/api/pictures/" in render
    assert "textContent" in render
    assert "innerHTML" not in render


def test_api_js_uses_post(api):
    """Verifies: AC-030 (web/js/api.js sends a command with "POST"; no request to /commands without a method)."""
    content = _file(api, "js/api.js")
    calls = [m.start() for m in re.finditer(r"/commands", content)]
    assert calls, "api.js does not send commands to /api/games/{id}/commands"
    for pos in calls:
        window = content[pos:pos + 300]  # the call that uses this URL, with its method
        assert "POST" in window, f"a request to /commands without POST: {window[:120]!r}"

def test_files_are_small_and_local(api):
    """Verifies: AC-020 (no file under web/ contains http:// or https://, each has at most 250 lines)."""
    for path in WEB_FILES:
        text = _file(api, path)
        for url in WEB_PAGE_CONTENT["forbidden_urls"]:
            assert url not in text, f"{path} contains {url}"
        assert len(text.splitlines()) <= WEB_PAGE_CONTENT["max_lines_per_file"], f"{path} is too long"


def test_chapter_folder(api):
    """Verifies: AC-020, AC-031 (index.json names act1; chapter.json holds title, ending_title and commands with
    pick lock; no "Act I" or "ACT I" in index.html or the scripts)."""
    assert json.loads(_file(api, "chapters/index.json"))["current"] == "act1"
    chapter = json.loads(_file(api, "chapters/act1/chapter.json"))
    assert chapter["title"] == "The Last Signal: Act I"
    assert chapter["ending_title"] == "ACT I COMPLETE"
    assert "pick lock" in json.dumps(chapter["commands"])
    for path in CODE_FILES:
        text = _file(api, path)
        # AC-031: No "Act I" or "ACT I" in any case
        assert "Act I" not in text, f"{path} contains chapter text 'Act I'"
        assert "ACT I" not in text, f"{path} contains chapter text 'ACT I'"


def test_paths_outside_web_and_missing_files_are_404(api):
    """Verifies: AC-020 (GET /web/../src/main.py, /web/%2e%2e/src/main.py and /web/no-such-file.js: 404)."""
    for path in ["../src/main.py", "%2e%2e/src/main.py", "no-such-file.js"]:
        r = api.get_web_file_raw(path)
        assert r.status_code == 404, f"/web/{path}: {r.status_code}"


def test_pictures_js_removed(api):
    """Verifies: AC-032 (GET /web/js/pictures.js returns 404)."""
    r = api.get_web_file_raw("js/pictures.js")
    assert r.status_code == 404, f"GET /web/js/pictures.js should return 404, got {r.status_code}"

def test_render_js_dimensions(api):
    """Verifies: AC-037 (web/js/render.js sets width and height for pictures: 640, 360, 128, 64)."""
    render = _file(api, "js/render.js")
    for size in EXPECTED_RENDER_JS_SIZES:
        assert size in render, f"render.js should contain '{size}'"
