"""Parsing whatever shape the tracker answers with."""

from __future__ import annotations

import pytest

from tzbot.providers.base import ProviderError, Snapshot
from tzbot.providers.d2runewizard import _pick

FREE_PAYLOAD = {
    "current": "Dark Wood and Underground Passage",
    "next": "Durance of Hate",
    "currentTerrorZone": {"zone": "Dark Wood and Underground Passage"},
    "nextTerrorZone": {"zone": "Durance of Hate"},
}

NESTED_ONLY = {
    "currentTerrorZone": {"zone": "Travincal"},
    "nextTerrorZone": {"zone": "Tristram"},
}


def test_reads_the_flat_shape():
    current = _pick(FREE_PAYLOAD, "current", "currentTerrorZone")
    assert current == "Dark Wood and Underground Passage"
    assert _pick(FREE_PAYLOAD, "next", "nextTerrorZone") == "Durance of Hate"


def test_falls_back_to_the_nested_shape():
    assert _pick(NESTED_ONLY, "current", "currentTerrorZone") == "Travincal"


def test_reads_the_token_gated_shape():
    payload = {"terrorZone": {"highestProbabilityZone": {"zone": "Chaos Sanctuary"}}}
    assert _pick(payload, "current", "currentTerrorZone") == "Chaos Sanctuary"


@pytest.mark.parametrize("payload", [{}, {"current": ""}, {"current": None}, []])
def test_unusable_payloads_raise(payload):
    with pytest.raises(ProviderError):
        _pick(payload, "current", "currentTerrorZone")


def test_snapshot_labels_fall_back_to_the_raw_name():
    """An unrecognised zone is still relayed, not swallowed."""
    snapshot = Snapshot(current_raw="Brand New Zone", next_raw="Travincal")
    assert snapshot.current is None
    assert snapshot.current_label() == "Brand New Zone"
    assert snapshot.next.id == 25
    assert snapshot.next_label() == "Travincal"
