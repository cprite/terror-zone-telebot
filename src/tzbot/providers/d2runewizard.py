"""D2Runewizard terror zone tracker.

Replaces the headless-Chrome scraper this project started life with.  The
endpoint is a documented, cached JSON API (s-maxage=60), so a one-minute poll
costs the upstream nothing and cannot get us blocked the way scraping did.

https://d2runewizard.com/integration
"""

from __future__ import annotations

import logging

import aiohttp

from tzbot.providers.base import ProviderError, Snapshot

log = logging.getLogger(__name__)

ENDPOINT = "https://d2runewizard.com/api/trackers/terror-zone"


class D2RunewizardProvider:
    name = "d2runewizard"

    def __init__(
        self,
        *,
        contact: str = "",
        platform: str = "Telegram",
        repo: str = "",
        token: str = "",
        timeout: float = 15.0,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._token = token
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        self._session = session
        self._owns_session = session is None
        # D2Runewizard asks integrations to identify themselves on every call.
        self._headers = {"Accept": "application/json"}
        if contact:
            self._headers["D2R-Contact"] = contact
        if platform:
            self._headers["D2R-Platform"] = platform
        if repo:
            self._headers["D2R-Repo"] = repo

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(timeout=self._timeout)
            self._owns_session = True
        return self._session

    async def fetch(self) -> Snapshot:
        session = await self._get_session()
        params = {"token": self._token} if self._token else None
        try:
            async with session.get(
                ENDPOINT, headers=self._headers, params=params
            ) as response:
                if response.status != 200:
                    body = (await response.text())[:200]
                    raise ProviderError(f"HTTP {response.status}: {body}")
                payload = await response.json(content_type=None)
        except aiohttp.ClientError as exc:
            raise ProviderError(f"request failed: {exc}") from exc

        return Snapshot(
            current_raw=_pick(payload, "current", "currentTerrorZone"),
            next_raw=_pick(payload, "next", "nextTerrorZone"),
        )

    async def close(self) -> None:
        if self._session is not None and self._owns_session and not self._session.closed:
            await self._session.close()


def _pick(payload: object, flat_key: str, nested_key: str) -> str:
    """Read a zone name, tolerating both shapes the API is known to return.

    The free endpoint answers {"current": "..."}; the token-gated one nests the
    same value under {"currentTerrorZone": {"zone": "..."}}.
    """
    if not isinstance(payload, dict):
        raise ProviderError(f"expected a JSON object, got {type(payload).__name__}")

    flat = payload.get(flat_key)
    if isinstance(flat, str) and flat.strip():
        return flat.strip()

    nested = payload.get(nested_key)
    if isinstance(nested, dict):
        zone = nested.get("zone")
        if isinstance(zone, str) and zone.strip():
            return zone.strip()

    # The token-gated payload wraps everything one level deeper again.
    tracker = payload.get("terrorZone")
    if isinstance(tracker, dict):
        highest = tracker.get("highestProbabilityZone")
        if isinstance(highest, dict) and flat_key == "current":
            zone = highest.get("zone")
            if isinstance(zone, str) and zone.strip():
                return zone.strip()

    raise ProviderError(f"no usable value for {flat_key!r} in {sorted(payload)}")
