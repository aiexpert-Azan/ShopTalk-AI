"""Pydantic schemas for Product (Inventory) API request/response."""
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.common import PyObjectId


def _ensure_datetime(value: Any) -> datetime:
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    return datetime.now(timezone.utc)


class ProductCreate(BaseModel):
    """Schema for creating a product."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    price: float = Field(..., ge=0)
    category: Optional[str] = None
    stock: int = Field(0, ge=0)
    business_id: str = Field(..., description="Owner business ID")


class ProductUpdate(BaseModel):
    """Schema for partial product update."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    category: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)


class ProductInDB(BaseModel):
    """Internal schema for product as stored."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    stock: int = 0
    business_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )


class ProductResponse(BaseModel):
    """Schema for product in API responses."""
    id: str
    name: str
    description: Optional[str] = None
    price: float
    category: Optional[str] = None
    stock: int = 0
    business_id: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_doc(cls, doc: dict) -> "ProductResponse":
        """Build from MongoDB/Cosmos DB document."""
        doc_id = doc.get("_id")
        return cls(
            id=str(doc_id) if doc_id is not None else "",
            name=doc.get("name", ""),
            description=doc.get("description"),
            price=float(doc.get("price", 0)),
            category=doc.get("category"),
            stock=int(doc.get("stock", 0)),
            business_id=doc.get("business_id", ""),
            created_at=_ensure_datetime(doc.get("created_at")),
        )
