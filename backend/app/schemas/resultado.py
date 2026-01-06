"""Schema para Resultados (21 KPIs)."""

from pydantic import BaseModel, ConfigDict


class ResultadoResponse(BaseModel):
    """Response con los 21 KPIs de simulación."""

    simulacion_id: int

    # Nivel de Servicio
    nivel_servicio_pct: float
    probabilidad_quiebre_stock_pct: float
    dias_con_quiebre: float  # Changed to float to handle fractional values

    # Inventario
    inventario_promedio_tm: float
    inventario_minimo_tm: float
    inventario_maximo_tm: float
    inventario_final_tm: float
    inventario_inicial_tm: float
    inventario_std_tm: float

    # Autonomía
    autonomia_promedio_dias: float
    autonomia_minima_dias: float

    # Demanda
    demanda_total_tm: float
    demanda_satisfecha_tm: float
    demanda_insatisfecha_tm: float
    demanda_promedio_diaria_tm: float
    demanda_maxima_diaria_tm: float
    demanda_minima_diaria_tm: float

    # Flujo
    total_recibido_tm: float
    total_despachado_tm: float

    # Disrupciones
    disrupciones_totales: float  # Changed to float to handle fractional values
    dias_bloqueados_total: float  # Changed to float to handle fractional values
    pct_tiempo_bloqueado: float

    # Control
    dias_simulados: float  # Changed to float to handle fractional values

    model_config = ConfigDict(from_attributes=True)
