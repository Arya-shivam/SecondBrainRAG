from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_url: str = "postgresql://airflow:airflow@postgres:5432/postgres"
    opensearch_url: str = "http://opensearch:9200"
    
    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
