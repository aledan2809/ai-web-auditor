"""
User repository for database operations
"""

from typing import Optional, List
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email: str, password_hash: str, name: Optional[str] = None) -> User:
        """Create a new user"""
        user = User(
            email=email.lower().strip(),
            password_hash=password_hash,
            name=name,
            credits=3  # Free credits for new users
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email.lower().strip())
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 100, offset: int = 0) -> List[User]:
        """Get all users with pagination"""
        result = await self.db.execute(
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Count total users"""
        result = await self.db.execute(select(func.count(User.id)))
        return result.scalar() or 0

    async def update(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user fields"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        for key, value in kwargs.items():
            if hasattr(user, key):
                setattr(user, key, value)

        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def add_credits(self, user_id: str, credits: int) -> Optional[User]:
        """Add credits to user"""
        user = await self.get_by_id(user_id)
        if not user:
            return None

        user.credits += credits
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def deduct_credit(self, user_id: str) -> bool:
        """Deduct one credit from user"""
        user = await self.get_by_id(user_id)
        if not user or user.credits <= 0:
            return False

        user.credits -= 1
        await self.db.flush()
        return True

    async def delete(self, user_id: str) -> bool:
        """Delete user"""
        user = await self.get_by_id(user_id)
        if not user:
            return False

        await self.db.delete(user)
        await self.db.flush()
        return True

    async def set_role(self, user_id: str, role: str) -> Optional[User]:
        """Set user role (user/admin)"""
        return await self.update(user_id, role=role)
