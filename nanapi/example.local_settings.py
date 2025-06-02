# TODO: Uncommented variables must be set to work properly.

# from zoneinfo import ZoneInfo

# LOG_LEVEL = 'INFO'
# ERROR_WEBHOOK_URL = None
# PROFILING = False

## General
# INSTANCE_NAME = 'nanapi'
# TZ = ZoneInfo('Europe/Paris')

## EdgeDB
# EDGEDB_CONFIG = dict()

## Meilisearch
# MEILISEARCH_HOST_URL = 'http://localhost:7700'
# MEILISEARCH_CONFIG = dict()

## FastAPI/Uvicorn
# FASTAPI_APP = 'nanapi.fastapi:app'
# FASTAPI_CONFIG = dict()
# HYPERCORN_CONFIG = dict(workers=4, accesslog='-')

## Security
BASIC_AUTH_USERNAME = 'username'
BASIC_AUTH_PASSWORD = 'password'
# JWT_ALGORITHM = 'HS256'
# JWT_EXPIRE_MINUTES = 30
JWT_SECRET_KEY = ''  # openssl rand -hex 32

## OpenAPI
# OPENAPI_URL = '/openapi.json'
# DOCS_URL = '/docs'
# SWAGGER_UI_OAUTH2_REDIRECT_URL = DOCS_URL + '/oauth2-redirect'
# REDOC_URL = '/redoc'

## AniList
# AL_LOW_PRIORITY_THRESH = 30

## MyAnimeList
MAL_CLIENT_ID = ''

## Producer
# PRODUCER_UPLOAD_ENDPOINT = 'https://producer.japan7.bde.enseeiht.fr'
# PRODUCER_TOKEN = ''

## AI
# AI_EMBEDDING_MODEL_NAME = 'text-embedding-3-small'
# AI_EMBEDDING_MODEL_MAX_TOKENS = 8192
# AI_MESSAGEPAGES_FOR_CLIENTS = []
