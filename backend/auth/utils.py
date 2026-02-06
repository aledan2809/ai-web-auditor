"""
Authentication utilities
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
from jose import jwt, JWTError

from .config import auth_settings


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    try:
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception:
        return False


def create_access_token(user_id: str, role: str = "user") -> str:
    """Create a JWT access token"""
    expire = datetime.utcnow() + timedelta(minutes=auth_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "role": role,
        "exp": expire,
        "type": "access"
    }
    return jwt.encode(payload, auth_settings.JWT_SECRET, algorithm=auth_settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token"""
    expire = datetime.utcnow() + timedelta(days=auth_settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "exp": expire,
        "type": "refresh"
    }
    return jwt.encode(payload, auth_settings.JWT_SECRET, algorithm=auth_settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(
            token,
            auth_settings.JWT_SECRET,
            algorithms=[auth_settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError:
        return None


def validate_password(password: str) -> tuple[bool, str]:
    """Validate password strength"""
    if len(password) < 8:
        return False, "Parola trebuie sa aiba minim 8 caractere"
    if not any(c.isupper() for c in password):
        return False, "Parola trebuie sa contina cel putin o litera mare"
    if not any(c.islower() for c in password):
        return False, "Parola trebuie sa contina cel putin o litera mica"
    if not any(c.isdigit() for c in password):
        return False, "Parola trebuie sa contina cel putin o cifra"
    return True, ""
