"""Runtime configuration, loaded from the environment (or a local .env file)."""

from __future__ import annotations

from typing import Annotated

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    bot_token: str = Field(alias="BOT_TOKEN")
    # NoDecode keeps pydantic-settings from json.loads()-ing "1,2" before the
    # validator below gets a chance to split it.
    admin_ids: Annotated[tuple[int, ...], NoDecode] = Field(default=(), alias="ADMIN_IDS")
    database_path: str = Field(default="data/tzbot.sqlite3", alias="DATABASE_PATH")

    poll_interval: int = Field(default=60, ge=15, alias="POLL_INTERVAL")
    prealert_minute: int = Field(default=45, ge=0, le=59, alias="PREALERT_MINUTE")
    broadcast_rate: float = Field(default=25.0, gt=0, alias="BROADCAST_RATE")

    # D2Runewizard asks integrations to identify themselves. These are sent on
    # every request; the token is optional and only unlocks the richer payload.
    d2rw_contact: str = Field(default="", alias="D2RW_CONTACT")
    d2rw_platform: str = Field(default="Telegram", alias="D2RW_PLATFORM")
    d2rw_repo: str = Field(
        default="https://github.com/cprite/terror-zone-telebot", alias="D2RW_REPO"
    )
    d2rw_token: str = Field(default="", alias="D2RW_TOKEN")

    @field_validator("admin_ids", mode="before")
    @classmethod
    def _split_admin_ids(cls, value: object) -> object:
        """Accept ADMIN_IDS as a comma-separated string: "123, 456"."""
        if isinstance(value, str):
            return tuple(int(part) for part in value.replace(" ", "").split(",") if part)
        return value


def load_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
