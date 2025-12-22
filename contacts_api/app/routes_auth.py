from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request, File, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import JSONResponse
from contacts_api.app.cloudinary_utils import upload_avatar

from contacts_api.app.database import get_db
from contacts_api.app.models import User
from contacts_api.app.schemas import UserCreate, UserResponse, Token
from pydantic import EmailStr
from fastapi import Body
from contacts_api.app.auth import hash_password, verify_password
from contacts_api.app.jwt_utils import (
    create_access_token,
    create_email_token,
    decode_email_token
)
from contacts_api.app.email_utils import send_verification_email, send_password_reset_email
from contacts_api.app.dependencies import get_current_user, admin_required

from slowapi.errors import RateLimitExceeded
from contacts_api.app.limiter_config import limiter

router = APIRouter(tags=["Authentication"])


def ratelimit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = result.scalar_one_or_none()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    new_user = User(
        email=user_data.email,
        hashed_password=hash_password(user_data.password)
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)

    token = create_email_token(new_user.email)
    background_tasks.add_task(send_verification_email, new_user.email, token)

    return new_user


@router.post("/login", response_model=Token)
async def login_user(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == user_data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    access_token = create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/verify-email/{token}")
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    email = decode_email_token(token)
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    await db.commit()
    return {"message": "Email verified successfully!"}


@router.get("/me", response_model=UserResponse)
@limiter.limit("5/minute")
async def get_my_profile(
    request: Request,
    current_user: User = Depends(get_current_user)
):
    if not current_user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user



@router.post("/avatar", response_model=UserResponse)
async def update_avatar(
    request: Request,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(admin_required) 
):
    if not current_user.is_verified:
        raise HTTPException(status_code=403, detail="Email not verified")

    content = await file.read()
    url = upload_avatar(content, public_id=str(current_user.id))

    current_user.avatar_url = url
    await db.commit()
    await db.refresh(current_user)

    return current_user

@router.post("/request-password-reset")
async def request_password_reset(
    background_tasks: BackgroundTasks,
    email: EmailStr,
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if user:
        token = create_email_token(user.email)
        background_tasks.add_task(send_password_reset_email, user.email, token)

    # Повертаємо завжди успішно — щоб не дати знати, чи email зареєстрований
    return {"message": "If the email is registered, reset instructions will be sent."}

@router.post("/reset-password/{token}")
async def reset_password(
    token: str,
    new_password: str = Body(..., min_length=6),
    db: AsyncSession = Depends(get_db)
):
    try:
        email = decode_email_token(token)
    except:
        raise HTTPException(status_code=400, detail="Invalid or expired token")

    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.hashed_password = hash_password(new_password)
    await db.commit()

    return {"message": "Password reset successfully."}

@router.post("/make-admin/{user_id}")
async def make_user_admin(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(admin_required),  # 🔐 лише admin
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = "admin"
    await db.commit()
    await db.refresh(user)

    return {"message": f"User {user.email} promoted to admin"}
