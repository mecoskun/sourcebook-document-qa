from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT = Path(__file__).resolve().parents[1]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="QA_", env_file=ROOT / ".env", extra="ignore")
    model_url: str = "http://127.0.0.1:8081/v1"
    model_name: str = "sourcebook"
    model_api_key: str = ""
    embedding_model: str = "BAAI/bge-small-en"
    embedding_path: Path = ROOT / ".models" / "embedding"
    cache_dir: Path = ROOT / ".models"
    allowed_origins: list[str] = ["http://127.0.0.1:4173", "http://localhost:4173"]
    session_ttl_seconds: int = 3600
    max_sessions: int = 20
    max_documents: int = 5
    max_file_bytes: int = 10 * 1024 * 1024
    max_text_chars: int = 150_000
    max_pages: int = 100
    max_chunks: int = 250
    daily_questions: int = 200
    daily_uploads: int = 100
    per_session_questions: int = 20
    min_similarity: float = 0.80
    model_timeout: int = 120
    max_output_tokens: int = 600


settings = Settings()
