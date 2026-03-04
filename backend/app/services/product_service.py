"""Business logic and async MongoDB operations for Product (Inventory) CRUD."""
from datetime import datetime, timezone
from typing import List, Optional

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.schemas.product import ProductCreate, ProductUpdate


COLLECTION = "products"


class ProductService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.collection = db[COLLECTION]

    async def create(self, product_in: ProductCreate) -> dict:
        """Insert one product."""
        now = datetime.now(timezone.utc)
        doc = {
            "name": product_in.name,
            "description": product_in.description,
            "price": product_in.price,
            "category": product_in.category,
            "stock": product_in.stock,
            "business_id": product_in.business_id,
            "created_at": now,
        }
        result = await self.collection.insert_one(doc)
        doc["_id"] = result.inserted_id
        return doc

    async def list(
        self,
        business_id: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        category: Optional[str] = None,
    ) -> List[dict]:
        """List products; filter by business_id and optional category."""
        filt: dict = {}
        if business_id:
            filt["business_id"] = business_id
        if category is not None and category != "":
            filt["category"] = category
        cursor = (
            self.collection.find(filt)
            .sort("created_at", -1)
            .skip(skip)
            .limit(limit)
        )
        return await cursor.to_list(length=limit)

    async def get_by_id(self, product_id: str) -> Optional[dict]:
        """Get a product by ObjectId string."""
        if not ObjectId.is_valid(product_id):
            return None
        doc = await self.collection.find_one({"_id": ObjectId(product_id)})
        return doc

    async def update(self, product_id: str, product_in: ProductUpdate) -> Optional[dict]:
        """Partially update a product. Returns updated document or None."""
        if not ObjectId.is_valid(product_id):
            return None
        update_data = product_in.model_dump(exclude_unset=True)
        if not update_data:
            return await self.get_by_id(product_id)
        result = await self.collection.find_one_and_update(
            {"_id": ObjectId(product_id)},
            {"$set": update_data},
            return_document=True,
        )
        return result

    async def delete(self, product_id: str) -> bool:
        """Delete a product by ID. Returns True if deleted."""
        if not ObjectId.is_valid(product_id):
            return False
        result = await self.collection.delete_one({"_id": ObjectId(product_id)})
        return result.deleted_count > 0
