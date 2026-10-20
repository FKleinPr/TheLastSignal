"""Acceptance tests for T-014: reaction texts of the core choice.

Verifies AC-19 (FR-032, FR-035): the choosing command's response text contains its reaction text (spec 9.6), and
the warning and the ending still come on the 2nd and 3rd command after it. The positions in each route are fixed:
death_awakening gives the core at index 3, ending_awakeners and ending_silencers at index 7, ending_escape enters
edge-of-town with the core at index 2.
"""
from game_data import CORE_REACTIONS, ROUTES, TEXT


def test_awakeners_reaction_and_counting(api, game):
    """Verifies: AC-019 (giving the core to archivist-lira in archives)."""
    responses = api.run(game["game_id"], ROUTES["ending_awakeners"])
    choice = 7
    assert CORE_REACTIONS["awakeners"] in responses[choice]["text"]
    assert TEXT["awakening_warning"] in responses[choice + 2]["text"]
    assert responses[choice + 3]["ending"] == "ending-awakeners"
    assert responses[choice + 2]["ending"] is None


def test_silencers_reaction_and_counting(api, game):
    """Verifies: AC-019 (giving the core to silencer-leader in control-center)."""
    responses = api.run(game["game_id"], ROUTES["ending_silencers"])
    choice = 7
    assert CORE_REACTIONS["silencers"] in responses[choice]["text"]
    assert TEXT["awakening_warning"] in responses[choice + 2]["text"]
    assert responses[choice + 3]["ending"] == "ending-silencers"
    assert responses[choice + 2]["ending"] is None


def test_flee_reaction_after_location_description(api, game):
    """Verifies: AC-019 (entering edge-of-town with the core; the reaction comes after the description)."""
    responses = api.run(game["game_id"], ROUTES["ending_escape"])
    choice = 2
    entered = responses[choice]
    assert entered["location"] == "edge-of-town"
    assert CORE_REACTIONS["flee"] in entered["text"]
    assert entered["text"].index(CORE_REACTIONS["flee"]) > 0
    assert TEXT["awakening_warning"] in responses[choice + 2]["text"]
    assert responses[choice + 3]["ending"] == "ending-escape"


def test_death_awakening_counting_unchanged(api, game):
    """Verifies: AC-019 (after giving the core and staying: warning at 2, death-awakening at 3)."""
    responses = api.run(game["game_id"], ROUTES["death_awakening"])
    choice = 3
    assert CORE_REACTIONS["awakeners"] in responses[choice]["text"]
    assert TEXT["awakening_warning"] in responses[choice + 2]["text"]
    assert responses[choice + 2]["dead"] is False
    assert responses[choice + 3]["dead"] is True
    assert TEXT["awakening_death"] in responses[choice + 3]["text"]


def test_reaction_only_in_choosing_command(api, game):
    """Verifies: AC-019 (the reaction text belongs to the choosing command, not to the commands after it)."""
    responses = api.run(game["game_id"], ROUTES["death_awakening"])
    assert all(CORE_REACTIONS["awakeners"] not in r["text"] for r in responses[:3] + responses[4:])
