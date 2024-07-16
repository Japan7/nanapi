from typing import Any
from zoneinfo import ZoneInfo

INSTANCE_NAME = 'nanapi'
LOG_LEVEL = 'INFO'
ERROR_WEBHOOK_URL = None
PROFILING = False

# FastAPI/Uvicorn
FASTAPI_APP = 'nanapi.fastapi:app'
FASTAPI_CONFIG: dict[str, Any] = dict()
HYPERCORN_CONFIG: dict[str, Any] = dict(workers=4, accesslog='-')
# Security
JWT_ALGORITHM = 'HS256'
JWT_EXPIRE_MINUTES = 30
# OpenAPI
OPENAPI_URL = '/openapi.json'
DOCS_URL = '/docs'
SWAGGER_UI_OAUTH2_REDIRECT_URL = DOCS_URL + '/oauth2-redirect'
REDOC_URL = '/redoc'

# EdgeDB
EDGEDB_CONFIG: dict[str, Any] = dict()

# Meilisearch
MEILISEARCH_HOST_URL = 'http://localhost:7700'
MEILISEARCH_CONFIG: dict[str, Any] = dict()

# General
TZ = ZoneInfo('Europe/Paris')
PRODUCER_UPLOAD_ENDPOINT = 'https://producer.japan7.bde.enseeiht.fr'
PRODUCER_TOKEN = ''

# AniList
LOW_PRIORITY_THRESH = 30

try:
    from .local_settings import *  # noqa: F403
except ImportError:
    raise Exception('A local_settings.py file is required to run this project')
