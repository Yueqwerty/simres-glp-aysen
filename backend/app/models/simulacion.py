"""Modelo de Simulación ejecutada."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.configuracion import Configuracion


class Simulacion(Base):
    """Simulación ejecutada con resultados."""

    __tablename__ = "simulaciones"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    configuracion_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("configuraciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Estado
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="running",
        index=True,
    )  # running, completed, failed

    # Resultados (21 KPIs)
    nivel_servicio_pct: Mapped[float | None] = mapped_column(Float)
    probabilidad_quiebre_stock_pct: Mapped[float | None] = mapped_column(Float)
    dias_con_quiebre: Mapped[int | None] = mapped_column(Integer)
    inventario_promedio_tm: Mapped[float | None] = mapped_column(Float)
    inventario_minimo_tm: Mapped[float | None] = mapped_column(Float)
    inventario_maximo_tm: Mapped[float | None] = mapped_column(Float)
    inventario_final_tm: Mapped[float | None] = mapped_column(Float)
    inventario_inicial_tm: Mapped[float | None] = mapped_column(Float)
    inventario_std_tm: Mapped[float | None] = mapped_column(Float)
    autonomia_promedio_dias: Mapped[float | None] = mapped_column(Float)
    autonomia_minima_dias: Mapped[float | None] = mapped_column(Float)
    demanda_total_tm: Mapped[float | None] = mapped_column(Float)
    demanda_satisfecha_tm: Mapped[float | None] = mapped_column(Float)
    demanda_insatisfecha_tm: Mapped[float | None] = mapped_column(Float)
    demanda_promedio_diaria_tm: Mapped[float | None] = mapped_column(Float)
    demanda_maxima_diaria_tm: Mapped[float | None] = mapped_column(Float)
    demanda_minima_diaria_tm: Mapped[float | None] = mapped_column(Float)
    total_recibido_tm: Mapped[float | None] = mapped_column(Float)
    total_despachado_tm: Mapped[float | None] = mapped_column(Float)
    disrupciones_totales: Mapped[int | None] = mapped_column(Integer)
    dias_bloqueados_total: Mapped[int | None] = mapped_column(Integer)
    pct_tiempo_bloqueado: Mapped[float | None] = mapped_column(Float)
    dias_simulados: Mapped[int | None] = mapped_column(Integer)

    # Series temporales (comprimido JSON)
    timeseries_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Metadata
    ejecutada_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    duracion_segundos: Mapped[float | None] = mapped_column(Float)
    error_mensaje: Mapped[str | None] = mapped_column(Text)

    # Relationships
    configuracion: Mapped["Configuracion"] = relationship(back_populates="simulaciones")
