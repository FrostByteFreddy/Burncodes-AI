# backend/shared — code used by several services

The single source of truth for code that more than one backend service
(`api`, `worker_fast`, `worker_heavy`, `worker_chat`, `beat`) uses. A map of
everything: `.claude/skills/burncodes-codebase/references/backend.md`.

| Module | Does |
|---|---|
| `ai_models.py` | every model and price setting (read from `.env`) |
| `auth/` | `token_required` / `optional_user`, change password, delete account |
| `billing/services.py` | balance, charges (ledger), Stripe crediting |
| `database/` | Supabase service-role client, `fetch_all`, retries |
| `gemini_store/` | Gemini File Search stores and documents |
| `knowledge/` | the knowledge pipeline: crawl scope and pace, learning, dates, facts, names, review, branding |
| `logging_config.py` | `error_logger` |
| `models/` | enums (`CrawlingStatus`, `SourceType`) |
| `security/url_guard.py` | every fetch of a user-given URL goes through it |
| `soup_extractor.py` | light HTML fetch and link extraction |

## How services get it

- **Locally:** each service's `app/` holds relative symlinks to these files and
  folders (tracked by git). Edit the files here, never through a link.
- **In the images:** each service's `Dockerfile` copies what it needs with
  `COPY shared/<module> app/<module>`. A new module, or a new import of one, needs
  a `COPY` line in every Dockerfile whose service imports it, and a symlink in
  that service's `app/`.
- **`worker_chat` copies `knowledge/` file by file.** A missing line only shows
  in production, where every chat then fails on import;
  `backend/tests/test_images.py` checks the chat worker's imports.
- Build the image the way production does before relying on a new module:
  `docker build -f services/<service>/Dockerfile -t check .` (from `backend/`).
