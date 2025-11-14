# Телеграм-парсер зборів

Комплект містить два незалежні сервіси, які разом будують повний пайплайн:

1. **`python_parser/`** – асинхронний Telethon-скрипт із локальним zero-shot AI, який витягує пости з каналу, класифікує їх (fundraising/report/other) і відправляє валідні об'єкти у бекенд.
2. **`backend/`** – Node.js (TypeScript) API на Express + MongoDB. Приймає імпорт, зберігає записи без дублікатів (`tg_id`), надає пагінований список та деталі постів для фронтенду.

```
Telegram → Telethon collector → AI classifier → HTTP import → Express API → MongoDB → Frontend
```

## Швидкий старт

### 1. Оточення

1. Скопіюй `.env.example` у `.env` і заповни значення для обох сервісів.
2. Запусти MongoDB (локально або в Docker) й переконайся, що URI в `.env` доступний.

### 2. Backend (`backend/`)

```bash
cd backend
yarn install
yarn dev
```

API з'явиться на `http://localhost:3000`. Доступні ендпоїнти:

| Method | Path | Опис |
| --- | --- | --- |
| `POST` | `/api/posts/import` | Приймає один або масив постів (ті, що надсилає парсер). |
| `GET` | `/api/posts` | Пагінований список (`?page=1&limit=20`). |
| `GET` | `/api/posts/:id` | Один пост за Mongo `_id` або `tg_id`. |

Якщо `INGEST_TOKEN` задано, потрібно надсилати заголовок `X-INGESTION-KEY`.

### 3. Python parser (`python_parser/`)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r python_parser/requirements.txt
python python_parser/collector.py --new
```

Скрипт очікує, що:
- `API_ID`, `API_HASH`, `CHANNEL` задані в `.env`.
- `BACKEND_URL` вказує на `/api/posts/import` вашого бекенду.
- Сесія Telethon зберігається в `python_parser/session/` (автоматично створюється).

За замовчуванням проходиться весь канал (`MAX_MESSAGES` обмежує історію). Ключ `--new` змушує брати тільки ті повідомлення, що новіші за збережений `state.json`. Можна передати інший канал через `--channel some_channel`.

### Формат даних

Парсер надсилає об'єкти вигляду:

```json
{
  "tg_id": 123,
  "type": "fundraising",
  "text": "...",
  "images": ["file:///abs/path/image.jpg"],
  "date": "2024-05-14T12:00:00+00:00",
  "links": ["https://monobank.ua/..."]
}
```

AI (`ai_filter.py`) використовує zero-shot класифікатор `facebook/bart-large-mnli` і пропускає тільки "fundraising" або "report". Медійні файли зберігаються локально в `python_parser/downloads/` і віддаються як `file://` URI – адаптуйте логіку завантаження під власну інфраструктуру за потреби.

## Структура репозиторію

```
python_parser/
  ai_filter.py        # Zero-shot класифікація
  collector.py        # Основний цикл Telethon + HTTP
  utils.py            # Конфіг, нормалізація, менеджер стану
  requirements.txt
  session/
  downloads/
backend/
  src/
    api/server.ts     # Старт Express
    api/validators/   # Zod-схеми
    controllers/      # Бізнес-логіка роутів
    models/           # Mongoose-схеми
    routes/           # Express routers
    utils/            # env + Mongo конект
  package.json
  tsconfig.json
```

## .env налаштування

```ini
# Parser
API_ID=...
API_HASH=...
CHANNEL=my_channel
BACKEND_URL=http://localhost:3000/api/posts/import
BACKEND_TOKEN=
SESSION_NAME=tg-parser
MAX_MESSAGES=200

# Backend
NODE_ENV=development
PORT=3000
MONGODB_URI=mongodb://localhost:27017/tg_volunteer
INGEST_TOKEN=
```

## Рекомендації

- Для продакшену використай Cron/task runner, що викликає `python python_parser/collector.py --new` з бажаною періодичністю.
- Якщо Torch важко ставиться на Mac M1/M2, скористайся офіційною інструкцією `pip install torch --index-url https://download.pytorch.org/whl/cpu` перед встановленням requirements.
- Фронтенд може напряму звертатися до `GET /api/posts` та `GET /api/posts/:id` для відображення зборів/звітів.
