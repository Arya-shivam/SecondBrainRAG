from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database connections
    # Use container hostnames (postgres/opensearch) when running inside Docker
    # Use localhost when running the server locally with `uv run`
    postgres_url: str = "postgresql://airflow:airflow@localhost:5432/postgres"
    opensearch_url: str = "http://localhost:9200"

    # OpenRouter — LLM & Embeddings gateway
    openrouter_api_key: str = ""
    openrouter_model: str = "openrouter/free"  # Free tier default
    embed_model: str = "nvidia/llama-nemotron-embed-vl-1b-v2:free"

    # Obsidian vault path (set in .env as OBSIDIAN_VAULT_PATH)
    obsidian_vault_path: str = r"C:\Second Brain"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
