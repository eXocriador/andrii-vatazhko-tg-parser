# Telegram Fundraiser Parser

This repository hosts two cooperating pieces:

1. **Python ingestion bot** – connects to Telegram via the MTProto API, streams all posts
   from configured channels, classifies/filters them, and serialises the relevant bits to JSON
   documents so they can be stored in a relational database.
2. **Node.js backend** – the primary backend facing the frontend; it exposes REST endpoints
   backed by MongoDB and consumes the JSON payloads produced by the bot.

## High-level architecture

```
Telegram Channel(s) ──> Python Bot (Telethon) ──> JSON batch ──> MongoDB
                                                        │
                                                        ▼
                                             Node.js API (Express + Mongoose)
```

- The bot is intentionally isolated so that the MTProto credentials never live inside the
  main backend container. It can run on a scheduler (cron, GitHub Actions, etc.) and only
  writes to an ingestion queue/folder or directly to the DB.
- The Node.js service is written in TypeScript using Express (lightweight) and Mongoose as the ODM,
  keeping the JSON schema aligned with the documents stored in MongoDB.
- JSON schema is shared between the services (see `schemas/fundraiser.schema.json`). The Python
  bot validates outgoing payloads with Pydantic, while the Node.js layer uses Zod to validate the
  payload when inserting or reading from the DB.

## Repository layout

```
python_bot/      # Telethon-based collector
backend/         # Node.js (TS) API scaffold
schemas/         # JSON schemas shared by both sides
```

The next sections go into detail for each part.

---

## Python ingestion bot

- Implemented with **Telethon** because it supports full-channel history export plus granular
  filtering over message entities/attachments.
- The bot accepts filters so you can target only fundraiser posts (e.g. containing specific hashtags
  or custom emoji) and normalises each matched post to a consistent structure.
- Outputs can either be:
  - `stdout`/`jsonl` stream (useful for piping into another process)
  - JSON file under `artifacts/` for later import
  - Direct DB insert (optional; see TODO section)

Key modules:

| Path | Description |
| --- | --- |
| `python_bot/config.py` | Loads env vars / `.env` for API_ID, API_HASH, session name, etc. |
| `python_bot/models.py` | Pydantic models for fundraiser posts. |
| `python_bot/filters.py` | Helpers to decide whether a Telegram message is relevant. |
| `python_bot/collector.py` | Main entrypoint: fetches channel history, applies filters, emits JSON. |

Run instructions are documented inside `python_bot/README.md`.

## Node.js backend (primary service)

- Built with **TypeScript + Express**, so the runtime stays lean but strongly typed.
- **MongoDB + Mongoose** store the posts using the same JSON structure produced by the bot.
- Exposes endpoints such as:
  - `GET /fundraisers` – paginated list
  - `GET /fundraisers/:id` – details
  - `POST /fundraisers/import` – (protected) ingestion endpoint when the bot pushes data

The backend scaffold lives under `backend/`. Development instructions are in `backend/README.md`.

## Shared schema

`schemas/fundraiser.schema.json` captures the payload format (same fields as the Pydantic
model). Both services validate against it to reduce drift.

## Next steps

1. Configure `.env` for Telethon (API credentials, channel usernames) і `MONGODB_URI` для бекенду.
2. Встанови залежності (`pip install -r python_bot/requirements.txt`, `cd backend && yarn install`).
3. Запусти збір даних із Telegram та надішли JSON у `/fundraisers/import` для наповнення MongoDB.
4. Налаштуй воркфлоу (cron/CI), який періодично запускає бота та синхронізує дані з Node API.
