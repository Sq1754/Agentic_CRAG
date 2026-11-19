from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DocuMind"
    env: str = "development"
    debug: bool = False

    # Qdrant (local: set qdrant_host/port; cloud: set qdrant_url + qdrant_api_key)
    qdrant_host: str = "localhost"
    qdrant_port: int = 6333
    qdrant_url: str = ""           # e.g. https://xxxx.us-east4-0.gcp.cloud.qdrant.io
    qdrant_api_key: str = ""       # required for Qdrant Cloud
    qdrant_collection: str = "tenant_corpus"

    # PostgreSQL
    database_url: str = "postgresql://documind:documind_dev@localhost:5432/documind"

    # Authentication
    jwt_secret_key: str = "change-this-to-a-random-64-char-secret-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 1440  # 24 hours

    # Models
    dense_model: str = "BAAI/bge-small-en-v1.5"
    reranker_model: str = "BAAI/bge-reranker-base"
    groq_model: str = "openai/gpt-oss-20b"
    groq_api_key: str = ""

    # File Upload (use /tmp/uploads on ephemeral cloud hosting like Render)
    max_upload_size_mb: int = 20
    upload_dir: str = "./uploads"

    # CORS
    cors_origins: str = "http://localhost:3000,http://localhost:8000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
