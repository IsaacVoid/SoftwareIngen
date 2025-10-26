from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from app import models, schemas
from app.deps import get_db
from app.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_refresh
from app.config import settings


router = APIRouter(prefix="/auth", tags=["auth"])

COOKIE_FLAGS = {
"httponly": True,
"secure": settings.COOKIE_SECURE,
"samesite": settings.COOKIE_SAMESITE,
"domain": settings.COOKIE_DOMAIN or None,
}


@router.post("/register", status_code=201)
def register(payload: schemas.RegisterIn, db: Session = Depends(get_db)):
    exists = db.scalar(select(models.User).where(models.User.email == payload.email))
    if exists:
        raise HTTPException(status_code=409, detail="Email already registered")


    user = models.User(email=payload.email, password_hash=hash_password(payload.password), name=payload.name)
    db.add(user)
    db.commit()
    return {"message": "registered"}




@router.post("/login")
def login(payload: schemas.LoginIn, request: Request, response: Response, db: Session = Depends(get_db)):
    user = db.scalar(select(models.User).where(models.User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user.last_login_at = datetime.now(timezone.utc)

    access = create_access_token(user.id)
    refresh = create_refresh_token(user.id)

    # Persistimos refresh token con expiración y metadatos
    exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)
    rt = models.RefreshToken(user_id=user.id, expires_at=exp, user_agent=request.headers.get("user-agent"), ip=request.client.host)
    db.add(rt)
    db.commit()

    response.set_cookie("access_token", access, max_age=settings.ACCESS_TOKEN_EXPIRES_MIN * 60, **COOKIE_FLAGS)
    response.set_cookie("refresh_token", refresh, max_age=settings.REFRESH_TOKEN_EXPIRES_DAYS * 86400, **COOKIE_FLAGS)
    return {"message": f"hello {user.name or user.email}"}




@router.post("/refresh")
def refresh(request: Request, response: Response, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    if not token:
        raise HTTPException(status_code=401, detail="No refresh token")
    try:
        payload = decode_refresh(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    user_id: str = payload.get("sub")

    user = db.get(models.User, user_id)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    access = create_access_token(user.id)
    new_refresh = create_refresh_token(user.id)

    exp = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRES_DAYS)
    rt = models.RefreshToken(user_id=user.id, expires_at=exp, user_agent=request.headers.get("user-agent"), ip=request.client.host)
    db.add(rt)
    db.commit()

    response.set_cookie("access_token", access, max_age=settings.ACCESS_TOKEN_EXPIRES_MIN * 60, **COOKIE_FLAGS)
    response.set_cookie("refresh_token", new_refresh, max_age=settings.REFRESH_TOKEN_EXPIRES_DAYS * 86400, **COOKIE_FLAGS)
    return {"message": "logged out"}

@router.post("/logout")
def logout(response: Response, db: Session = Depends(get_db)):
    response.delete_cookie("access_token", domain=settings.COOKIE_DOMAIN or None)
    response.delete_cookie("refresh_token", domain=settings.COOKIE_DOMAIN or None)
    return {"message": "logged out"}
