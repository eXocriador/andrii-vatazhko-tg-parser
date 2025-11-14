"""Filtering helpers for Telegram messages."""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable, List, Optional

from telethon.tl.custom.message import Message

from .config import FilterConfig
from .models import MediaMeta

HASHTAG_PATTERN = re.compile(r"#(\w+)")
AMOUNT_PATTERN = re.compile(
    r"(?P<amount>[\d\s.,]{3,})(?P<currency>\s?(грн|uah|usd|eur|₴|\$|€|£))",
    re.IGNORECASE,
)
MONO_PATTERN = re.compile(r"https?://(?:www\.)?mono\w+\.ua/[\w/.-]+", re.IGNORECASE)
CARD_PATTERN = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
GENERIC_URL_PATTERN = re.compile(r"https?://\S+")


@dataclass
class FilterOutcome:
    accepted: bool
    reason: str
    tags: List[str]
    amount: Optional[int]
    currency: Optional[str]
    donation_links: List[str]
    media: List[MediaMeta]


def _collect_media(message: Message) -> List[MediaMeta]:
    media_meta: List[MediaMeta] = []
    if message.photo:
        media_meta.append(
            MediaMeta(
                kind="photo",
                file_name=getattr(message.file, "name", None),
                mime_type=getattr(message.file, "mime_type", None),
                size=getattr(message.file, "size", None),
                caption=message.message,
            )
        )
    if message.video:
        media_meta.append(
            MediaMeta(
                kind="video",
                file_name=getattr(message.file, "name", None),
                mime_type=getattr(message.file, "mime_type", None),
                size=getattr(message.file, "size", None),
                caption=message.message,
            )
        )
    if message.document and not message.video:
        media_meta.append(
            MediaMeta(
                kind="document",
                file_name=getattr(message.file, "name", None),
                mime_type=getattr(message.file, "mime_type", None),
                size=getattr(message.file, "size", None),
                caption=message.message,
            )
        )
    return media_meta


def _extract_tags(text: str) -> List[str]:
    return [match.group(1).lower() for match in HASHTAG_PATTERN.finditer(text or "")]


def _extract_amount(text: str) -> tuple[Optional[int], Optional[str]]:
    match = AMOUNT_PATTERN.search(text)
    if not match:
        return None, None
    amount_raw = match.group("amount")
    digits = re.sub(r"[\s,.]", "", amount_raw)
    try:
        amount = int(digits)
    except ValueError:
        return None, None
    currency = match.group("currency").strip().upper()
    currency = currency.replace("₴", "UAH").replace("$", "USD").replace("€", "EUR")
    return amount, currency


def _extract_links(text: str) -> List[str]:
    links = set()
    for pattern in (MONO_PATTERN, CARD_PATTERN, GENERIC_URL_PATTERN):
        for match in pattern.findall(text or ""):
            links.add(match if isinstance(match, str) else match[0])
    return sorted(links)


def should_ingest(message: Message, config: FilterConfig) -> FilterOutcome:
    if not message.message:
        return FilterOutcome(False, "empty", [], None, None, [], [])

    text = message.message
    lowered = text.lower()

    # Keyword / hashtag heuristics
    keywords_hit = any(keyword.lower() in lowered for keyword in config.keywords)
    tags = _extract_tags(text)
    hashtags_hit = bool(set(tags) & set(config.hashtags))

    amount, currency = _extract_amount(text)
    if config.min_amount and amount and amount < config.min_amount:
        return FilterOutcome(False, "below-min", tags, amount, currency, [], [])

    links = _extract_links(text)
    media_meta = _collect_media(message)

    include = keywords_hit or hashtags_hit or bool(links)
    reason = "keywords" if keywords_hit else "hashtags" if hashtags_hit else "links" if links else "none"

    return FilterOutcome(include, reason, tags, amount, currency, links, media_meta)
