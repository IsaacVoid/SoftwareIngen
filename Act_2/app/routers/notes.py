from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app import models, schemas
from app.deps import get_db, get_current_user


router = APIRouter(prefix="/notes", tags=["notes"])

@router.get("/me", response_model=schemas.NoteOut)
def get_my_note(db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if not user.note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No note yet")
    return schemas.NoteOut(content=user.note.content, updated_at=user.note.updated_at)

@router.post("/me", response_model=schemas.NoteOut)
def upsert_my_note(payload: schemas.NoteIn, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    if user.note:
        user.note.content = payload.content
    else:
        user.note = models.Note(user_id=user.id, content=payload.content)
    db.add(user)
    db.commit()
    db.refresh(user.note)
    return schemas.NoteOut(content=user.note.content, updated_at=user.note.updated_at)
