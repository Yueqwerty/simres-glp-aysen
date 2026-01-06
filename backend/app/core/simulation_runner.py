import asyncio
import sys
import time
from pathlib import Path
from typing import Any

_root_dir = Path(__file__).parents[3]
if str(_root_dir) not in sys.path:
    sys.path.insert(0, str(_root_dir))

from bll.config import SimulationConfig
from bll.simulation import run_simulation


async def run_simulation_async(params: dict[str, Any]) -> dict[str, Any]:
    loop = asyncio.get_event_loop()

    inv_initial = params.get("inventario_inicial_tm")
    if inv_initial is None:
        inv_initial = params["capacidad_hub_tm"] * params.get("inventario_inicial_pct", 60) / 100

    config = SimulationConfig(
        capacity_tm=params["capacidad_hub_tm"],
        reorder_point_tm=params["punto_reorden_tm"],
        order_quantity_tm=params["cantidad_pedido_tm"],
        initial_inventory_tm=inv_initial,
        base_daily_demand_tm=params["demanda_base_diaria_tm"],
        demand_variability=params["variabilidad_demanda"],
        seasonal_amplitude=params["amplitud_estacional"],
        peak_winter_day=params["dia_pico_invernal"],
        nominal_lead_time_days=params["lead_time_nominal_dias"],
        annual_disruption_rate=params["tasa_disrupciones_anual"],
        disruption_min_days=params["duracion_disrupcion_min_dias"],
        disruption_mode_days=params["duracion_disrupcion_mode_dias"],
        disruption_max_days=params["duracion_disrupcion_max_dias"],
        simulation_days=params["duracion_simulacion_dias"],
        seed=params.get("semilla_aleatoria") or 42,
        use_seasonality=params["usar_estacionalidad"],
    )

    start = time.time()
    result = await loop.run_in_executor(None, run_simulation, config)
    duration = time.time() - start

    kpis = {
        "nivel_servicio_pct": result["service_level_pct"],
        "probabilidad_quiebre_stock_pct": result["stockout_probability_pct"],
        "dias_con_quiebre": result["stockout_days"],
        "inventario_promedio_tm": result["avg_inventory_tm"],
        "inventario_minimo_tm": result["min_inventory_tm"],
        "inventario_maximo_tm": result["max_inventory_tm"],
        "inventario_final_tm": result["final_inventory_tm"],
        "inventario_inicial_tm": result["initial_inventory_tm"],
        "inventario_std_tm": result["std_inventory_tm"],
        "autonomia_promedio_dias": result["avg_autonomy_days"],
        "autonomia_minima_dias": result["min_autonomy_days"],
        "demanda_total_tm": result["total_demand_tm"],
        "demanda_satisfecha_tm": result["satisfied_demand_tm"],
        "demanda_insatisfecha_tm": result["unsatisfied_demand_tm"],
        "demanda_promedio_diaria_tm": result["avg_daily_demand_tm"],
        "demanda_maxima_diaria_tm": result["max_daily_demand_tm"],
        "demanda_minima_diaria_tm": result["min_daily_demand_tm"],
        "total_recibido_tm": result["total_received_tm"],
        "total_despachado_tm": result["total_dispatched_tm"],
        "disrupciones_totales": result["total_disruptions"],
        "dias_bloqueados_total": result["total_blocked_days"],
        "pct_tiempo_bloqueado": result["blocked_time_pct"],
        "dias_simulados": result["simulated_days"],
        "series_temporales": result.get("time_series", []),
        "_duracion_segundos": duration,
    }

    return kpis
