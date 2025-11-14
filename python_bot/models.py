"""Pydantic models shared across the ingestion pipeline."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, Field, field_serializer


class MediaMeta(BaseModel):
    kind: str
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    size: Optional[int] = None  # bytes
    caption: Optional[str] = None


class FundraiserPost(BaseModel):
    uid: str = Field(..., description="Stable identifier: channel_id:message_id")
    channel_id: int
    channel_username: Optional[str]
    message_id: int
    title: Optional[str] = None
    body: str
    original_posted_at: datetime
    collected_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    amount_requested: Optional[int] = None
    currency: Optional[str] = None
    donation_links: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    media: List[MediaMeta] = Field(default_factory=list)
    source_url: Optional[str] = None

    @field_serializer("original_posted_at", "collected_at")
    def serialize_dt(self, value: datetime):  # type: ignore[override]
        return value.isoformat()

    @classmethod
    def from_telegram_message(
        cls,
        message,
        *,
        channel_username: str | None,
        tags: List[str],
        amount_requested: Optional[int],
        currency: Optional[str],
        donation_links: List[str],
        media: List[MediaMeta],
    ) -> "FundraiserPost":
        body = message.message or ""
        title = (message.raw_text or "").split("\n", 1)[0][:120] if body else None
        return cls(
            uid=f"{message.chat_id}:{message.id}",
            channel_id=message.chat_id,
            channel_username=channel_username,
            message_id=message.id,
            title=title,
            body=body,
            original_posted_at=message.date.replace(tzinfo=timezone.utc),
            amount_requested=amount_requested,
            currency=currency,
            donation_links=donation_links,
            tags=tags,
            media=media,
            source_url=f"https://t.me/{channel_username}/{message.id}" if channel_username else None,
        )
