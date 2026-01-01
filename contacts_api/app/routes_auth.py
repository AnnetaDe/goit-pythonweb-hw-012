from fastapi import APIRouter, HTTPException, status, Depends, BackgroundTasks, Request, File, UploadFile
from sqlalchemy import and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.responses import JSONResponse

from contacts_api.app.cache import set_cached_user
from contacts_api.app.cloudinary_utils import upload_avatar

from contacts_api.app.database import get_db
from contacts_api.app.models import User
from contacts_api.app.schemas import UserCreate, UserResponse, Token
from pydantic import EmailStr, BaseModel
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


class SignupResponse(BaseModel):
    user: UserResponse


def ratelimit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Rate limit exceeded"}
    )


@router.post("/signup", response_model=SignupResponse, status_code=status.HTTP_201_CREATED)
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

    return {"user": new_user}


@router.post("/login", response_model=Token)
async def login_user(request: Request, db: AsyncSession = Depends(get_db)):
    content_type = (request.headers.get("content-type") or "").lower()

    if "application/json" in content_type:
        payload = await request.json()
        email = payload.get("email")
        password = payload.get("password")
    else:
        form = await request.form()
        email = form.get("email") or form.get("username")
        password = form.get("password")

    if not email or not password:
        raise HTTPException(status_code=422, detail="Email and password are required")

    stmt = select(User).where(User.email == email)
    user = await db.scalar(stmt)

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    # IMPORTANT: do NOT auto-verify here, do NOT auto-create user here
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


async def create_user(user_in, db):
    exists = (await db.execute(select(User).where(User.email == user_in.email))).scalar_one_or_none()
    if exists:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    u = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
        is_verified=False,
        role="user",
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@router.get("/me", response_model=UserResponse)
@limiter.limit("5/minute")
async def get_my_profile(request: Request, current_user: User = Depends(get_current_user)):
    if not current_user.is_verified:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Email not verified")
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
    _: User = Depends(admin_required),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.role = "admin"
    await db.commit()
    await db.refresh(user)

    return {"message": f"User {user.email} promoted to admin"}
