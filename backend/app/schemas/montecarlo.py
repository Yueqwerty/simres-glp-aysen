"""Schemas Pydantic para Monte Carlo.

Este módulo define los schemas de validación y serialización para
experimentos Monte Carlo usando Pydantic v2.
"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator


# Request schemas
class MonteCarloExperimentCreate(BaseModel):
    """Schema para crear un experimento Monte Carlo.

    Attributes:
        configuracion_id: ID de la configuración base
        num_replicas: Número de réplicas (100 - 100,000)
        max_workers: Trabajadores paralelos (1 - 16)
        nombre: Nombre opcional del experimento
    """

    configuracion_id: int = Field(..., gt=0, description="ID de la configuración base")
    num_replicas: int = Field(
        1000,
        ge=100,
        le=100000,
        description="Número de réplicas a ejecutar (100-100,000)",
    )
    max_workers: int = Field(
        11,
        ge=1,
        le=16,
        description="Número de trabajadores paralelos (1-16)",
    )
    nombre: str | None = Field(
        None,
        max_length=200,
        description="Nombre personalizado del experimento",
    )

    @field_validator("num_replicas")
    @classmethod
    def validate_replicas(cls, v: int) -> int:
        """Validar que el número de réplicas esté en el rango permitido."""
        if v < 100:
            raise ValueError("Mínimo 100 réplicas requeridas")
        if v > 100000:
            raise ValueError("Máximo 100,000 réplicas permitidas")
        return v

    @field_validator("max_workers")
    @classmethod
    def validate_workers(cls, v: int) -> int:
        """Validar que el número de workers esté en el rango permitido."""
        if v < 1:
            raise ValueError("Mínimo 1 worker requerido")
        if v > 16:
            raise ValueError("Máximo 16 workers permitidos")
        return v


class MonteCarloReplicaBase(BaseModel):
    """Schema base para una réplica."""

    replica_numero: int
    nivel_servicio_pct: float | None = None
    probabilidad_quiebre_stock_pct: float | None = None
    dias_con_quiebre: int | None = None
    inventario_promedio_tm: float | None = None
    inventario_minimo_tm: float | None = None
    autonomia_promedio_dias: float | None = None
    demanda_insatisfecha_tm: float | None = None
    disrupciones_totales: int | None = None
    estado: str
    duracion_segundos: float | None = None


class MonteCarloReplica(MonteCarloReplicaBase):
    """Schema completo para una réplica."""

    id: int
    experiment_id: int
    simulacion_id: int | None = None
    ejecutada_en: datetime | None = None
    error_mensaje: str | None = None

    model_config = {"from_attributes": True}


class ResultadosAgregados(BaseModel):
    """Estadísticas agregadas de un experimento Monte Carlo.

    Contiene estadísticas descriptivas (media, desviación estándar, percentiles)
    para cada KPI principal.
    """

    # Nivel de Servicio
    nivel_servicio_mean: float = Field(..., description="Media del nivel de servicio (%)")
    nivel_servicio_std: float = Field(..., description="Desv. estándar del nivel de servicio (%)")
    nivel_servicio_min: float = Field(..., description="Mínimo del nivel de servicio (%)")
    nivel_servicio_max: float = Field(..., description="Máximo del nivel de servicio (%)")
    nivel_servicio_p25: float = Field(..., description="Percentil 25 del nivel de servicio (%)")
    nivel_servicio_p50: float = Field(..., description="Mediana del nivel de servicio (%)")
    nivel_servicio_p75: float = Field(..., description="Percentil 75 del nivel de servicio (%)")
    nivel_servicio_p95: float = Field(..., description="Percentil 95 del nivel de servicio (%)")

    # Probabilidad de Quiebre
    probabilidad_quiebre_stock_mean: float = Field(..., description="Media de prob. quiebre (%)")
    probabilidad_quiebre_stock_std: float = Field(..., description="Desv. estándar de prob. quiebre (%)")
    probabilidad_quiebre_stock_p50: float = Field(..., description="Mediana de prob. quiebre (%)")
    probabilidad_quiebre_stock_p95: float = Field(..., description="Percentil 95 de prob. quiebre (%)")

    # Días con Quiebre
    dias_con_quiebre_mean: float = Field(..., description="Media de días con quiebre")
    dias_con_quiebre_std: float = Field(..., description="Desv. estándar de días con quiebre")
    dias_con_quiebre_p50: float = Field(..., description="Mediana de días con quiebre")
    dias_con_quiebre_p95: float = Field(..., description="Percentil 95 de días con quiebre")

    # Inventario
    inventario_promedio_mean: float = Field(..., description="Media de inventario promedio (TM)")
    inventario_promedio_std: float = Field(..., description="Desv. estándar de inventario promedio (TM)")
    inventario_minimo_mean: float = Field(..., description="Media de inventario mínimo (TM)")
    inventario_minimo_std: float = Field(..., description="Desv. estándar de inventario mínimo (TM)")

    # Autonomía
    autonomia_promedio_mean: float = Field(..., description="Media de autonomía promedio (días)")
    autonomia_promedio_std: float = Field(..., description="Desv. estándar de autonomía promedio (días)")
    autonomia_promedio_p50: float = Field(..., description="Mediana de autonomía promedio (días)")

    # Demanda
    demanda_insatisfecha_mean: float = Field(..., description="Media de demanda insatisfecha (TM)")
    demanda_insatisfecha_std: float = Field(..., description="Desv. estándar de demanda insatisfecha (TM)")

    # Disrupciones
    disrupciones_totales_mean: float = Field(..., description="Media de disrupciones totales")
    disrupciones_totales_std: float = Field(..., description="Desv. estándar de disrupciones totales")


class MonteCarloExperimentBase(BaseModel):
    """Schema base para experimento Monte Carlo."""

    configuracion_id: int
    nombre: str
    num_replicas: int
    max_workers: int
    estado: str
    progreso: int = Field(0, ge=0, le=100)


class MonteCarloExperiment(MonteCarloExperimentBase):
    """Schema completo para experimento Monte Carlo."""

    id: int
    iniciado_en: datetime
    completado_en: datetime | None = None
    duracion_segundos: float | None = None
    resultados_agregados: dict | None = None  # Changed from ResultadosAgregados to dict to match JSON column
    error_mensaje: str | None = None

    model_config = {"from_attributes": True}


class MonteCarloExperimentDetail(MonteCarloExperiment):
    """Schema detallado con réplicas incluidas."""

    replicas: list[MonteCarloReplica] = []

    model_config = {"from_attributes": True}


class MonteCarloProgress(BaseModel):
    """Schema para reportar progreso de un experimento."""

    experiment_id: int
    estado: str
    progreso: int = Field(..., ge=0, le=100)
    replicas_completadas: int
    replicas_totales: int
    tiempo_transcurrido_segundos: float
    tiempo_estimado_restante_segundos: float | None = None
