from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings


class Base(DeclarativeBase):
    pass


engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# En MVP: creamos tablas al arrancar.
# En producción: usa Alembic para migraciones.


def init_db():
    from app import models # noqa: F401
    Base.metadata.create_all(bind=engine)
