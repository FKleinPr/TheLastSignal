"""Acceptance tests for T-013: character names in the parser.

Verifies AC-016 (FR-030): the rule-based parser (the stub model answers {"verb": null}) accepts every name in a
character's `names`, case-insensitive, with an optional `the`, and uses the character id; a name of two characters
present (`local` in scrap-market) still asks which one is meant and changes nothing.
"""
from game_data import ROUTES, TEXT


def first_answer(api, route: list, command: str) -> dict:
    """The answer to `command` in a new game, after `route`."""
    game_id = api.new_game()["game_id"]
    api.run(game_id, route)
    return api.cmd(game_id, command)


def test_talk_to_jex_same_as_merchant_jex(api):
    """Verifies: AC-016 (talk to jex answers the same line as talk to merchant-jex)."""
    by_name = first_answer(api, ROUTES["to_scrap_market"], "talk to jex")
    by_id = first_answer(api, ROUTES["to_scrap_market"], "talk to merchant-jex")
    assert TEXT["jex_always"] in by_id["text"]
    assert by_name["text"] == by_id["text"]


def test_talk_to_the_merchant_works_like_jex(api):
    """Verifies: AC-016 (talk to the merchant works like talk to jex)."""
    with_the = first_answer(api, ROUTES["to_scrap_market"], "talk to the merchant")
    by_name = first_answer(api, ROUTES["to_scrap_market"], "talk to jex")
    assert TEXT["jex_always"] in with_the["text"]
    assert with_the["text"] == by_name["text"]


def test_names_are_case_insensitive(api):
    """Verifies: AC-016 (talk to JEX works like talk to jex)."""
    upper = first_answer(api, ROUTES["to_scrap_market"], "talk to JEX")
    assert TEXT["jex_always"] in upper["text"]


def test_talk_to_echo_same_as_child_echo(api):
    """Verifies: AC-016 (a second character: echo is child-echo)."""
    by_name = first_answer(api, ROUTES["to_scrap_market"], "talk to echo")
    by_id = first_answer(api, ROUTES["to_scrap_market"], "talk to child-echo")
    assert TEXT["child_always"] in by_id["text"]
    assert by_name["text"] == by_id["text"]


def test_give_core_to_lira_records_awakeners_choice(api):
    """Verifies: AC-016 (give core to lira records the awakeners choice as give core to archivist-lira does)."""
    route = ["give core to lira" if c == "give core to archivist-lira" else c for c in ROUTES["death_awakening"]]
    game_id = api.new_game()["game_id"]
    responses = api.run(game_id, route)
    assert "core" not in responses[3]["inventory"]
    assert TEXT["awakening_warning"] in responses[-2]["text"]
    assert responses[-1]["dead"] is True
    assert TEXT["awakening_death"] in responses[-1]["text"]


def test_shared_name_still_ambiguous(api, game):
    """Verifies: AC-016 (local is a name of child-echo and merchant-jex: the game asks, nothing changes)."""
    game_id = game["game_id"]
    api.run(game_id, ROUTES["to_scrap_market"])
    before = api.state(game_id)
    r = api.cmd(game_id, "talk to local")
    assert TEXT["ambiguous"] in r["text"]
    assert "merchant-jex" in r["text"] and "child-echo" in r["text"]
    after = api.state(game_id)
    assert (after["location"], after["inventory"], after["flags"], after["clues"]) == (
        before["location"], before["inventory"], before["flags"], before["clues"])
