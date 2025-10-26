from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
from app.middleware.security_headers import SecurityHeadersMiddleware
from app.routers import auth, notes
from app.deps import get_current_user


app = FastAPI(title="Auth+Notes API", version="0.1.0")


# DB init (solo para MVP)
init_db()

# CORS
origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")] if settings.CORS_ORIGINS else []
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins and origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    )

# Security headers
app.add_middleware(SecurityHeadersMiddleware)


# Routers
app.include_router(auth.router)
app.include_router(notes.router)




@app.get("/me")
def me(user=Depends(get_current_user)):
    return {"message": f"Hola, {user.name or user.email}!"}
