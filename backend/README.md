# Node.js backend

This is the primary API that fronts the frontend clients. It consumes the JSON payloads
(usually via the `/fundraisers/import` endpoint) that the Python bot emits.

## Stack

- **TypeScript + Express** – мінімальний REST-шар
- **MongoDB + Mongoose** – зберігання та ODM із гнучкими схемами
- **Zod** – рантайм-валідація, щоб формат збігався з Python-колектором

## Commands

```bash
cd backend
yarn install
yarn dev
```

Переконайся, що `MONGODB_URI` заданий у `.env` перед запуском.

## API surface

| Method | Path | Description |
| --- | --- | --- |
| `GET` | `/healthz` | Liveness probe |
| `GET` | `/fundraisers` | Paginated list (`?page=1&pageSize=20`) |
| `GET` | `/fundraisers/:uid` | Fetch single fundraiser |
| `POST` | `/fundraisers/import` | Protected (via `X-INGESTION-KEY`) ingestion endpoint |

The import route accepts either a single object or an array of fundraiser objects as defined
in `schemas/fundraiser.schema.json`.

## Deployment model

1. Python bot dumps JSON (or pushes HTTP) after scraping Telegram.
2. CI/CD job posts the JSON to `/fundraisers/import` using the shared token.
3. Frontend reads curated fundraisers via the REST endpoints.
