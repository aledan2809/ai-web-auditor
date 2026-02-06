"""
Authentication API routes
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from database.connection import get_db
from database.models import User
from repositories.user_repo import UserRepository
from .utils import hash_password, verify_password, create_access_token, create_refresh_token, validate_password, decode_token
from .dependencies import get_current_user
from .config import auth_settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# ============== REQUEST/RESPONSE MODELS ==============

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    role: str
    credits: int
    created_at: str

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    message: str


# ============== ENDPOINTS ==============

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    data: RegisterRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Register a new user"""
    user_repo = UserRepository(db)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adresa de email este deja folosita"
        )

    # Validate password
    is_valid, error_msg = validate_password(data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg
        )

    # Create user
    password_hash = hash_password(data.password)
    user = await user_repo.create(
        email=data.email,
        password_hash=password_hash,
        name=data.name
    )

    # Auto-login after registration
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,  # Set to True in production with HTTPS
        samesite="lax",
        max_age=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        credits=user.credits,
        created_at=user.created_at.isoformat()
    )


@router.post("/login", response_model=UserResponse)
async def login(
    data: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Login with email and password"""
    user_repo = UserRepository(db)

    # Get user by email
    user = await user_repo.get_by_email(data.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email sau parola incorecta"
        )

    # Verify password
    if not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email sau parola incorecta"
        )

    # Check if active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Contul este dezactivat"
        )

    # Create tokens
    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    # Set cookies
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60
    )

    return UserResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        credits=user.credits,
        created_at=user.created_at.isoformat()
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info"""
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        role=current_user.role,
        credits=current_user.credits,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/logout", response_model=MessageResponse)
async def logout(response: Response):
    """Logout and clear cookies"""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")
    return MessageResponse(message="Deconectare reusita")


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    response: Response,
    db: AsyncSession = Depends(get_db)
):
    """Refresh access token using refresh token"""
    refresh_token_cookie = request.cookies.get("refresh_token")
    if not refresh_token_cookie:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh lipseste"
        )

    # Decode refresh token
    payload = decode_token(refresh_token_cookie)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token de refresh invalid"
        )

    # Get user
    user_id = payload.get("sub")
    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Utilizator invalid"
        )

    # Create new access token
    access_token = create_access_token(user.id, user.role)

    # Update cookie
    response.set_cookie(
        key="access_token",
        value=access_token,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

    return TokenResponse(
        access_token=access_token,
        expires_in=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )
