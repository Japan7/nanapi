from pydantic_ai.models.google import GoogleModel
from pydantic_ai.providers.google import GoogleProvider

NANAPI_CLIENT_ID = ''

EMBEDDING_MODEL_NAME = 'text-embedding-3-large'
EMBEDDING_MODEL_MAX_TOKENS = 8192

PYDANTIC_AI_MODEL_CLS = GoogleModel
PYDANTIC_AI_DEFAULT_MODEL_NAME = 'gemini-2.5-flash-preview'
PYDANTIC_AI_PROVIDER = GoogleProvider()
