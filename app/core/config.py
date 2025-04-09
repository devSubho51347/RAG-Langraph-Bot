from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings using Pydantic BaseSettings."""
    
    # Database
    DATABASE_URL: str
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Convert DATABASE_URL to async version."""
        return self.DATABASE_URL.replace('postgresql://', 'postgresql+asyncpg://', 1) \
            if self.DATABASE_URL.startswith('postgresql://') \
            else self.DATABASE_URL
    
    # Vector DB
    QDRANT_URL: str
    QDRANT_API_KEY: Optional[str] = None
    
    # OpenAI
    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-ada-002"
    LLM_MODEL: str = "gpt-3.5-turbo"
    
    # LangSmith
    LANGSMITH_API_KEY: str
    
    # Auth
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
