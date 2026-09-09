"""Provider interface: anything that can report the current and next terror zone."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from tzbot.zones import Zone, match


class ProviderError(RuntimeError):
    """The provider could not be reached, or answered with something unusable."""


@dataclass(frozen=True)
class Snapshot:
    """One reading of the tracker: what is terrorised now, and what is next."""

    current_raw: str
    next_raw: str

    @property
    def current(self) -> Zone | None:
        return match(self.current_raw)

    @property
    def next(self) -> Zone | None:
        return match(self.next_raw)

    def current_label(self) -> str:
        zone = self.current
        return zone.label if zone else self.current_raw

    def next_label(self) -> str:
        zone = self.next
        return zone.label if zone else self.next_raw


@runtime_checkable
class TerrorZoneProvider(Protocol):
    name: str

    async def fetch(self) -> Snapshot: ...

    async def close(self) -> None: ...
