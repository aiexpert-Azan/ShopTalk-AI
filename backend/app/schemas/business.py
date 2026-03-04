"""Pydantic schemas for Business API request/response."""
from datetime import datetime, timezone
from typing import Any, Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.common import PyObjectId


def _ensure_datetime(value: Any) -> datetime:
    """Ensure value is a datetime for JSON serialization (e.g. from Cosmos DB)."""
    if value is None:
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    if hasattr(value, "isoformat"):
        return value
    return datetime.now(timezone.utc)


class BusinessCreate(BaseModel):
    """Schema for creating a business."""
    name: str = Field(..., min_length=1, max_length=200)
    owner_email: EmailStr
    password: str = Field(..., min_length=8)
    settings: dict = Field(default_factory=dict, description="Custom business settings")


class BusinessUpdate(BaseModel):
    """Schema for partial business update."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    owner_email: Optional[EmailStr] = None
    settings: Optional[dict] = None


class BusinessInDB(BaseModel):
    """Internal schema for business as stored (with _id)."""
    id: Optional[PyObjectId] = Field(None, alias="_id")
    name: str
    owner_email: str
    settings: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        from_attributes=True,
    )


class BusinessResponse(BaseModel):
    """Schema for business in API responses."""
    id: str = Field(..., description="Business ID (ObjectId string)")
    name: str
    owner_email: str
    settings: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_doc(cls, doc: dict) -> "BusinessResponse":
        """Build from MongoDB/Cosmos DB document."""
        doc_id = doc.get("_id")
        return cls(
            id=str(doc_id) if doc_id is not None else "",
            name=doc.get("name", ""),
            owner_email=doc.get("owner_email", ""),
            settings=doc.get("settings") if isinstance(doc.get("settings"), dict) else {},
            created_at=_ensure_datetime(doc.get("created_at")),
        )
