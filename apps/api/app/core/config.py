import os

try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # noqa: BLE001 - dotenv is optional
    pass


class Settings:
    DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./data/aicte.db")
    DEMO_MODE = os.environ.get("DEMO_MODE", "northstar")  # northstar | aarohan

    # S3-compatible object storage (adobe/s3mock in dev, any S3 in prod)
    S3_ENDPOINT = os.environ.get("S3_ENDPOINT", "")
    S3_ACCESS_KEY = os.environ.get("S3_ACCESS_KEY", "foo")
    S3_SECRET_KEY = os.environ.get("S3_SECRET_KEY", "bar")
    S3_BUCKET = os.environ.get("S3_BUCKET", "aicte-documents")
    S3_SECURE = os.environ.get("S3_SECURE", "false").lower() in ("1", "true", "yes")

    MAX_UPLOAD_BYTES = int(os.environ.get("MAX_UPLOAD_BYTES", 25 * 1024 * 1024))

    # LLM (OpenAI-compatible; Groq free tier by default, model openai/gpt-oss-20b)
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.groq.com/openai/v1")
    LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
    LLM_MODEL = os.environ.get("LLM_MODEL", "openai/gpt-oss-20b")

    @property
    def llm_enabled(self) -> bool:
        return bool(self.LLM_BASE_URL and self.LLM_API_KEY and self.LLM_MODEL)

    @property
    def s3_enabled(self) -> bool:
        return bool(self.S3_ENDPOINT)


settings = Settings()
