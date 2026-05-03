from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    postgres_url: str = "postgresql://airflow:airflow@localhost:5432/airflow"
    opensearch_url: str = "http://localhost:9200"
    
    class Config:
        env_file = ".env"

settings = Settings()
