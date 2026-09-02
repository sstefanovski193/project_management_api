import os

from pydantic_settings import BaseSettings, SettingsConfigDict

env_file = ".env.test" if os.getenv("APP_ENV") == "test" else ".env"


class Settings(BaseSettings):
    database_url: str

    jwt_secret_key: str
    jwt_algorithm: str
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=env_file, extra="ignore")


settings = Settings()
