# nanapi Development Guide

## Architecture Overview

This is a **FastAPI backend** using **EdgeDB** (via Gel) and **Meilisearch** for the Discord bot [nanachan](https://github.com/Japan7/nanachan). The codebase follows a **multi-tenant architecture** with client-based access control using EdgeDB's global variables.

### Key Components

- **Database Layer** (`nanapi/database/`): Auto-generated Python bindings from EdgeQL queries via `gel-pydantic-codegen`
- **Schema Layer** (`dbschema/`): EdgeDB schema files organized by module (`.esdl` files)
- **API Layer** (`nanapi/routers/`): FastAPI routers with custom authentication decorators
- **Models** (`nanapi/models/`): Pydantic models for API request/response bodies
- **Tasks** (`nanapi/tasks/`): Background jobs (primarily for syncing Meilisearch indexes)

## Database Workflow (EdgeDB + Gel)

### Schema Changes & Migrations

When modifying `.esdl` schema files:
1. Edit the schema in `dbschema/<module>.esdl`
2. Create migration: `gel migration create` (follow prompts - auto-generated)
3. Apply migration: `gel migration apply`

### Query Pattern

1. Write EdgeQL in `nanapi/database/<module>/<query_name>.edgeql`
2. Run codegen: `uv run gel-pydantic-codegen nanapi/database/` (or use the build task)
3. Import and use the generated function with `AsyncIOExecutor`

**Example:**
```python
from nanapi.database.waicolle.player_get_by_user import player_get_by_user
from nanapi.utils.fastapi import get_client_edgedb

# In a router:
async def my_endpoint(db: gel.AsyncIOClient = Depends(get_client_edgedb)):
    result = await player_get_by_user(db, user_id=...)
```

**EdgeQL conventions:**
- Use `<optional type>$param` for optional parameters: `<optional str>$discord_id`
- Use `str` type for Discord snowflake IDs (avoids JavaScript parseInt overflow issues)
- Use `json_get(obj, 'key1', 'key2', ...)` for safe JSON path access (returns empty set if path doesn't exist)
- For EdgeQL syntax and stdlib functions, consult **Context7**: https://context7.com/websites/geldata

### Multi-Tenant Access Control

EdgeDB uses **global variables** for tenant isolation:
- Schema defines: `global client_id -> uuid` and `global client := (select Client filter .id = global client_id)`
- Most types extend `ClientObject` which has row-level security policies
- In routers, use `get_client_edgedb()` which injects `client_id` via `.with_globals(client_id=...)`

**Never bypass this pattern** - queries automatically filter by the global client.

## Authentication & Authorization

### NanAPIRouter Decorators

The custom `NanAPIRouter` class provides auth variants:

- `@router.public.<method>` - No authentication
- `@router.basic_auth.<method>` - HTTP Basic Auth (for API docs access)
- `@router.oauth2.<method>` - JWT token required
- `@router.oauth2_client.<method>` - JWT + optional client_id param
- `@router.oauth2_client_restricted.<method>` - JWT + client_id must match authenticated client

**Pattern:**
```python
from nanapi.utils.fastapi import NanAPIRouter

router = NanAPIRouter(prefix='/mymodule', tags=['mymodule'])

@router.oauth2_client.get('/')
async def my_endpoint(db = Depends(get_client_edgedb)):
    # db is already scoped to client_id
    ...
```

## Module Structure

The project is organized by **domain modules** (matches Discord bot features):

- `anilist` - AniList/MAL integration (anime/manga metadata)
- `waicolle` - Gacha collection game (waifus/husbandos)
- `projection` - Event projection planning
- `quizz` - Quiz system
- `calendar`, `pot`, `reminder`, `role`, `user`, etc.

Each module has:
- Schema: `dbschema/<module>.esdl`
- Queries: `nanapi/database/<module>/*.edgeql` + auto-generated `.py`
- Router: `nanapi/routers/<module>.py`
- Models (if needed): `nanapi/models/<module>.py`

## Adding a New Module/Endpoint

When adding new functionality, follow this workflow (order flexible):

1. **Create EdgeQL queries** in `nanapi/database/<module>/<query_name>.edgeql`
2. **Run codegen** to generate Python bindings: `uv run gel-pydantic-codegen nanapi/database/`
3. **Create router** in `nanapi/routers/<module>.py` with appropriate auth decorators
4. **Register router** in `nanapi/fastapi.py` (manual - add `app.include_router(<module>.router)`)
5. **Define models** in `nanapi/models/<module>.py` for request/response bodies
6. **Add utilities** in `nanapi/utils/` if needed for shared logic

**Example router registration in `fastapi.py`:**
```python
from nanapi.routers import mymodule
# ...
app.include_router(mymodule.router)
```

## Development Commands

```bash
# Run server (development)
uv run --frozen -m nanapi

# Run with uvicorn (for hot reload)
uv run uvicorn nanapi.fastapi:app --reload

# Code generation (EdgeQL → Pydantic)
uv run gel-pydantic-codegen nanapi/database/

# Type checking
uv run pyright

# Linting
uv run ruff check nanapi/
uv run ruff format --check nanapi/

# Database management
uv run gel project init     # Initialize EdgeDB
uv run gel migration create # Create migration after schema changes
uv run gel migration apply  # Apply pending migrations
uv run gel ui               # Web UI for EdgeDB

# Background tasks (run separately, not part of main app)
uv run -m nanapi.tasks.meilisearch  # Rebuild Meilisearch indexes
uv run -m nanapi.tasks.userlists    # Sync user lists
```

## Initial Setup

For complete development environment setup, see [nanadev](https://github.com/Japan7/nanadev).

**Quick local setup:**
1. Setup EdgeDB: `uv run gel project init`
2. Load initial data: Use `ghcr.io/japan7/gel-dump` image for a basic EdgeDB dump
3. Setup Meilisearch: `docker run -d --name meilisearch -p 7700:7700 getmeili/meilisearch:latest`
4. Configure settings: Copy `nanapi/example.local_settings.py` to `nanapi/local_settings.py`
5. Run codegen: `uv run gel-pydantic-codegen nanapi/database/`

## Dependency Management

- Use `uv` for package management
- **Always pin dependencies** in `pyproject.toml` (e.g., `"fastapi==0.120.1"`)
- Use `--frozen` flag (`uv run --frozen`) to ensure lockfile consistency
- Renovate bot handles dependency updates automatically

## Settings Configuration

Copy `nanapi/example.local_settings.py` to `nanapi/local_settings.py` and configure:
- `JWT_SECRET_KEY` - Required for auth
- `BASIC_AUTH_USERNAME/PASSWORD` - For API docs access
- `MAL_CLIENT_ID` - MyAnimeList integration
- EdgeDB/Meilisearch connection details (defaults usually work locally)

## External Services

- **EdgeDB** - Primary database (managed via Gel)
- **Meilisearch** - Full-text search for characters/media/staff (run via Docker)
  - Indexes synced via cron tasks in `nanapi/tasks/` (production)
  - Update indexes after database changes to fields used for full-text search
  - Run `uv run -m nanapi.tasks.meilisearch` locally to rebuild indexes
- **AniList API** - Anime/manga metadata (rate-limited to 70 req/min via `AL_LOW_PRIORITY_THRESH`)

## Background Tasks

Tasks in `nanapi/tasks/` are **run separately** (not part of the main FastAPI app):
- In production: Executed by Kubernetes CronJobs
- Locally: Run with `uv run -m nanapi.tasks.<module_name>`
- Common tasks:
  - `nanapi.tasks.meilisearch` - Rebuild search indexes
  - `nanapi.tasks.userlists` - Sync AniList user lists
  - `nanapi.tasks.anilist` - Update AniList data

## API Documentation

- FastAPI automatically converts **function docstrings** to OpenAPI descriptions
- Write clear docstrings - these are used as AI agent **tool descriptions in nanachan** (the Discord bot)
- API docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc)

## Error Handling

- Use `try/except` in routers and return appropriate HTTP status codes
- Production uses `ERROR_WEBHOOK_URL` (Discord webhook) to send all router exceptions
- EdgeDB constraint violations: Debug with trial and error, check schema constraints

## Code Style

- **Ruff** formatting with single quotes (`quote-style = 'single'`)
- **Pyright strict** mode (except generated code in `nanapi/database/`)
- Line length: 99 characters
- Generated database code (`.py` files in `nanapi/database/`) should never be manually edited

## Common Gotchas

- When adding new EdgeQL queries, always run codegen before importing
- Database functions take `AsyncIOExecutor` (use `get_edgedb()` or `get_client_edgedb()`)
- The `global client` filtering is automatic - don't add manual `.client = ...` filters
- EdgeQL files use snake_case, generated functions preserve this naming
- Meilisearch indexes need manual population via tasks in `nanapi/tasks/`
- **Routers must be manually registered** in `nanapi/fastapi.py` - no auto-discovery
- Use `async` functions wherever possible for better performance
- Discord snowflake IDs must be `str` type to avoid JavaScript parseInt overflow

## Wrapped Feature

The "Wrapped" feature provides Spotify Wrapped-style yearly statistics for Discord users. It's a good example of a **utility-based module** where complex logic lives in `nanapi/utils/` rather than in routers.

### Structure

```
nanapi/
├── database/discord/wrapped_*.edgeql      # Stats queries
├── models/wrapped.py                      # WrappedEmbed, WrappedResponse
├── routers/wrapped.py                     # GET /{discord_id} endpoint
└── utils/wrapped/
    ├── common.py                          # Shared utilities
    ├── messages.py                        # Message stats → embeds
    └── emotes.py                          # Emote stats → embeds
```

### Adding New Wrapped Stats

1. Create EdgeQL query in `nanapi/database/discord/wrapped_*.edgeql`
2. Run codegen: `uv run gel-pydantic-codegen nanapi/database/`
3. Create utility module in `nanapi/utils/wrapped/<stat_name>.py`:
   - Define templates and thresholds
   - Create `build_*_embeds()` function returning `list[WrappedEmbed]`
   - Create `get_*_embeds()` async function that queries and builds embeds
4. Import and add to router's `asyncio.gather()` call
