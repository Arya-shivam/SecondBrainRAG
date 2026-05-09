from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database connections (use container hostnames inside Docker)
    postgres_url: str = "postgresql://airflow:airflow@postgres:5432/postgres"
    opensearch_url: str = "http://opensearch:9200"

    # OpenRouter — LLM & Embeddings gateway
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.1-8b-instruct:free"  # Free tier default
    embed_model: str = "nomic-ai/nomic-embed-text-v1.5"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
