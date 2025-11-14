"""Main entrypoint for scraping Telegram fundraiser posts."""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
from pathlib import Path
from typing import List

from telethon import TelegramClient
from telethon.errors import RPCError
from telethon.tl.custom.message import Message

from .config import Settings, settings
from .filters import FilterOutcome, should_ingest
from .models import FundraiserPost

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


async def _fetch_from_channel(
    client: TelegramClient,
    channel: str,
    limit: int | None,
    cfg: Settings,
) -> List[FundraiserPost]:
    posts: List[FundraiserPost] = []
    logger.info("Scanning %s", channel)
    async for message in client.iter_messages(channel, limit=limit):
        fundraiser = _process_message(message, cfg)
        if fundraiser:
            posts.append(fundraiser)
    logger.info("%s -> %s fundraiser posts", channel, len(posts))
    return posts


def _process_message(message: Message, cfg: Settings) -> FundraiserPost | None:
    outcome: FilterOutcome = should_ingest(message, cfg.filter_config)
    if not outcome.accepted:
        return None
    chat = getattr(message, "chat", None)
    return FundraiserPost.from_telegram_message(
        message,
        channel_username=getattr(chat, "username", None),
        tags=outcome.tags,
        amount_requested=outcome.amount,
        currency=outcome.currency,
        donation_links=outcome.donation_links,
        media=outcome.media,
    )


async def run_collector(cfg: Settings, *, channels: List[str], limit: int | None, output: Path | None, stdout: bool) -> None:
    if not channels:
        raise SystemExit("No channels configured. Provide --channel or TELEGRAM_CHANNELS.")

    async with TelegramClient(cfg.session_name, cfg.api_id, cfg.api_hash) as client:
        collected: List[FundraiserPost] = []
        for channel in channels:
            try:
                posts = await _fetch_from_channel(client, channel, limit, cfg)
            except RPCError as exc:  # pragma: no cover
                logger.error("Failed to fetch %s: %s", channel, exc)
                continue
            collected.extend(posts)

    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as handle:
            for post in collected:
                handle.write(json.dumps(post.model_dump(), ensure_ascii=False) + "\n")
        logger.info("Written %s fundraiser posts to %s", len(collected), output)

    if stdout:
        for post in collected:
            print(json.dumps(post.model_dump(), ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram fundraiser collector")
    parser.add_argument("--channel", action="append", help="Telegram channel username (without @)")
    parser.add_argument("--limit", type=int, default=None, help="Max messages per channel")
    parser.add_argument("--output", type=Path, default=None, help="Path to JSONL output")
    parser.add_argument("--stdout", action="store_true", help="Also dump payloads to stdout")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = settings
    channels = args.channel or cfg.channels
    limit = args.limit or cfg.max_messages
    output = args.output or cfg.output_path
    stdout = args.stdout

    asyncio.run(run_collector(cfg, channels=channels, limit=limit, output=output, stdout=stdout))


if __name__ == "__main__":
    main()
