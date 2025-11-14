"""Shared helpers for the Telegram parser."""
from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
from telethon.tl.custom.message import Message

load_dotenv()

LINK_RE = re.compile(r"https?://[^\s]+", re.IGNORECASE)
IMAGE_MIME_PREFIX = "image/"
DOCUMENT_MIME_WHITELIST = {"application/pdf", "application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}


@dataclass
class ParserConfig:
    api_id: int
    api_hash: str
    channel: List[str]
    backend_url: str
    backend_token: Optional[str]
    max_messages: Optional[int]
    session_name: str
    state_path: Path
    media_dir: Path


def load_config() -> ParserConfig:
    base_dir = Path(__file__).resolve().parent
    media_dir = base_dir / "downloads"
    media_dir.mkdir(parents=True, exist_ok=True)
    state_path = base_dir / "state.json"

    api_id = int(os.environ.get("API_ID", "0"))
    api_hash = os.environ.get("API_HASH", "")
    channel_value = os.environ.get("CHANNEL", "")
    backend_url = os.environ.get("BACKEND_URL", "http://localhost:3000/api/posts/import")
    backend_token = os.environ.get("BACKEND_TOKEN") or None
    session_name = os.environ.get("SESSION_NAME", "tg-parser")
    max_messages_env = os.environ.get("MAX_MESSAGES")
    max_messages = int(max_messages_env) if max_messages_env else None

    if not api_id or not api_hash or not channel_value:
        raise SystemExit("API_ID, API_HASH, and CHANNEL must be configured")

    channels = [chunk.strip() for chunk in channel_value.split(",") if chunk.strip()]

    return ParserConfig(
        api_id=api_id,
        api_hash=api_hash,
        channel=channels,
        backend_url=backend_url,
        backend_token=backend_token,
        max_messages=max_messages,
        session_name=session_name,
        state_path=state_path,
        media_dir=media_dir,
    )


@dataclass
class NormalizedMessage:
    tg_id: int
    text: str
    date: datetime
    images: List[str]
    links: List[str]

    def to_payload(self, label: str) -> Dict[str, object]:
        return {
            "tg_id": self.tg_id,
            "type": label,
            "text": self.text,
            "images": self.images,
            "date": self.date.astimezone(timezone.utc).isoformat(),
            "links": self.links,
        }


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self._data = self._read()

    def _read(self) -> Dict[str, int]:
        if not self.path.exists():
            return {}
        with self.path.open("r", encoding="utf-8") as handle:
            try:
                raw = json.load(handle)
            except json.JSONDecodeError:
                return {}
        return {str(key): int(value) for key, value in raw.items()}

    def last_id(self, channel: str) -> Optional[int]:
        return self._data.get(channel)

    def update(self, channel: str, message_id: int) -> None:
        current = self._data.get(channel, 0)
        self._data[channel] = max(current, message_id)
        with self.path.open("w", encoding="utf-8") as handle:
            json.dump(self._data, handle, indent=2)


async def extract_media(message: Message, media_dir: Path) -> List[str]:
    media_dir.mkdir(parents=True, exist_ok=True)
    saved: List[str] = []

    async def _download(suffix: str | None = None) -> None:
        index = len(saved)
        filename = f"{message.id}_{index}{suffix or ''}"
        destination = media_dir / filename
        result = await message.download_media(file=destination)
        if result:
            saved.append(Path(result).resolve().as_uri())

    file = getattr(message, "file", None)
    mime_type = getattr(file, "mime_type", None)

    if message.photo:
        await _download(".jpg")
    elif message.document and mime_type:
        if mime_type.startswith(IMAGE_MIME_PREFIX) or mime_type in DOCUMENT_MIME_WHITELIST:
            suffix = Path(getattr(file, "name", "")).suffix or None
            await _download(suffix)

    return saved


def extract_links(text: str) -> List[str]:
    return sorted({match.group(0) for match in LINK_RE.finditer(text or "")})


async def normalize_message(message: Message, media_dir: Path) -> Optional[NormalizedMessage]:
    text = (message.message or message.raw_text or "").strip()
    if not text:
        return None

    images = await extract_media(message, media_dir)
    links = extract_links(text)
    date = message.date
    if date.tzinfo is None:
        date = date.replace(tzinfo=timezone.utc)

    return NormalizedMessage(
        tg_id=message.id,
        text=text,
        date=date,
        images=images,
        links=links,
    )
