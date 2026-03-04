"""
Database initialization and session management using Motor (async MongoDB).
Connection is managed via FastAPI lifespan to avoid NoneType errors.
"""
from typing import Optional

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from app.core.config import settings


class Database:
    """
    Async MongoDB client and database holder.
    Set in lifespan: connect() at startup, close() at shutdown.
    """

    client: Optional[AsyncIOMotorClient] = None
    db: Optional[AsyncIOMotorDatabase] = None

    async def connect(self) -> None:
        """Create Motor client and get database. Call once at app startup."""
        conn = settings.AZURE_COSMOS_CONNECTION_STRING
        if "<password>" in conn or "&lt;password&gt;" in conn:
            print(
                "WARNING: AZURE_COSMOS_CONNECTION_STRING still contains placeholder <password>. "
                "Replace it with your Cosmos DB primary key (Azure Portal → Cosmos DB account → Keys)."
            )
        self.client = AsyncIOMotorClient(conn)
        self.db = self.client[settings.DB_NAME]
        try:
            await self.client.admin.command("ping")
            print("Connected to Azure Cosmos DB (MongoDB)")
        except Exception as e:
            print(
                f"Cosmos DB ping note: {e}. "
                "If you see auth errors on requests, replace <password> in .env with your Cosmos DB primary key."
            )

    async def close(self) -> None:
        """Close Motor client. Call once at app shutdown."""
        if self.client is not None:
            self.client.close()
            self.client = None
            self.db = None
            print("Closed connection to Azure Cosmos DB")

    def get_db(self) -> AsyncIOMotorDatabase:
        """Return the database instance. Safe to call only after lifespan startup."""
        if self.db is None:
            raise RuntimeError(
                "Database is not initialized. Ensure FastAPI lifespan has run (startup)."
            )
        return self.db


# Singleton used by lifespan and get_database dependency
db = Database()


async def get_database() -> AsyncIOMotorDatabase:
    """FastAPI dependency: injects the Motor database instance."""
    return db.get_db()
