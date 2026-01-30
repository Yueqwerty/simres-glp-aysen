"""Schemas para Simulación."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SimulacionRequest(BaseModel):
    """Request para ejecutar simulación."""

    configuracion_id: int


class SimulacionResponse(BaseModel):
    """Response de simulación."""

    id: int
    configuracion_id: int
    configuracion_nombre: str | None = None
    estado: str
    ejecutada_en: datetime
    duracion_segundos: float | None
    error_mensaje: str | None

    # KPIs principales
    nivel_servicio_pct: float | None = None
    probabilidad_quiebre_stock_pct: float | None = None
    dias_con_quiebre: float | None = None  # Changed to float to handle fractional values
    inventario_promedio_tm: float | None = None
    inventario_minimo_tm: float | None = None
    inventario_maximo_tm: float | None = None
    inventario_final_tm: float | None = None
    inventario_inicial_tm: float | None = None
    inventario_std_tm: float | None = None
    autonomia_promedio_dias: float | None = None
    autonomia_minima_dias: float | None = None
    demanda_total_tm: float | None = None
    demanda_satisfecha_tm: float | None = None
    demanda_insatisfecha_tm: float | None = None
    demanda_promedio_diaria_tm: float | None = None
    demanda_maxima_diaria_tm: float | None = None
    demanda_minima_diaria_tm: float | None = None
    total_recibido_tm: float | None = None
    total_despachado_tm: float | None = None
    disrupciones_totales: float | None = None  # Changed to float to handle fractional values
    dias_bloqueados_total: float | None = None  # Changed to float to handle fractional values
    pct_tiempo_bloqueado: float | None = None
    dias_simulados: float | None = None  # Changed to float to handle fractional values

    # Series temporales
    timeseries_data: dict | None = None

    model_config = ConfigDict(from_attributes=True)
