import os
from dotenv import load_dotenv

load_dotenv()

API_V1_STR: str = "/api/v1"
PROJECT_NAME: str = "RAG Chat API"
PROJECT_DESCRIPTION: str = "API for ingesting content, generating FAQs, and chatting with it."
PROJECT_VERSION: str = "1.0.0"

NUM_FAQS_TO_GENERATE: int = int(os.getenv("NUM_FAQS_TO_GENERATE", 5))
MAX_CRAWL_PAGES: int = int(os.getenv("MAX_CRAWL_PAGES", 1))

LLM_MODEL_DEFAULT: str = os.getenv("OPENROUTER_MODEL", "gpt-4o-mini") 
WEB_SEARCH_MODEL_DEFAULT: str = os.getenv("WEB_SEARCH_MODEL_DEFAULT", "perplexity/sonar-reasoning-pro")

EMBEDDING_MODEL_DEFAULT: str = os.getenv("EMBEDDING_MODEL_DEFAULT", "text-embedding-3-small")
EMBEDDING_MODEL_DIMENSION: int = int(os.getenv("EMBEDDING_MODEL_DIMENSION", 1536))

OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")
OPENROUTER_API_KEY: str = os.getenv("OPENROUTER_API_KEY")
FIRECRAWL_API_KEY: str = os.getenv("FIRECRAWL_API_KEY")
LLAMA_CLOUD_API_KEY: str = os.getenv("LLAMA_CLOUD_API_KEY")

SESSION_DB_URL: str = os.getenv("SESSION_DB_URL") 
SESSION_DB_TOKEN: str = os.getenv("SESSION_DB_TOKEN")

QDRANT_HOST: str = os.getenv("QDRANT_HOST")
QDRANT_API_KEY: str = os.getenv("QDRANT_API_KEY")
