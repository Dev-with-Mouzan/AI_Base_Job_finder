import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APIFY_API_KEY: str = "YOUR_APIFY_API_KEY"
    EMBED_MODEL: str = "nomic-embed-text:latest"
    LLM_MODEL: str = "llama3.2:latest"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
