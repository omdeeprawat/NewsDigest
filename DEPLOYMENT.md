# Deployment

News Digest is not a long-running web server. It is a **batch job**: GitHub Actions starts a runner, the job connects to **Neon Postgres** over `DATABASE_URL`, runs `uv run python main.py`, then exits.

```text
GitHub Actions (cron 00:30 UTC)
        │
        │  secrets → env
        │
        ▼
  uv run python main.py
        │
        ├── SQLAlchemy ──► Neon (Postgres)
        ├── Groq API (summarize + rank + email copy)
        └── Gmail SMTP (digest email)
```

## Neon database

The app never hardcodes host or credentials. [`app/database/connection.py`](app/database/connection.py) reads `DATABASE_URL` and builds a SQLAlchemy engine with `pool_pre_ping=True` (useful if Neon scales to idle).

### 1. Create a Neon project

1. In the [Neon console](https://console.neon.tech), create a project (Postgres).
2. Copy the connection string. Use the **pooled** URL if Neon offers one (`-pooler` in the host) for short-lived jobs.
3. Prefer `sslmode=require` in the query string.

Example shape (do not commit real credentials):

```text
postgresql://USER:PASSWORD@ep-xxxxx.region.aws.neon.tech/neondb?sslmode=require
```

### 2. Create tables once

From a machine that can reach Neon (local or a one-off Actions run):

```bash
export DATABASE_URL="postgresql://..."
uv run python scripts/create_tables.py
```

That calls `Base.metadata.create_all` for:

- `youtube_videos`
- `openai_articles`
- `anthropic_articles`
- `digests`

The daily job assumes these tables already exist. It does not migrate schema on each run.

### 3. Point GitHub at Neon

In the GitHub repo: **Settings → Secrets and variables → Actions**.

| Secret | Used as | Role |
| --- | --- | --- |
| `NEON_DATABASE_URL` | `DATABASE_URL` | Neon connection string |
| `GROQ_API_KEY` | `GROQ_API_KEY` | Summaries, ranking, email intro |
| `MY_EMAIL` | `MY_EMAIL` | Gmail From/To |
| `APP_PASSWORD` | `APP_PASSWORD` | Gmail app password |

The workflow maps the Neon secret to the name the code expects:

```yaml
env:
  DATABASE_URL: ${{ secrets.NEON_DATABASE_URL }}
  GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
  MY_EMAIL: ${{ secrets.MY_EMAIL }}
  APP_PASSWORD: ${{ secrets.APP_PASSWORD }}
```

Local `.env` can use the same Neon URL so local runs and Actions share one database, or a Docker Postgres URL for isolation.

## GitHub Actions schedule

Workflow file: [`.github/workflows/daily_digest.yml`](.github/workflows/daily_digest.yml).

### Triggers

| Trigger | When |
| --- | --- |
| `schedule` cron `30 0 * * *` | Every day at **00:30 UTC** |
| `workflow_dispatch` | Manual run from the Actions tab |

GitHub cron is UTC and can drift by several minutes. Scheduled workflows on the default branch of public repos are more reliable than on unused branches; keep this workflow on the branch GitHub uses for schedules (typically `main` / `master`, or whatever is the default).

### Job steps

1. **Checkout** the repository (`actions/checkout@v4`).
2. **Python 3.12.9** (`actions/setup-python@v5`).
3. **Install uv** (`astral-sh/setup-uv@v6`).
4. **`uv sync --locked`** — install from `uv.lock`.
5. **`uv run python main.py`** — full digest pipeline with secrets injected as env vars.

The job runs on `ubuntu-latest`. There is no persistent disk: all state lives in Neon (scraped rows and digests) plus the emailed newsletter.

### Manual run

**Actions → Daily AI News Digest → Run workflow.** Use this after changing secrets, after `create_tables`, or to test without waiting for midnight UTC.

### Failure behavior

`main.py` exits `0` if the pipeline reports success (including “no new digests, email skipped”) and `1` otherwise. A failed email send is retried once inside [`app/daily_runner.py`](app/daily_runner.py). GitHub will mark the workflow red on non-zero exit.

## Checklist

- [ ] Neon project created; tables created via `scripts/create_tables.py`
- [ ] GitHub secrets: `NEON_DATABASE_URL`, `GROQ_API_KEY`, `MY_EMAIL`, `APP_PASSWORD`
- [ ] Workflow file on the branch that should run the schedule
- [ ] Manual `workflow_dispatch` succeeds
- [ ] Digest email arrives after a run that created new digests

## Alternate: Render

[`render.yaml`](render.yaml) describes a Render cron + Render Postgres blueprint. The current production path is **Neon + GitHub Actions**. If you use Render instead, set `DATABASE_URL` (or Render’s `fromDatabase` connection string) and the same Groq/Gmail env vars on that service.
