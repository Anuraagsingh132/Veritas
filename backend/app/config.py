import os
from pathlib import Path
from pydantic import BaseModel
from dotenv import load_dotenv

# Load from .env if present
env_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

class Settings(BaseModel):
    APP_NAME: str = "Superjoin Fact Knowledge Layer"
    APP_VERSION: str = "1.0.0"
    HOST: str = os.getenv("HOST", "127.0.0.1")
    PORT: int = int(os.getenv("PORT", 8000))
    
    # LLM Settings
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    DEFAULT_MODEL: str = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
    FALLBACK_MODEL: str = os.getenv("LLM_FALLBACK_MODEL", "llama-3.1-8b-instant")
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    DATA_DIR: Path = BASE_DIR / "data"
    UPLOAD_DIR: Path = BASE_DIR / "uploads"
    DB_PATH: Path = DATA_DIR / "knowledge_layer.db"
    
    # Processing parameters (Brownie Points: large PDF handling)
    MAX_PAGES_DEFAULT: int = int(os.getenv("MAX_PAGES_PER_DOC", 100))
    PAGES_PER_CHUNK: int = int(os.getenv("BATCH_PAGES_PER_CHUNK", 3))

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
