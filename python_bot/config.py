"""Configuration helpers for the Telegram collector."""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class FilterConfig(BaseModel):
    keywords: List[str] = Field(default_factory=list)
    hashtags: List[str] = Field(default_factory=list)
    min_amount: Optional[int] = None


class Settings(BaseSettings):
    api_id: int = Field(alias="TELEGRAM_API_ID")
    api_hash: str = Field(alias="TELEGRAM_API_HASH")
    session_name: str = Field(default="tg-parser", alias="TELEGRAM_SESSION")
    channels: List[str] = Field(default_factory=list, alias="TELEGRAM_CHANNELS")
    max_messages: Optional[int] = Field(default=None, alias="MAX_MESSAGES")
    output_path: Path = Field(
        default_factory=lambda: Path("artifacts/fundraisers.jsonl"),
        alias="OUTPUT_PATH",
    )
    keywords: List[str] = Field(default_factory=list, alias="FUNDRAISER_KEYWORDS")
    hashtags: List[str] = Field(default_factory=list, alias="FUNDRAISER_HASHTAGS")
    min_amount: Optional[int] = Field(default=None, alias="FUNDRAISER_MIN_AMOUNT")

    model_config = SettingsConfigDict(populate_by_name=True, extra="allow")

    @field_validator("channels", mode="before")
    @classmethod
    def parse_channels(cls, value: str | List[str]) -> List[str]:
        if isinstance(value, list):
            return value
        return _split_csv(value)

    @field_validator("keywords", "hashtags", mode="before")
    @classmethod
    def parse_csv_field(cls, value):
        if isinstance(value, list):
            return value
        return _split_csv(value)

    @field_validator("hashtags", mode="after")
    @classmethod
    def normalize_hashtags(cls, value: List[str]) -> List[str]:
        return [item.lower().lstrip("#") for item in value]

    @field_validator("min_amount", mode="before")
    @classmethod
    def parse_min_amount(cls, value):
        if value in (None, ""):
            return None
        if isinstance(value, str):
            try:
                return int(value)
            except ValueError:
                raise ValueError("FUNDRAISER_MIN_AMOUNT must be an integer") from None
        return value

    @field_validator("output_path", mode="before")
    @classmethod
    def coerce_path(cls, value):
        if isinstance(value, Path):
            return value
        if value in (None, ""):
            return Path("artifacts/fundraisers.jsonl")
        return Path(value)

    @classmethod
    def from_env(cls) -> "Settings":
        return cls()

    @property
    def filter_config(self) -> FilterConfig:
        return FilterConfig(
            keywords=self.keywords,
            hashtags=self.hashtags,
            min_amount=self.min_amount,
        )


settings = Settings.from_env()
