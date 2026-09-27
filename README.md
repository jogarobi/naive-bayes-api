# Naive Bayes API

I've been learning Python and statistics these past couple of weeks and wanted to put my knowledge to the test by coding a simple API.

The project is a small FastAPI service that labels text messages as **spam** or **not spam** using multinomial bayes classifying. Training data is ingested via CSV, word statistics and inputs for computing classifications are kept in a PostgreSQL database.

The API is deployed on [Render](https://render.com/) and its Swagger is available at https://naive-bayes-api-icck.onrender.com/docs.

## How it works

All the statistics (e.g. total words, total messages, unique words per class, etc) the classifier needs live in the database and are updated incrementally as data is ingested:

1. **Ingestion** — You upload a CSV of labeled messages with the columns (`message`, `is_spam`). Each message is stored in `labeled_messages` with an MD5 hash used to reject duplicates.
2. **Aggregation** — A PostgreSQL `AFTER INSERT` trigger (`scripts.sql`) splits every new message into words, upserts per-word occurrence counts into `labeled_words`, and updates running totals in the `measures` table.
3. **Prediction** — At request time the classifier reads only the words present in the incoming message plus the aggregate measures, then computes class probabilities.

## Requirements

- Python >= 3.9
- A PostgreSQL database (developed against [Neon](https://neon.tech))

## Setup

Dependencies are managed with [uv](https://github.com/astral-sh/uv).

```bash
uv sync
```

Configure the database connection:

```bash
cp .env.example .env
# then set NEON_POSTGRES_DATABASE_URL in .env
```

Tables are created automatically on startup (`create_tables()` in `app/main.py`). The aggregation trigger must be installed once by running the SQL in `scripts.sql` against your database:

```bash
psql "$NEON_POSTGRES_DATABASE_URL" -f scripts.sql
```

## Running

```bash
fastapi dev app/main.py
```

Or with Docker:

```bash
docker build -t naive-bayes-api .
docker run -p 80:80 --env-file .env naive-bayes-api
```

Interactive docs are available at `/docs`.

## Endpoints

### `POST /dataset/ingest`

Upload a CSV of labeled training messages. Must be `text/csv` with `message` and `is_spam` columns (`is_spam` = `1` or `0`).

```bash
curl -X POST http://localhost:8000/dataset/ingest \
  -F "file=@dataset.csv;type=text/csv"
```

**Response**

```json
{
  "file": { "name": "dataset.csv", "size": 12345 }
}
```

Duplicate messages (same content, matched by hash) are rejected with `400`.

### `POST /message/predict`

Classify a single message. The message is passed as a query parameter.

```bash
curl -X POST "http://localhost:8000/message/predict?message=win%20a%20free%20prize%20now"
```

**Response**

```json
{
  "prediction": "spam",
  "details": {
    "spam": "98.72%",
    "not_spam": "1.28%"
  }
}
```

## Project layout

```
app/
  main.py       # app entrypoint, startup hooks, router wiring
  routes.py     # HTTP endpoints (ingest, predict)
  services.py   # database access (SQLAlchemy sessions and queries)
  models.py     # ORM models: LabeledMessage, LabeledWord, Measure
  utils.py      # Classifier (Naive Bayes math), CSV field-size helper
scripts.sql     # PostgreSQL trigger that maintains word/measure aggregates
tests/          # pytest suite for the classifier and routes
```

## Tests

```bash
uv run pytest
```
