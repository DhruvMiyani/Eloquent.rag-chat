"""Configuration settings for the API."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    # OpenAI
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

    # Pinecone
    PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
    PINECONE_INDEX = os.getenv("PINECONE_INDEX", "ai-powered-chatbot-challenge")
    PINECONE_ENDPOINT = os.getenv("PINECONE_ENDPOINT")

    # Database
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chat_database.db")
    USE_DYNAMODB = os.getenv("USE_DYNAMODB", "false").lower() == "true"

    # AWS
    AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
    DYNAMODB_TABLE_PREFIX = os.getenv("DYNAMODB_TABLE_PREFIX", "chatbot")

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here-change-in-production")
    ALGORITHM = os.getenv("ALGORITHM", "HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    # CORS
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

    # RAG Settings
    VECTOR_SEARCH_TOP_K = int(os.getenv("VECTOR_SEARCH_TOP_K", "6"))
    LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
    MAX_CONTEXT_LENGTH = int(os.getenv("MAX_CONTEXT_LENGTH", "3000"))

settings = Settings()