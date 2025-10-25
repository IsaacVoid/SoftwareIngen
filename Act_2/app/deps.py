from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app import models
from app.security import decode_access




def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()




def get_current_user(request: Request, db: Session = Depends(get_db)) -> models.User:
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
        try:
            payload = decode_access(token)
            user_id: str = payload.get("sub")
        except Exception:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
