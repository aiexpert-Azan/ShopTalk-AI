"""
Application configuration via environment variables.
Uses pydantic-settings with .env (AZURE_OPENAI_API_KEY, AZURE_COSMOS_CONNECTION_STRING, etc.).
"""
from typing import List, Union
import json
from urllib.parse import quote_plus

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _escape_mongodb_uri_password(uri: str) -> str:
    """
    Escape the password in a MongoDB URI per RFC 3986. The password may contain
    special chars (e.g. @, +, =, /). Use the *last* @ to split userinfo from host,
    since the password can contain @.
    """
    if "://" not in uri or "@" not in uri:
        return uri
    try:
        scheme, rest = uri.split("://", 1)
        # Last @ separates user:password from host (password can contain @)
        userinfo, _, host_part = rest.rpartition("@")
        if ":" not in userinfo:
            return uri
        username, password = userinfo.split(":", 1)
        password_escaped = quote_plus(password)
        return f"{scheme}://{username}:{password_escaped}@{host_part}"
    except Exception:
        return uri


class Settings(BaseSettings):
    """Load from .env; compatible with Azure and JWT env vars."""

    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "ShopTalk-AI"

    # Azure Cosmos DB (MongoDB API)
    AZURE_COSMOS_CONNECTION_STRING: str
    DB_NAME: str = "shoptalk_db"

    # Azure OpenAI
    AZURE_OPENAI_API_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT_NAME: str = "gpt-4o-mini"
    AZURE_OPENAI_API_VERSION: str = "2024-07-18"

    # JWT Auth
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days

    # CORS (supports JSON array string in .env e.g. ["http://localhost", "*"])
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost", "http://localhost:3000"]

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            v = v.strip()
            if v.startswith("["):
                try:
                    return json.loads(v)
                except json.JSONDecodeError:
                    return [i.strip() for i in v.strip("[]").replace('"', "").split(",")]
            return [i.strip() for i in v.split(",")] if v else []
        if isinstance(v, list):
            return list(v)
        return []

    @field_validator("AZURE_OPENAI_ENDPOINT", mode="before")
    @classmethod
    def strip_endpoint(cls, v: str) -> str:
        if isinstance(v, str):
            v = v.strip().strip('"').strip("'").rstrip("/")
            return v
        return v

    @field_validator("AZURE_COSMOS_CONNECTION_STRING", mode="before")
    @classmethod
    def strip_connection_string(cls, v: str) -> str:
        """Remove quotes and escape password so special chars in Cosmos key don't cause InvalidURI."""
        if isinstance(v, str):
            v = v.strip().strip('"').strip("'")
            return _escape_mongodb_uri_password(v)
        return v

    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


def get_settings() -> Settings:
    """Return validated settings; raises on missing/invalid env."""
    return Settings()


# Module-level instance for backward compatibility (used by db, routers, services)
try:
    settings = get_settings()
except Exception as e:
    print("\n============================================================")
    print("FATAL CONFIGURATION ERROR: Missing or Invalid Environment Variables")
    print("============================================================")
    print(e)
    print("============================================================\n")
    raise
