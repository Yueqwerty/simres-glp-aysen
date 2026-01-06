"""Database initialization."""

from app.db.base import Base
from app.db.session import engine
from app.models import configuracion, simulacion, montecarlo  # noqa


def init_db() -> None:
    """Crear todas las tablas en la base de datos."""
    Base.metadata.create_all(bind=engine)
