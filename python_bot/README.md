# Python Telegram collector

This folder hosts the Telethon-based script that scrapes one or more Telegram channels and
turns fundraiser posts into JSON documents.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r python_bot/requirements.txt
cp .env.example .env  # edit secrets
python -m python_bot.collector --stdout
```

## Environment variables

| Variable | Description |
| --- | --- |
| `TELEGRAM_API_ID` | API ID from https://my.telegram.org |
| `TELEGRAM_API_HASH` | API hash from https://my.telegram.org |
| `TELEGRAM_SESSION` | Local session name (default `tg-parser`). |
| `TELEGRAM_CHANNELS` | Comma-separated list of channels (`channel1,channel2`). |
| `MAX_MESSAGES` | Optional per-channel limit for history (default: all). |
| `OUTPUT_PATH` | JSONL file path (default `artifacts/fundraisers.jsonl`). |
| `FUNDRAISER_KEYWORDS` | CSV keywords to match (`збір,волонтери`). |
| `FUNDRAISER_HASHTAGS` | CSV hashtags without `#` (`zbir,dopomoga`). |
| `FUNDRAISER_MIN_AMOUNT` | Minimum detected sum to accept (integer). |

## Filtering logic

1. Each message is scanned for keywords and hashtags; if any match, it is marked relevant.
2. Even if no keywords match, the presence of donation-style links (mono bank, raw cards,
   or any https URL) will keep the post.
3. Amounts/currency are parsed with regex heuristics. They can be used for analytics or
   to discard low-effort posts via `FUNDRAISER_MIN_AMOUNT`.
4. Attachments (photos/videos/docs) are described as metadata and included in the JSON.

## Output

- Default output is a `JSONL` (one document per line) saved to `artifacts/fundraisers.jsonl`.
- `--stdout` mirrors the same payload so you can pipe it somewhere else, e.g. `| jq '.'`.
- Each document is compatible with `schemas/fundraiser.schema.json`.

## Extending

- Add richer heuristics to `filters.py` (e.g. NLP classifiers, channel-specific logic).
- Swap the writer in `collector.py` to insert straight into PostgreSQL via asyncpg
  when you do not want to store intermediate files.
