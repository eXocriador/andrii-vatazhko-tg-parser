"""Telegram collector that pipes fundraiser/report posts into the backend."""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Iterable, List, Tuple

import httpx
from telethon import TelegramClient
from telethon.errors import RPCError

from ai_filter import classify
from utils import NormalizedMessage, ParserConfig, StateStore, load_config, normalize_message

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

SESSION_DIR = Path(__file__).resolve().parent / "session"
SESSION_DIR.mkdir(parents=True, exist_ok=True)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Telegram parser for fundraisers")
    parser.add_argument("--channel", action="append", help="Override channel username (without @)")
    parser.add_argument("--limit", type=int, default=None, help="Max messages per channel")
    parser.add_argument("--new", action="store_true", help="Only fetch messages newer than the saved state")
    return parser.parse_args()


async def send_payloads(payloads: List[dict], config: ParserConfig) -> None:
    if not payloads:
        return
    headers = {"Content-Type": "application/json"}
    if config.backend_token:
        headers["X-INGESTION-KEY"] = config.backend_token
    data = payloads if len(payloads) > 1 else payloads[0]
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(config.backend_url, json=data, headers=headers)
        response.raise_for_status()
    logger.info("Uploaded %s posts to backend", len(payloads))


async def process_channel(
    client: TelegramClient,
    channel: str,
    config: ParserConfig,
    state: StateStore,
    limit: int | None,
    only_new: bool,
) -> Tuple[List[dict], int]:
    logger.info("Scanning %s", channel)
    collected: List[dict] = []
    last_seen = state.last_id(channel)
    highest_seen = last_seen or 0

    async for message in client.iter_messages(channel, limit=limit):
        if only_new and last_seen and message.id <= last_seen:
            break
        highest_seen = max(highest_seen, message.id)
        normalized = await normalize_message(message, config.media_dir)
        if not normalized:
            continue
        label = classify(normalized.text)
        if label == "other":
            continue
        collected.append(normalized.to_payload(label))

    logger.info("Channel %s produced %s deliverable posts", channel, len(collected))
    return collected, highest_seen


async def run_collector() -> None:
    args = parse_args()
    config = load_config()
    channels = args.channel or config.channel
    if not channels:
        raise SystemExit("No channel configured. Use CHANNEL env or --channel")

    limit = args.limit or config.max_messages
    state = StateStore(config.state_path)

    session_path = SESSION_DIR / config.session_name
    client = TelegramClient(str(session_path), config.api_id, config.api_hash)

    async with client:
        for channel in channels:
            try:
                payloads, highest_seen = await process_channel(
                    client, channel, config, state, limit, args.new
                )
            except RPCError as exc:
                logger.error("Failed to read %s: %s", channel, exc)
                continue

            if payloads:
                try:
                    await send_payloads(payloads, config)
                except httpx.HTTPError as exc:
                    logger.error("Failed to upload payloads for %s: %s", channel, exc)
                    continue

            if highest_seen:
                state.update(channel, highest_seen)


def main() -> None:
    asyncio.run(run_collector())


if __name__ == "__main__":
    main()
