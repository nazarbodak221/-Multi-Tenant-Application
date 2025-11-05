import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    # Application
    APP_NAME: str = os.getenv("APP_NAME")
    DEBUG: bool = os.getenv("DEBUG")
    API_V1_PREFIX: str = os.getenv("API_V1_PREFIX")

    # Core Database
    CORE_DB_HOST: str = os.getenv("CORE_DB_HOST")
    CORE_DB_PORT: int = os.getenv("CORE_DB_PORT")
    CORE_DB_NAME: str = os.getenv("CORE_DB_NAME")
    CORE_DB_USER: str = os.getenv("CORE_DB_USER")
    CORE_DB_PASSWORD: str = os.getenv("CORE_DB_PASSWORD")

    # Tenant Database Template
    TENANT_DB_HOST: str = os.getenv("TENANT_DB_HOST")
    TENANT_DB_PORT: int = os.getenv("TENANT_DB_PORT")
    TENANT_DB_USER: str = os.getenv("TENANT_DB_USER")
    TENANT_DB_PASSWORD: str = os.getenv("TENANT_DB_PASSWORD")

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES")

    # Tenant
    TENANT_HEADER_NAME: str = os.getenv("TENANT_HEADER_NAME", "X-Tenant-Id")

    @property
    def core_database_url(self) -> str:
        return f"postgres://{self.CORE_DB_USER}:{self.CORE_DB_PASSWORD}@{self.CORE_DB_HOST}:{self.CORE_DB_PORT}/{self.CORE_DB_NAME}"

    def tenant_database_url(self, tenant_id: str) -> str:
        db_name = f"tenant_{tenant_id}"
        return f"postgres://{self.TENANT_DB_USER}:{self.TENANT_DB_PASSWORD}@{self.TENANT_DB_HOST}:{self.TENANT_DB_PORT}/{db_name}"


@lru_cache
def get_settings() -> Settings:
    return Settings()
