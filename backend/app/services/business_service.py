"""Business logic and async MongoDB operations for Business CRUD."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.business import BusinessCreate, BusinessUpdate
from app.core.security import get_password_hash


COLLECTION = "businesses"


class BusinessService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[COLLECTION]

    async def create(self, business_in: BusinessCreate) -> dict:
        """Insert one business. Password is hashed before storage."""
        now = datetime.now(timezone.utc)
        doc = {
            "name": business_in.name,
            "owner_email": business_in.owner_email.lower(),
            "hashed_password": get_password_hash(business_in.password),
            "settings": business_in.settings,
            "created_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def list(self, skip: int = 0, limit: int = 100) -> List[dict]:
        """List businesses with skip/limit; sort by created_at desc."""
        cursor = self.collection.find({}).sort("created_at", -1).skip(skip).limit(limit)
        return await cursor.to_list(length=limit)

    async def get_by_id(self, business_id: str) -> Optional[dict]:
        """Get a business by ObjectId string."""
        if not ObjectId.is_valid(business_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(business_id)})
        return doc

    async def get_by_email(self, owner_email: str) -> Optional[dict]:
        """Get a business by owner email (for login and uniqueness check)."""
        doc = await self.collection.find_one({"owner_email": owner_email.lower()})
        return doc

    async def update(self, business_id: str, business_in: BusinessUpdate) -> Optional[dict]:
        """Partially update a business. Returns updated document or None."""
        if not ObjectId.is_valid(business_id):
            return None
        update_data = business_in.model_dump(exclude_unset=True)
        if "owner_email" in update_data:
            update_data["owner_email"] = update_data["owner_email"].lower()
        if not update_data:
            return await self.get_by_id(business_id)
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(business_id)},
            {"$set": update_data},
            return_document=True,
        )
        return result

    async def delete(self, business_id: str) -> bool:
        """Delete a business by ID. Returns True if deleted."""
        if not ObjectId.is_valid(business_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(business_id)})
        return result.deleted_count > 0
