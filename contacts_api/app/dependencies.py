from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from contacts_api.app.cache import set_cached_user, get_cached_user
from contacts_api.app.database import get_db
from contacts_api.app.jwt_utils import decode_access_token
from contacts_api.app.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    try:
        payload = decode_access_token(token)
        user_id = int(payload.get("sub"))
    except (JWTError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    cached = await get_cached_user(user_id)
    if cached:
        u = User(
            id=cached["id"],
            email=cached["email"],
            hashed_password=cached.get("hashed_password", ""),  # optional
            is_verified=cached["is_verified"],
            avatar_url=cached.get("avatar_url"),
            role=cached.get("role", "user"),
        )
        return u


    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    await set_cached_user(
        user.id,
        {
            "id": user.id,
            "email": user.email,
            "is_verified": user.is_verified,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "avatar_url": user.avatar_url,
            "role": user.role,
        },
        ttl=300,
    )
    return user

async def admin_required(current_user: User = Depends(get_current_user)) -> User:
    """
    Дозволити доступ тільки адміністраторам.
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action"
        )
    return current_user