from __future__ import annotations

import pytest

from tzbot.storage import Storage


@pytest.fixture
async def storage(tmp_path):
    store = Storage(tmp_path / "test.sqlite3")
    await store.connect()
    try:
        yield store
    finally:
        await store.close()
