"""
Inventory (Products) Management: full CRUD with async MongoDB (Motor).
Collection: products. Optional filter by business_id and category.
"""
from typing import Any, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.db.mongodb import get_database
from app.schemas.product import ProductCreate, ProductUpdate, ProductResponse
from app.services.product_service import ProductService

router = APIRouter()


def _product_service(db=Depends(get_database)) -> ProductService:
    return ProductService(db)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_in: ProductCreate,
    service: ProductService = Depends(_product_service),
) -> Any:
    """Create a new product (inventory item)."""
    doc = await service.create(product_in)
    return ProductResponse.from_doc(doc)


@router.get("/", response_model=List[ProductResponse])
async def list_products(
    business_id: Optional[str] = Query(None, description="Filter by business ID"),
    category: Optional[str] = Query(None, description="Filter by category"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    service: ProductService = Depends(_product_service),
) -> Any:
    """List products with optional filters and pagination."""
    docs = await service.list(
        business_id=business_id,
        category=category,
        skip=skip,
        limit=limit,
    )
    return [ProductResponse.from_doc(d) for d in docs]


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: str,
    service: ProductService = Depends(_product_service),
) -> Any:
    """Get a single product by ID."""
    doc = await service.get_by_id(product_id)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return ProductResponse.from_doc(doc)


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: str,
    product_in: ProductUpdate,
    service: ProductService = Depends(_product_service),
) -> Any:
    """Partially update a product."""
    doc = await service.update(product_id, product_in)
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return ProductResponse.from_doc(doc)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: str,
    service: ProductService = Depends(_product_service),
) -> None:
    """Delete a product by ID."""
    deleted = await service.delete(product_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
