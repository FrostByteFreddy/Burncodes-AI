# backend/shared — Shared Application Modules

This directory is the **single source of truth** for code that is used identically across all backend services (`api`, `worker_fast`, `worker_heavy`, `worker_chat`).

## Modules

| Module | Description |
|---|---|
| `auth/` | `@token_required` decorator + auth routes |
| `database/` | Supabase client singleton |
| `models/` | Pydantic domain models + Enums |
| `logging_config.py` | Rotating file + stdout logging setup |

## How it works

Each service's `app/` directory contains **relative symlinks** that point here:

```
backend/services/worker_fast/app/auth  →  ../../../../shared/auth
backend/services/worker_fast/app/database  →  ../../../../shared/database
# etc.
```

Git tracks symlinks natively, and Docker's `COPY` instruction dereferences them — so Dockerfiles require **no changes**: they continue to `COPY app/ .` and the shared files are resolved and included automatically.

## Rules

- **Only add truly shared code here.** If a module is service-specific, it belongs in that service's `app/` directory.
- **Edit files here, never in a service's `app/` directory** — those are just symlinks and changes would be lost.
- **Adding a new shared module**: copy it here, then create a symlink in each service's `app/` that needs it.
