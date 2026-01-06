"""Modelos de base de datos para experimentos Monte Carlo.

Este módulo define los modelos SQLAlchemy para almacenar experimentos
Monte Carlo y sus resultados agregados.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.db.base import Base


class MonteCarloExperiment(Base):
    """Modelo para experimento Monte Carlo."""

    __tablename__ = "monte_carlo_experiments"

    id = Column(Integer, primary_key=True, index=True)
    configuracion_id = Column(Integer, ForeignKey("configuraciones.id", ondelete="CASCADE"), nullable=False, index=True)
    nombre = Column(String(200), nullable=False)
    num_replicas = Column(Integer, nullable=False)
    max_workers = Column(Integer, nullable=False)
    estado = Column(String(20), nullable=False, default="pending", index=True)  # pending, running, completed, failed
    progreso = Column(Integer, default=0)  # 0-100

    # Timestamps
    iniciado_en = Column(DateTime, default=datetime.utcnow)
    completado_en = Column(DateTime, nullable=True)
    duracion_segundos = Column(Float, nullable=True)

    # Resultados agregados (JSON con stats)
    resultados_agregados = Column(JSON, nullable=True)

    # Error handling
    error_mensaje = Column(String, nullable=True)

    # Relationships
    configuracion = relationship("Configuracion", back_populates="monte_carlo_experiments")
    replicas = relationship("MonteCarloReplica", back_populates="experiment", cascade="all, delete-orphan")


class MonteCarloReplica(Base):
    """Modelo para una réplica individual de un experimento Monte Carlo."""

    __tablename__ = "monte_carlo_replicas"

    id = Column(Integer, primary_key=True, index=True)
    experiment_id = Column(Integer, ForeignKey("monte_carlo_experiments.id", ondelete="CASCADE"), nullable=False, index=True)
    replica_numero = Column(Integer, nullable=False)
    simulacion_id = Column(Integer, ForeignKey("simulaciones.id", ondelete="CASCADE"), nullable=True)

    # KPIs de esta réplica
    nivel_servicio_pct = Column(Float, nullable=True)
    probabilidad_quiebre_stock_pct = Column(Float, nullable=True)
    dias_con_quiebre = Column(Integer, nullable=True)
    inventario_promedio_tm = Column(Float, nullable=True)
    inventario_minimo_tm = Column(Float, nullable=True)
    autonomia_promedio_dias = Column(Float, nullable=True)
    demanda_insatisfecha_tm = Column(Float, nullable=True)

    estado = Column(String(20), nullable=False, default="pending")
    ejecutada_en = Column(DateTime, nullable=True)
    duracion_segundos = Column(Float, nullable=True)
    error_mensaje = Column(String, nullable=True)

    # Relationships
    experiment = relationship("MonteCarloExperiment", back_populates="replicas")
    simulacion = relationship("Simulacion")
