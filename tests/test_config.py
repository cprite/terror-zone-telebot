"""Settings parsing, read the way production reads it: from the environment.

Constructing Settings(...) in Python skips the environment source, which is
exactly how a comma-separated ADMIN_IDS passed every test while still crashing
the container on boot.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from tzbot.config import Settings

BASE_ENV = {"BOT_TOKEN": "42:TEST"}


@pytest.fixture(autouse=True)
def clean_env(monkeypatch, tmp_path):
    for key in (
        "BOT_TOKEN", "ADMIN_IDS", "DATABASE_PATH", "POLL_INTERVAL",
        "PREALERT_MINUTE", "BROADCAST_RATE", "D2RW_CONTACT", "D2RW_TOKEN",
    ):
        monkeypatch.delenv(key, raising=False)
    # Never pick up a developer's real .env while testing.
    monkeypatch.chdir(tmp_path)


def load(monkeypatch, **env: str) -> Settings:
    for key, value in {**BASE_ENV, **env}.items():
        monkeypatch.setenv(key, value)
    return Settings()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("", ()),
        ("123", (123,)),
        ("123,456", (123, 456)),
        ("123, 456", (123, 456)),
        (" 123 , 456 ,", (123, 456)),
    ],
)
def test_admin_ids_from_env(monkeypatch, raw, expected):
    assert load(monkeypatch, ADMIN_IDS=raw).admin_ids == expected


def test_admin_ids_default_to_nobody(monkeypatch):
    assert load(monkeypatch).admin_ids == ()


def test_missing_token_is_an_error(monkeypatch):
    with pytest.raises(ValidationError):
        Settings()


@pytest.mark.parametrize(
    ("key", "value"),
    [
        ("POLL_INTERVAL", "5"),        # below the upstream cache, pointless
        ("PREALERT_MINUTE", "60"),     # not a minute of the hour
        ("BROADCAST_RATE", "0"),       # would divide by zero
        ("ADMIN_IDS", "not-a-number"),
    ],
)
def test_bad_values_are_rejected(monkeypatch, key, value):
    with pytest.raises(ValidationError):
        load(monkeypatch, **{key: value})


def test_defaults(monkeypatch):
    settings = load(monkeypatch)
    assert settings.poll_interval == 60
    assert settings.prealert_minute == 45
    assert settings.database_path == "data/tzbot.sqlite3"
    assert settings.d2rw_platform == "Telegram"
    assert settings.d2rw_token == ""
