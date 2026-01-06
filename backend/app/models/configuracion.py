"""Modelo de Configuración de Simulación."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.simulacion import Simulacion
    from app.models.montecarlo import MonteCarloExperiment


class Configuracion(Base):
    """Configuración de parámetros de simulación."""

    __tablename__ = "configuraciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descripcion: Mapped[str | None] = mapped_column(String, nullable=True)

    # Parámetros como JSON
    parametros: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Metadata
    creada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    actualizada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    simulaciones: Mapped[list["Simulacion"]] = relationship(
        back_populates="configuracion",
        cascade="all, delete-orphan",
    )
    monte_carlo_experiments: Mapped[list["MonteCarloExperiment"]] = relationship(
        back_populates="configuracion",
        cascade="all, delete-orphan",
    )
