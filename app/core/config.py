from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_DB: str
    PROJECT_NAME: str = "School Billing API"

    class Config:
        env_file = ".env"


settings = Settings()
