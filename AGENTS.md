# nanapi - Agent Instructions

## Project Overview

FastAPI + Gel (EdgeDB) backend for the Nana-chan Discord bot ecosystem. Manages anime/manga data (AniList integration), Discord users, waifu collecting game (WaiColle), projections, quizzes, and more.

## Architecture

### Layer Structure

```
dbschema/*.esdl          → Gel/EdgeDB schema definitions (modules: anilist, waicolle, user, discord, etc.)
nanapi/database/<module>/ → Auto-generated query files (.edgeql + .py pairs)
nanapi/models/            → Pydantic models for API request/response bodies
nanapi/routers/           → FastAPI route handlers (one per domain)
nanapi/utils/             → Shared utilities (clients, security, etc.)
nanapi/tasks/             → Background/cron tasks (anilist sync, meilisearch indexing)
```

### Database Query Pattern (Critical)

The project uses `gel-pydantic-codegen` to generate Python bindings from `.edgeql` files:

1. Write queries in `nanapi/database/<module>/<query_name>.edgeql`
2. Run build task: `uv run gel-pydantic-codegen nanapi/database/`
3. Import generated function and result type from the corresponding `.py` file

**Example** - [chara_select.edgeql](nanapi/database/anilist/chara_select.edgeql) generates [chara_select.py](nanapi/database/anilist/chara_select.py):

```python
from nanapi.database.anilist.chara_select import CharaSelectResult, chara_select
result = await chara_select(get_edgedb(), ids_al=[1, 2, 3])
```

**Never edit generated `.py` files in `nanapi/database/` directly** - they are overwritten by codegen.

### Router Authentication Patterns

Use `NanAPIRouter` with auth decorators defined in [nanapi/utils/fastapi.py](nanapi/utils/fastapi.py):

- `router.public.get(...)` - No auth
- `router.basic_auth.get(...)` - HTTP Basic auth (for OpenAPI docs)
- `router.oauth2.get(...)` - JWT OAuth2 token auth
- `router.oauth2_client.get(...)` - OAuth2 + client context (sets `global client_id` for Gel policies)

### Multi-tenancy via Gel Globals

The `default::ClientObject` abstract type uses Gel access policies with `global client_id`. Routes using `oauth2_client` decorator automatically scope data to the authenticated client.

## Key Commands

```sh
# Run dev server
uv run --frozen -m nanapi
# Or with hot reload (via VS Code launch config)
uvicorn nanapi.fastapi:app --reload

# Regenerate database bindings after editing .edgeql files
uv run gel-pydantic-codegen nanapi/database/

# Gel/EdgeDB CLI
gel ui              # Web UI
gel migration create  # After schema changes
gel migrate

# Type checking & linting
uv run pyright
uv run ruff check --fix
uv run ruff format
```

## Code Conventions

- **Type hints**: Strict pyright mode - all code must be fully typed
- **Formatting**: Ruff with single quotes (`quote-style = "single"`)
- **Imports**: Auto-sorted by ruff (isort rules)
- **Long lines in database/**: Allowed (E501 ignored for `nanapi/database/*`)

### Pydantic Models

- Request bodies in `nanapi/models/<domain>.py`
- Database result types are auto-generated in `nanapi/database/<module>/<query>.py`
- Use `model_dump()` for serialization, `to_edgedb()` method for DB-specific transforms

### EdgeQL/Gel Schema

- Each domain has its own module (`module anilist { ... }`)
- Use `extending default::ClientObject` for multi-tenant types
- Computed properties and links are common (e.g., `property rank := ...` in Character)

## Reflex Frontend

The project includes a Reflex-based frontend in [nanapi/reflex/](nanapi/reflex/) that shares the same process as FastAPI via `api_transformer`.

### Structure

```
nanapi/reflex/
├── app.py              → App entry, merges Reflex with FastAPI
├── state.py            → BaseState with Gel client properties
├── index/              → Root landing page
└── nanalook/           → Main feature: projection calendar viewer
    ├── state.py        → NanalookState extends BaseState
    ├── pages/          → Route handlers (index, projection, custom)
    ├── components/     → Reusable UI (layout, fullcalendar, participants)
    └── utils/          → Helper functions
```

### Key Patterns

**Multi-tenant state** - `BaseState` provides Gel executors:

```python
class BaseState(rx.State):
    @property
    def _client_executor(self) -> gel.AsyncIOClient | None:
        return self._global_executor.with_globals(client_id=self.client_id)
```

**Dynamic routes** - Pages use `[client_id]` path parameter:

```python
@rx.page(route='[client_id]/nanalook/', on_load=NanalookState.load_projections)
def index() -> rx.Component:
```

**Run Reflex dev server**: `uv run reflex run` (or VS Code launch config "Python Debugger: Reflex")

## External Dependencies

- **Gel/EdgeDB** (v6.11): Graph-relational database
- **Meilisearch**: Full-text search for anime/character autocomplete
- **AniList API**: Anime/manga metadata source (rate-limited, see `AL_LOW_PRIORITY_THRESH`)
- **Producer**: Japan7 image upload service

## Settings

Copy `nanapi/example.local_settings.py` → `nanapi/local_settings.py` and configure required secrets (see file for documentation).
