import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.api.v1 import api_router
from app.db.mongodb import db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage database connection lifecycle; use async connect/close to avoid NoneType."""
    await db.connect()
    try:
        yield
    finally:
        await db.close()


def _is_db_error(exc: Exception) -> bool:
    return "pymongo" in type(exc).__module__ or "motor" in type(exc).__module__


def _is_openai_error(exc: Exception) -> bool:
    return "openai" in type(exc).__module__


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    """Turn unhandled exceptions into structured 500/503 so clients see a clear message."""
    logger.exception("Unhandled exception: %s", exc)
    if _is_db_error(exc):
        detail = (
            "Database error. Check Azure Cosmos DB: "
            "replace <password> in AZURE_COSMOS_CONNECTION_STRING with your Cosmos DB primary key (Azure Portal → Cosmos DB → Keys)."
        )
        if "<password>" in (getattr(settings, "AZURE_COSMOS_CONNECTION_STRING", "") or ""):
            detail = (
                "Database connection failed: .env still has placeholder <password>. "
                "In Azure Portal go to your Cosmos DB account → Keys → copy Primary Key and replace <password> in AZURE_COSMOS_CONNECTION_STRING."
            )
        return JSONResponse(
            status_code=503,
            content={"detail": detail, "error_type": "database"},
        )
    if _is_openai_error(exc):
        detail = (
            "Azure OpenAI error. Check Azure Portal: "
            "API key, endpoint (no extra quotes in .env), and deployment name (e.g. gpt-4o-mini)."
        )
        return JSONResponse(
            status_code=502,
            content={"detail": detail, "error_type": "openai"},
        )
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error.", "error_type": "internal"},
    )


if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "Welcome to ShopTalk-AI Backend"}
