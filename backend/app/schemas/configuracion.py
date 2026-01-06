"""Schemas para Configuración."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, ValidationInfo


class ParametrosBase(BaseModel):
    """Parámetros de configuración de simulación."""

    # Capacidad
    capacidad_hub_tm: float = Field(431.0, gt=0, le=2000)
    punto_reorden_tm: float = Field(394.0, gt=0, le=2000)
    cantidad_pedido_tm: float = Field(230.0, gt=0, le=1000)
    inventario_inicial_pct: float = Field(60.0, ge=0, le=100)

    # Demanda
    demanda_base_diaria_tm: float = Field(52.5, gt=0)
    variabilidad_demanda: float = Field(0.15, ge=0, le=1)
    amplitud_estacional: float = Field(0.30, ge=0, le=1)
    dia_pico_invernal: int = Field(200, ge=1, le=365)
    usar_estacionalidad: bool = True

    # Disrupciones
    tasa_disrupciones_anual: float = Field(4.0, ge=0, le=50)
    duracion_disrupcion_min_dias: float = Field(3.0, gt=0)
    duracion_disrupcion_mode_dias: float = Field(7.0, gt=0)
    duracion_disrupcion_max_dias: float = Field(21.0, gt=0)

    # Operación
    lead_time_nominal_dias: float = Field(6.0, gt=0)
    duracion_simulacion_dias: int = Field(365, ge=1, le=3650)
    semilla_aleatoria: int | None = None

    @field_validator("punto_reorden_tm")
    @classmethod
    def validar_punto_reorden(cls, v: float, info: ValidationInfo) -> float:
        """El punto de reorden no puede exceder la capacidad."""
        capacidad = info.data.get("capacidad_hub_tm")
        if capacidad and v > capacidad:
            raise ValueError("punto_reorden_tm no puede exceder capacidad_hub_tm")
        return v

    @field_validator("duracion_disrupcion_mode_dias")
    @classmethod
    def validar_duracion_mode(cls, v: float, info: ValidationInfo) -> float:
        """La moda debe estar entre min y max."""
        min_dias = info.data.get("duracion_disrupcion_min_dias", 0)
        if v < min_dias:
            raise ValueError("duracion_disrupcion_mode_dias debe ser >= min_dias")
        return v

    @field_validator("duracion_disrupcion_max_dias")
    @classmethod
    def validar_duracion_max(cls, v: float, info: ValidationInfo) -> float:
        """El máximo debe ser >= moda."""
        mode_dias = info.data.get("duracion_disrupcion_mode_dias", 0)
        if v < mode_dias:
            raise ValueError("duracion_disrupcion_max_dias debe ser >= mode_dias")
        return v


class ConfiguracionCreate(ParametrosBase):
    """Schema para crear configuración."""

    nombre: str = Field(..., min_length=1, max_length=100)
    descripcion: str | None = None


class ConfiguracionUpdate(BaseModel):
    """Schema para actualizar configuración."""

    nombre: str | None = Field(None, min_length=1, max_length=100)
    descripcion: str | None = None
    parametros: ParametrosBase | None = None


class ConfiguracionRead(BaseModel):
    """Schema para leer configuración."""

    id: int
    nombre: str
    descripcion: str | None
    parametros: dict
    creada_en: datetime
    actualizada_en: datetime

    model_config = ConfigDict(from_attributes=True)
