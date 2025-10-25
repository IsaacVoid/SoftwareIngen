from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


# Auth
class RegisterIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    name: str | None = Field(default=None, max_length=120)


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class MeOut(BaseModel):
    id: str
    email: EmailStr
    name: str | None


# Nota
class NoteIn(BaseModel):
    content: str = Field(max_length=500)


class NoteOut(BaseModel):
    content: str
    updated_at: datetime
