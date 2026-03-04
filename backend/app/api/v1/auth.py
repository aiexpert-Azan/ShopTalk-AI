"""
Auth: login (owner_email + password) and JWT issuance.
Uses businesses collection for credentials; password verified via bcrypt.
"""
from datetime import timedelta
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.config import settings
from app.core.security import (
    verify_password,
    create_access_token,
    get_current_user,
)
from app.db.mongodb import get_database
from app.services.business_service import BusinessService

router = APIRouter()


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


def _business_service(db=Depends(get_database)) -> BusinessService:
    return BusinessService(db)


@router.post("/login/access-token", response_model=Token)
async def login_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: BusinessService = Depends(_business_service),
) -> Any:
    """Login with owner_email (as username) and password. Returns JWT."""
    business = await service.get_by_email(form_data.username)
    if not business or not verify_password(
        form_data.password,
        business.get("hashed_password", ""),
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )
    expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    # sub = business id for use in protected routes
    sub = str(business["_id"])
    access_token = create_access_token(subject=sub, expires_delta=expires)
    return Token(access_token=access_token, token_type="bearer")


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)) -> Any:
    """Return current user payload (e.g. sub = business id)."""
    return current_user
