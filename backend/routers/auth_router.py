"""
Auth Router — /auth

Endpoints:
  POST /auth/register  — create new account
  POST /auth/login     — get JWT token
  GET  /auth/me        — return current user profile
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from auth import (
    create_access_token,
    get_current_user,
    hash_password,
    verify_password,
)
from database import get_session
from group_models import AlloraUser

router = APIRouter(prefix="/auth", tags=["Auth"])


# ── Request / Response Models ──────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=64, description="Unique username")
    email: EmailStr
    password: str = Field(..., min_length=6, description="Min 6 characters")
    display_name: str = Field(..., min_length=1, max_length=128)
    avatar_emoji: str = Field(default="🧳", max_length=8)


class LoginRequest(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: dict


class UserProfile(BaseModel):
    id: str
    username: str
    email: str
    display_name: str
    avatar_emoji: str
    created_at: str


def _user_to_dict(user: AlloraUser) -> dict:
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "display_name": user.display_name,
        "avatar_emoji": user.avatar_emoji,
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(req: RegisterRequest, session: AsyncSession = Depends(get_session)):
    """Create a new Allora account. Returns a JWT token immediately."""
    # Check username uniqueness
    existing_username = await session.execute(
        select(AlloraUser).where(AlloraUser.username == req.username)
    )
    if existing_username.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Username already taken")

    # Check email uniqueness
    existing_email = await session.execute(
        select(AlloraUser).where(AlloraUser.email == req.email)
    )
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")

    user = AlloraUser(
        id=str(uuid.uuid4()),
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        display_name=req.display_name,
        avatar_emoji=req.avatar_emoji or "🧳",
    )
    session.add(user)
    await session.flush()

    token = create_access_token({"sub": user.id})
    return AuthResponse(access_token=token, user=_user_to_dict(user))


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest, session: AsyncSession = Depends(get_session)):
    """Login with username (or email) + password. Returns JWT."""
    # Accept username or email
    stmt = select(AlloraUser).where(
        (AlloraUser.username == req.username) | (AlloraUser.email == req.username)
    )
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    if user.deleted_at is not None:
        raise HTTPException(status_code=403, detail="Account is deactivated")

    token = create_access_token({"sub": user.id})
    return AuthResponse(access_token=token, user=_user_to_dict(user))


@router.get("/me", response_model=UserProfile)
async def get_me(current_user: AlloraUser = Depends(get_current_user)):
    """Return the authenticated user's profile."""
    return UserProfile(**_user_to_dict(current_user))


@router.get("/users", tags=["Auth"])
async def list_users_for_invite(
    q: str = "",
    session: AsyncSession = Depends(get_session),
    current_user: AlloraUser = Depends(get_current_user),
):
    """
    Search users by username or display_name for group invite.
    Returns id, username, display_name, avatar_emoji only (no emails).
    """
    stmt = select(AlloraUser).where(AlloraUser.deleted_at == None)
    if q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            (AlloraUser.username.ilike(like)) | (AlloraUser.display_name.ilike(like))
        )
    stmt = stmt.limit(20)
    result = await session.execute(stmt)
    users = result.scalars().all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "display_name": u.display_name,
            "avatar_emoji": u.avatar_emoji,
        }
        for u in users
        if u.id != current_user.id  # exclude self
    ]
