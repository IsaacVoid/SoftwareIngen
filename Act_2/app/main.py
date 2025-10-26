from fastapi import FastAPI, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import init_db
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
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "no-referrer")
    if request.url.path.startswith(("/docs", "/redoc", "/openapi.json")):
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
        )
    else:
        response.headers.setdefault("Content-Security-Policy", "default-src 'self'")
    return response


# Routers
app.include_router(auth.router)
app.include_router(notes.router)




@app.get("/", response_class=HTMLResponse)
def root():
    return """
    <html>
      <head><title>Auth+Notes</title></head>
      <body style="font-family: system-ui; max-width: 640px; margin: 40px auto;">
        <h1>Auth+Notes API</h1>
        <p>Ve a <a href="/docs">/docs</a> para probar el registro, login y notas.</p>
      </body>
    </html>
    """


"""
def me(user=Depends(get_current_user)):
    return {"message": f"Hola, {user.name or user.email}!"}
"""
