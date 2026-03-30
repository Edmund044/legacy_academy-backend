"""Auth endpoints: login, refresh, logout, forgot-password, reset-password."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.deps import get_db, get_current_active_user
from app.core.responses import ok
from app.core.security import (
    verify_password, create_access_token, create_refresh_token,
    decode_token, create_reset_token, verify_reset_token, get_password_hash,
)
from app.models.user import User
from app.schemas.schemas import LoginIn, RefreshIn, ForgotIn, ResetIn

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _role_str(user: User) -> str:
    """Return the role as a plain string regardless of whether it's an enum or str."""
    return user.role.value if hasattr(user.role, "value") else user.role


@router.post("/login", summary="Authenticate and obtain JWT tokens")
async def login(body: LoginIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(401, {"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"})

    if not verify_password(body.password, user.password_hash):
        raise HTTPException(401, {"code": "INVALID_CREDENTIALS verify", "message": "Invalid email or password"})

    if not user.is_active:
        raise HTTPException(403, {"code": "ACCOUNT_INACTIVE", "message": "Account deactivated"})

    await db.execute(
        update(User).where(User.id == user.id).values(last_login_at=datetime.now(timezone.utc))
    )
    await db.commit()

    role = _role_str(user)

    return ok({
        "access_token":  create_access_token(user.id, role=role),
        "refresh_token": create_refresh_token(user.id, role=role),
        "expires_in": 86400,
        "token_type": "Bearer",
        "user": {
            "id":         str(user.id),
            "email":      user.email,
            "role":       role,
            "first_name": user.first_name,
            "last_name":  user.last_name,
        },
    })


@router.post("/refresh", summary="Refresh access token")
async def refresh(body: RefreshIn, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token)
        if payload.get("type") != "refresh":
            raise ValueError
        uid = payload["sub"]
    except Exception:
        raise HTTPException(401, {"code": "TOKEN_EXPIRED", "message": "Refresh token invalid or expired"})

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user or not user.is_active:
        raise HTTPException(401, {"code": "TOKEN_INVALID", "message": "User not found"})

    role = _role_str(user)
    return ok({"access_token": create_access_token(user.id, role=role),"refresh_token": create_refresh_token(user.id, role=role), "expires_in": 86400})


@router.post("/logout", summary="End session")
async def logout(_user=Depends(get_current_active_user)):
    """Clears session. Add refresh_token to Redis blocklist in production."""
    return ok({"message": "Logged out successfully"})


@router.post("/forgot-password", summary="Request password reset email")
async def forgot_password(body: ForgotIn, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email))
    user = result.scalar_one_or_none()
    if user:
        _token = create_reset_token(body.email)
        # TODO: await email_service.send_reset(user.email, _token)
    return ok({"message": "If that email is registered, a reset link has been sent"})


@router.post("/reset-password", summary="Set new password with reset token")
async def reset_password(body: ResetIn, db: AsyncSession = Depends(get_db)):
    email = verify_reset_token(body.token)
    if not email:
        raise HTTPException(400, {"code": "TOKEN_INVALID", "message": "Reset token invalid or expired"})
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(404, {"code": "NOT_FOUND", "message": "User not found"})
    await db.execute(
        update(User).where(User.id == user.id).values(password_hash=get_password_hash(body.password))
    )
    return ok({"message": "Password updated successfully"})