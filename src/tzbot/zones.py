"""The 36 terror zone groups, and matching of free-form provider strings onto them.

Providers spell the same zone differently over time ("Chaos Sanctuary" vs "The
Chaos Sanctuary", the short vs long form of Nihlathak's Temple).  Rather than
comparing strings exactly, every name is reduced to a set of significant words
and matched on that, so a wording change upstream does not silently stop
notifications.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Words that carry no meaning for matching: articles, conjunctions, and the
# punctuation-only leftovers of an Oxford comma.
_STOP_WORDS = frozenset({"and", "the", "of", "a"})
_WORD_RE = re.compile(r"[a-z0-9]+")


def normalize(name: str) -> frozenset[str]:
    """Reduce a zone name to the set of words that identify it."""
    folded = unicodedata.normalize("NFKD", name).casefold()
    words = _WORD_RE.findall(folded)
    return frozenset(word for word in words if word not in _STOP_WORDS)


@dataclass(frozen=True)
class Zone:
    """One selectable terror zone group."""

    id: int
    act: int
    name: str
    """Canonical display name, spelled the way D2Runewizard spells it."""
    aliases: tuple[str, ...] = ()
    """Other spellings seen in the wild, used for matching only."""
    emoji: str = ""

    @property
    def label(self) -> str:
        return f"{self.emoji} {self.name}".strip()

    @property
    def keys(self) -> frozenset[frozenset[str]]:
        return frozenset(normalize(n) for n in (self.name, *self.aliases))


ZONES: tuple[Zone, ...] = (
    # --- Act I ---
    Zone(1, 1, "Blood Moor and Den of Evil"),
    Zone(2, 1, "Cold Plains and The Cave"),
    Zone(3, 1, "Burial Grounds, Crypt, and Mausoleum",
         ("Burial Grounds, The Crypt, and The Mausoleum",)),
    Zone(4, 1, "Stony Field"),
    Zone(5, 1, "Dark Wood and Underground Passage"),
    Zone(6, 1, "Black Marsh and The Hole"),
    Zone(7, 1, "The Forgotten Tower", ("Forgotten Tower",)),
    Zone(8, 1, "Jail and Barracks"),
    Zone(9, 1, "Cathedral and Catacombs"),
    Zone(10, 1, "The Pit and Tamoe Highland",
         ("Tamoe Highland, Outer Cloister, and The Pit", "The Pit", "Pit")),
    Zone(11, 1, "Tristram"),
    Zone(12, 1, "Moo Moo Farm", ("The Secret Cow Level",), emoji="\N{COW}"),
    # --- Act II ---
    Zone(13, 2, "Lut Gholein Sewers", ("Sewers",)),
    Zone(14, 2, "Rocky Waste and Stony Tomb", ("Stony Tomb and Rocky Waste",)),
    Zone(15, 2, "Dry Hills and Halls of the Dead"),
    Zone(16, 2, "Far Oasis"),
    Zone(17, 2, "Lost City, Valley of Snakes, and Claw Viper Temple"),
    Zone(18, 2, "Ancient Tunnels"),
    Zone(19, 2, "Arcane Sanctuary"),
    Zone(20, 2, "Tal Rasha's Tombs and Tal Rasha's Chamber", ("Tal Rasha's Tombs",)),
    # --- Act III ---
    Zone(21, 3, "Spider Forest and Spider Cavern"),
    Zone(22, 3, "Great Marsh"),
    Zone(23, 3, "Flayer Jungle and Flayer Dungeon"),
    Zone(24, 3, "Kurast Bazaar, Ruined Temple, and Disused Fane"),
    Zone(25, 3, "Travincal"),
    Zone(26, 3, "Durance of Hate"),
    # --- Act IV ---
    Zone(27, 4, "Outer Steppes and Plains of Despair"),
    Zone(28, 4, "River of Flame and City of the Damned"),
    Zone(29, 4, "Chaos Sanctuary", ("The Chaos Sanctuary",)),
    # --- Act V ---
    Zone(30, 5, "Bloody Foothills, Frigid Highlands, and Abaddon"),
    Zone(31, 5, "Glacial Trail and Drifter Cavern"),
    Zone(32, 5, "Crystalline Passage and Frozen River"),
    Zone(33, 5, "Arreat Plateau and Pit of Acheron"),
    Zone(34, 5, "Nihlathak's Temple, Halls of Anguish, Halls of Pain, and Halls of Vaught",
         ("Nihlathak's Temple and Temple Halls", "Nihlathak's Temple")),
    Zone(35, 5, "Ancient's Way and Icy Cellar"),
    Zone(36, 5, "Worldstone Keep, Throne of Destruction, and Worldstone Chamber"),
)

ZONES_BY_ID: dict[int, Zone] = {zone.id: zone for zone in ZONES}

_EXACT: dict[frozenset[str], Zone] = {}
for _zone in ZONES:
    for _key in _zone.keys:
        _EXACT.setdefault(_key, _zone)


def match(name: str) -> Zone | None:
    """Resolve a provider's zone string to a known zone, or None if unrecognised.

    Falls back to the best partial overlap so that an upstream rename such as
    "Chaos Sanctuary (Act 4)" still resolves instead of dropping a rotation.
    """
    if not name or not name.strip():
        return None

    words = normalize(name)
    if not words:
        return None

    exact = _EXACT.get(words)
    if exact is not None:
        return exact

    best: Zone | None = None
    best_score = 0.0
    for zone in ZONES:
        for key in zone.keys:
            overlap = len(words & key)
            if not overlap:
                continue
            # Jaccard similarity: rewards overlap, punishes extra words on
            # either side, so "Pit" does not win over "Pit of Acheron".
            score = overlap / len(words | key)
            if score > best_score:
                best_score, best = score, zone

    # Below this, the overlap is a coincidence (one shared word out of many).
    return best if best_score >= 0.5 else None
