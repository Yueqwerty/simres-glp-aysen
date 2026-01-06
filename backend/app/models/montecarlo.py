"""Modelos de base de datos para experimentos Monte Carlo.

Este módulo define los modelos SQLAlchemy para almacenar experimentos
Monte Carlo y sus resultados agregados estadísticos.
"""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.configuracion import Configuracion
    from app.models.simulacion import Simulacion


class MonteCarloExperiment(Base):
    """Experimento Monte Carlo con múltiples réplicas.

    Attributes:
        id: Identificador único del experimento
        configuracion_id: ID de la configuración base utilizada
        nombre: Nombre descriptivo del experimento
        num_replicas: Número total de réplicas a ejecutar
        max_workers: Número máximo de trabajadores paralelos
        estado: Estado actual (pending, running, completed, failed)
        progreso: Porcentaje de progreso (0-100)
        iniciado_en: Timestamp de inicio de ejecución
        completado_en: Timestamp de finalización
        duracion_segundos: Duración total de ejecución en segundos
        resultados_agregados: Estadísticas agregadas de todas las réplicas
        error_mensaje: Mensaje de error si falló
    """

    __tablename__ = "monte_carlo_experiments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    configuracion_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("configuraciones.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    num_replicas: Mapped[int] = mapped_column(Integer, nullable=False)
    max_workers: Mapped[int] = mapped_column(Integer, nullable=False)

    # Estado y progreso
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )  # pending, running, completed, failed
    progreso: Mapped[int] = mapped_column(Integer, default=0)  # 0-100

    # Timestamps
    iniciado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completado_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duracion_segundos: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Resultados agregados (JSON con estadísticas)
    # Incluye: mean, std, min, max, p25, p50, p75, p95 para cada KPI
    resultados_agregados: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Error handling
    error_mensaje: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    configuracion: Mapped["Configuracion"] = relationship(
        back_populates="monte_carlo_experiments"
    )
    replicas: Mapped[list["MonteCarloReplica"]] = relationship(
        back_populates="experiment",
        cascade="all, delete-orphan",
    )


class MonteCarloReplica(Base):
    """Réplica individual de un experimento Monte Carlo.

    Cada réplica representa una ejecución única de la simulación con
    una semilla aleatoria diferente.

    Attributes:
        id: Identificador único de la réplica
        experiment_id: ID del experimento al que pertenece
        replica_numero: Número secuencial de la réplica (1 a N)
        simulacion_id: ID de la simulación ejecutada
        estado: Estado de ejecución de esta réplica
        ejecutada_en: Timestamp de ejecución
        duracion_segundos: Duración de ejecución en segundos
        error_mensaje: Mensaje de error si falló
    """

    __tablename__ = "monte_carlo_replicas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    experiment_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("monte_carlo_experiments.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    replica_numero: Mapped[int] = mapped_column(Integer, nullable=False)
    simulacion_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("simulaciones.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # KPIs principales de esta réplica (desnormalizados para queries rápidas)
    nivel_servicio_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    probabilidad_quiebre_stock_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    dias_con_quiebre: Mapped[int | None] = mapped_column(Integer, nullable=True)
    inventario_promedio_tm: Mapped[float | None] = mapped_column(Float, nullable=True)
    inventario_minimo_tm: Mapped[float | None] = mapped_column(Float, nullable=True)
    autonomia_promedio_dias: Mapped[float | None] = mapped_column(Float, nullable=True)
    demanda_insatisfecha_tm: Mapped[float | None] = mapped_column(Float, nullable=True)
    disrupciones_totales: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Metadata
    estado: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )  # pending, running, completed, failed
    ejecutada_en: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    duracion_segundos: Mapped[float | None] = mapped_column(Float, nullable=True)
    error_mensaje: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Relationships
    experiment: Mapped["MonteCarloExperiment"] = relationship(
        back_populates="replicas"
    )
    simulacion: Mapped["Simulacion | None"] = relationship()
