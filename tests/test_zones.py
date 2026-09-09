"""The zone table, and matching provider strings onto it."""

from __future__ import annotations

import pytest

from tzbot.zones import ZONES, ZONES_BY_ID, match, normalize


def test_thirty_six_zones_numbered_consecutively():
    assert len(ZONES) == 36
    assert [zone.id for zone in ZONES] == list(range(1, 37))
    assert len(ZONES_BY_ID) == 36


def test_every_zone_belongs_to_a_real_act():
    assert {zone.act for zone in ZONES} == {1, 2, 3, 4, 5}


@pytest.mark.parametrize(
    ("reported", "expected_id"),
    [
        # Names exactly as d2runewizard reports them.
        ("Blood Moor and Den of Evil", 1),
        ("Dark Wood and Underground Passage", 5),
        ("Durance of Hate", 26),
        ("Worldstone Keep, Throne of Destruction, and Worldstone Chamber", 36),
        # Spellings the same tracker has also been seen using.
        ("The Chaos Sanctuary", 29),
        ("Chaos Sanctuary", 29),
        ("Nihlathak's Temple and Temple Halls", 34),
        ("Forgotten Tower", 7),
        ("The Pit", 10),
        # Observed live on 2026-09-09, and spelled differently again from the
        # tracker page - which is the whole reason matching is fuzzy.
        ("Tamoe Highland, Outer Cloister, and The Pit", 10),
        # Cosmetic noise must not break the match.
        ("  durance   of   hate  ", 26),
    ],
)
def test_known_names_resolve(reported, expected_id):
    zone = match(reported)
    assert zone is not None, reported
    assert zone.id == expected_id


@pytest.mark.parametrize("reported", ["", "   ", "Some Brand New Zone", "!!!"])
def test_unknown_names_do_not_resolve(reported):
    assert match(reported) is None


def test_close_but_different_zones_stay_distinct():
    """'Pit of Acheron' shares a word with 'The Pit' - they must not collide."""
    assert match("Arreat Plateau and Pit of Acheron").id == 33
    assert match("The Pit and Tamoe Highland").id == 10


def test_normalize_drops_filler_words():
    assert normalize("Cold Plains and The Cave") == normalize("Cold Plains Cave")


def test_every_canonical_name_matches_itself():
    for zone in ZONES:
        assert match(zone.name) is zone, zone.name
        for alias in zone.aliases:
            assert match(alias) is zone, alias
