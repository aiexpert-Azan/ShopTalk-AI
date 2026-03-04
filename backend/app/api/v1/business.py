"""
Business Management: full CRUD with async MongoDB (Motor).
Collection: businesses. Documents include hashed_password (never expose in response).
"""
from typing import Any, List

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.db.mongodb import get_database
from app.schemas.business import BusinessCreate, BusinessUpdate, BusinessResponse
from app.core.security import get_password_hash
from app.services.business_service import BusinessService

router = APIRouter()


def _business_service(db=Depends(get_database)) -> BusinessService:
    return BusinessService(db)


@router.post("/", response_model=BusinessResponse, status_code=status.HTTP_201_CREATED)
async def create_business(
    business_in: BusinessCreate,
    service: BusinessService = Depends(_business_service),
) -> Any:
    """Create a new business. Password is hashed before storage."""
    existing = await service.get_by_email(business_in.owner_email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A business with this owner email already exists.",
        )
    doc = await service.create(business_in)
    return BusinessResponse.from_doc(doc)


@router.get("/", response_model=List[BusinessResponse])
async def list_businesses(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: BusinessService = Depends(_business_service),
) -> Any:
    """List businesses with optional pagination."""
    docs = await service.list(skip=skip, limit=limit)
    return [BusinessResponse.from_doc(d) for d in docs]


@router.get("/{business_id}", response_model=BusinessResponse)
async def get_business(
    business_id: str,
    service: BusinessService = Depends(_business_service),
) -> Any:
    """Get a single business by ID."""
    doc = await service.get_by_id(business_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    return BusinessResponse.from_doc(doc)


@router.patch("/{business_id}", response_model=BusinessResponse)
async def update_business(
    business_id: str,
    business_in: BusinessUpdate,
    service: BusinessService = Depends(_business_service),
) -> Any:
    """Partially update a business."""
    doc = await service.update(business_id, business_in)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
    return BusinessResponse.from_doc(doc)


@router.delete("/{business_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business(
    business_id: str,
    service: BusinessService = Depends(_business_service),
) -> None:
    """Delete a business by ID."""
    deleted = await service.delete(business_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )
