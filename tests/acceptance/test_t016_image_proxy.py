"""Acceptance tests for task T-016: Image proxy (CR-002 section 2, design 6.6).

GET /api/pictures/{name}/png: for a name in the picture list the game server fetches the generator's PNG and answers
its bytes as image/png; a name not in the list, a generator 404, or a generator that is down gives 404.

AC-025 (the stub generator's PNG endpoint) can only be reached through this proxy: the stub is internal.

Verifies: AC-021, AC-025
"""
from game_data import PICTURES

PNG_SIGNATURE = b"\x89PNG"


def test_stored_picture_is_answered_as_png(api):
    """Verifies: AC-021, AC-025 (stub generator holds bone-yard: 200, image/png, PNG signature)."""
    api.set_pictures({"bone-yard": "Red sand rusted ship ribs."})
    r = api.get_picture_png_raw("bone-yard")
    assert r.status_code == 200, f"{r.status_code} {r.text[:200]}"
    assert r.headers.get("content-type", "").startswith("image/png")
    assert r.content.startswith(PNG_SIGNATURE)


def test_picture_the_generator_does_not_hold_is_404(api):
    """Verifies: AC-021, AC-025 (bone-yard is in the picture list, but the stub generator does not hold it: 404)."""
    assert "bone-yard" in PICTURES
    r = api.get_picture_png_raw("bone-yard")
    assert r.status_code == 404


def test_generator_down_is_404(api):
    """Verifies: AC-021, AC-025 (stub generator down, it answers 503: the proxy gives 404)."""
    api.set_pictures({"bone-yard": "Red sand rusted ship ribs."})
    api.generator_down()
    r = api.get_picture_png_raw("bone-yard")
    assert r.status_code == 404


def test_name_not_in_picture_list_is_404(api):
    """Verifies: AC-021 (GET /api/pictures/no-such-picture/png: 404, also when the generator holds pictures)."""
    api.set_pictures({"bone-yard": "Red sand rusted ship ribs.", "no-such-picture": "x"})
    r = api.get_picture_png_raw("no-such-picture")
    assert r.status_code == 404
