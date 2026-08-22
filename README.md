# News Digest

A scheduled AI news aggregator that scrapes recent content from YouTube, OpenAI, and Anthropic, stores it in Postgres, summarizes it with Groq, ranks items against a personal profile, and emails a daily digest.

The production path is a GitHub Actions cron job talking to a [Neon](https://neon.tech) Postgres database. See [DEPLOYMENT.md](DEPLOYMENT.md) for Neon wiring, secrets, and scheduling.

## How it works

`uv run python main.py` (or `python main.py`) runs a five-step pipeline in [`app/daily_runner.py`](app/daily_runner.py):

1. **Scrape** — Pull items published in the last 24 hours (configurable via `hours`).
   - YouTube channel RSS (channel IDs in [`app/config.py`](app/config.py))
   - OpenAI news RSS
   - Anthropic news / research / engineering RSS feeds
2. **Enrich Anthropic** — Fetch full article markdown with Trafilatura for rows that only have RSS metadata.
3. **Enrich YouTube** — Fetch transcripts for videos that do not have one yet.
4. **Digest** — For each new item, Groq (`openai/gpt-oss-20b`) writes a short title and summary. Results are stored in the `digests` table so the same article is not summarized twice.
5. **Email** — If any new digests were created:
   - Load recent digests
   - Rank them against [`app/profiles/user_profile.py`](app/profiles/user_profile.py)
   - Write an intro and HTML email
   - Send via Gmail SMTP (`smtp.gmail.com:465`)

If there are no new digests, the email step is skipped and the run still counts as success.

Optional CLI args on `main.py`:

```bash
uv run python main.py           # last 24 hours, top 10 ranked items
uv run python main.py 48 5      # last 48 hours, top 5
```

## Folder structure

```text
news-digest/
├── main.py                      # CLI entry: hours, top_n → daily pipeline
├── pyproject.toml               # Project metadata and dependencies (uv)
├── uv.lock                      # Locked dependency versions
├── .python-version              # Python 3.12.x
├── .github/workflows/
│   └── daily_digest.yml         # Daily schedule + manual dispatch
├── scripts/
│   └── create_tables.py         # SQLAlchemy create_all against DATABASE_URL
├── docker/
│   └── docker-compose.yml       # Local Postgres 17
├── render.yaml                  # Alternate Render cron + DB blueprint (legacy)
└── app/
    ├── config.py                # YouTube channel IDs to follow
    ├── daily_runner.py          # Orchestrates scrape → process → digest → email
    ├── runner.py                # Runs scrapers and writes raw rows
    ├── example.env              # Sample local Postgres env vars
    ├── agent/
    │   ├── digest_agent.py      # Per-article summary (Groq)
    │   ├── curator_agent.py     # Rank digests for the user
    │   └── email_agent.py       # Greeting + intro for the email
    ├── database/
    │   ├── connection.py        # SQLAlchemy engine from DATABASE_URL
    │   ├── models.py            # youtube_videos, openai_articles, anthropic_articles, digests
    │   └── repository.py        # CRUD, dedupe, “items missing digest”
    ├── profiles/
    │   └── user_profile.py      # Interests used by the curator
    ├── scrapers/
    │   ├── youtube.py
    │   ├── openai.py
    │   └── anthropic.py
    └── services/
        ├── process_anthropic.py
        ├── process_youtube.py
        ├── process_digest.py
        ├── process_email.py
        └── email_service.py     # Gmail send + HTML conversion
```

### Data model

| Table | Purpose |
| --- | --- |
| `youtube_videos` | Video metadata + optional transcript |
| `openai_articles` | OpenAI RSS items |
| `anthropic_articles` | Anthropic RSS items + optional full markdown |
| `digests` | One summary per source item (`id` = `{origin}:{article_id}`) |

Duplicates are skipped by primary key (`video_id` / `guid` / digest `id`).

## Local setup

Requirements: Python 3.12+, [uv](https://docs.astral.sh/uv/), Docker (for local Postgres) or a Neon connection string.

```bash
uv sync
```

Create a `.env` in the repo root (gitignored). Production uses a Neon URL; locally you can use Docker Postgres or Neon.

```env
DATABASE_URL=postgresql://USER:PASSWORD@HOST/DB?sslmode=require
GROQ_API_KEY=gsk_...
MY_EMAIL=you@gmail.com
APP_PASSWORD=your-gmail-app-password
```

Start local Postgres (optional):

```bash
docker compose -f docker/docker-compose.yml up -d
```

Create tables:

```bash
uv run python scripts/create_tables.py
```

Run the pipeline:

```bash
uv run python main.py
```

Gmail sending needs an [App Password](https://support.google.com/accounts/answer/185833), not your normal account password.

## Stack

- **Runtime:** Python 3.12, uv
- **DB:** Postgres (Neon in production, Docker locally) via SQLAlchemy + psycopg2
- **LLM:** Groq
- **Sources:** RSS (`feedparser`), YouTube transcripts, Trafilatura
- **Schedule:** GitHub Actions cron (see [DEPLOYMENT.md](DEPLOYMENT.md))
