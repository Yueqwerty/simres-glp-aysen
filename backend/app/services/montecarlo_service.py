import sys
import time
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from datetime import datetime
from typing import Any

import numpy as np
from sqlalchemy.orm import Session

_root = Path(__file__).parents[3]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from bll.config import SimulationConfig
from bll.simulation import run_simulation

from app.models.configuracion import Configuracion
from app.models.montecarlo import MonteCarloExperiment, MonteCarloReplica
from app.models.simulacion import Simulacion


def _run_replica(config_params: dict, replica_num: int) -> dict[str, Any]:
    start = time.time()
    try:
        cap = config_params.get("capacidad_hub_tm", 431.0)
        inv_pct = config_params.get("inventario_inicial_pct", 60.0)
        seed_base = config_params.get("semilla_aleatoria") or 42

        config = SimulationConfig(
            capacity_tm=cap,
            reorder_point_tm=config_params.get("punto_reorden_tm", cap * 0.7),
            order_quantity_tm=config_params.get("cantidad_pedido_tm", cap * 0.5),
            initial_inventory_tm=cap * inv_pct / 100.0,
            base_daily_demand_tm=config_params.get("demanda_base_diaria_tm", 52.5),
            nominal_lead_time_days=config_params.get("lead_time_nominal_dias", 6.0),
            disruption_min_days=config_params.get("duracion_disrupcion_min_dias", 3.0),
            disruption_mode_days=config_params.get("duracion_disrupcion_mode_dias", 7.0),
            disruption_max_days=config_params.get("duracion_disrupcion_max_dias", 21.0),
            annual_disruption_rate=config_params.get("tasa_disrupciones_anual", 4.0),
            use_seasonality=config_params.get("usar_estacionalidad", True),
            simulation_days=config_params.get("duracion_simulacion_dias", 365),
            seed=seed_base * 100000 + replica_num,
        )

        result = run_simulation(config)
        del result["time_series"]

        return {
            "replica_numero": replica_num,
            "estado": "completed",
            "kpis": {
                "nivel_servicio_pct": result["service_level_pct"],
                "probabilidad_quiebre_stock_pct": result["stockout_probability_pct"],
                "dias_con_quiebre": result["stockout_days"],
                "inventario_promedio_tm": result["avg_inventory_tm"],
                "inventario_minimo_tm": result["min_inventory_tm"],
                "autonomia_promedio_dias": result["avg_autonomy_days"],
                "demanda_insatisfecha_tm": result["unsatisfied_demand_tm"],
                "disrupciones_totales": result["total_disruptions"],
            },
            "duracion_segundos": time.time() - start,
            "error_mensaje": None,
        }
    except Exception as e:
        return {
            "replica_numero": replica_num,
            "estado": "failed",
            "kpis": None,
            "duracion_segundos": time.time() - start,
            "error_mensaje": str(e),
        }


def calcular_estadisticas_agregadas(replicas: list[MonteCarloReplica]) -> dict[str, float]:
    completed = [r for r in replicas if r.estado == "completed"]
    if not completed:
        return {}

    def arr(attr):
        return np.array([getattr(r, attr) for r in completed if getattr(r, attr) is not None])

    ns = arr("nivel_servicio_pct")
    pq = arr("probabilidad_quiebre_stock_pct")
    dq = arr("dias_con_quiebre")
    ip = arr("inventario_promedio_tm")
    im = arr("inventario_minimo_tm")
    au = arr("autonomia_promedio_dias")
    di = arr("demanda_insatisfecha_tm")
    dr = arr("disrupciones_totales")

    return {
        "nivel_servicio_mean": float(np.mean(ns)),
        "nivel_servicio_std": float(np.std(ns)),
        "nivel_servicio_min": float(np.min(ns)),
        "nivel_servicio_max": float(np.max(ns)),
        "nivel_servicio_p25": float(np.percentile(ns, 25)),
        "nivel_servicio_p50": float(np.percentile(ns, 50)),
        "nivel_servicio_p75": float(np.percentile(ns, 75)),
        "nivel_servicio_p95": float(np.percentile(ns, 95)),
        "probabilidad_quiebre_stock_mean": float(np.mean(pq)),
        "probabilidad_quiebre_stock_std": float(np.std(pq)),
        "probabilidad_quiebre_stock_p50": float(np.percentile(pq, 50)),
        "probabilidad_quiebre_stock_p95": float(np.percentile(pq, 95)),
        "dias_con_quiebre_mean": float(np.mean(dq)),
        "dias_con_quiebre_std": float(np.std(dq)),
        "dias_con_quiebre_p50": float(np.percentile(dq, 50)),
        "dias_con_quiebre_p95": float(np.percentile(dq, 95)),
        "inventario_promedio_mean": float(np.mean(ip)),
        "inventario_promedio_std": float(np.std(ip)),
        "inventario_minimo_mean": float(np.mean(im)),
        "inventario_minimo_std": float(np.std(im)),
        "autonomia_promedio_mean": float(np.mean(au)),
        "autonomia_promedio_std": float(np.std(au)),
        "autonomia_promedio_p50": float(np.percentile(au, 50)),
        "demanda_insatisfecha_mean": float(np.mean(di)),
        "demanda_insatisfecha_std": float(np.std(di)),
        "disrupciones_totales_mean": float(np.mean(dr)),
        "disrupciones_totales_std": float(np.std(dr)),
    }


def ejecutar_experimento_montecarlo(experiment_id: int) -> MonteCarloExperiment:
    from app.db.session import SessionLocal
    db = SessionLocal()

    try:
        exp = db.query(MonteCarloExperiment).filter(MonteCarloExperiment.id == experiment_id).first()
        if not exp:
            raise ValueError(f"Experiment {experiment_id} not found")
        if exp.estado != "pending":
            raise ValueError(f"Experiment {experiment_id} not pending")

        config = db.query(Configuracion).filter(Configuracion.id == exp.configuracion_id).first()
        if not config:
            raise ValueError(f"Config {exp.configuracion_id} not found")

        exp.estado = "running"
        exp.progreso = 0
        exp.iniciado_en = datetime.utcnow()
        db.commit()

        start_total = time.time()
        params = config.parametros
        results = []

        with ProcessPoolExecutor(max_workers=exp.max_workers) as executor:
            futures = {executor.submit(_run_replica, params, i): i for i in range(1, exp.num_replicas + 1)}
            done = 0
            for future in as_completed(futures):
                results.append(future.result())
                done += 1
                exp.progreso = int(done / exp.num_replicas * 100)
                db.commit()

        for res in results:
            replica = MonteCarloReplica(
                experiment_id=exp.id,
                replica_numero=res["replica_numero"],
                estado=res["estado"],
                ejecutada_en=datetime.utcnow(),
                duracion_segundos=res["duracion_segundos"],
                error_mensaje=res.get("error_mensaje"),
            )
            if res["estado"] == "completed" and res["kpis"]:
                kpis = res["kpis"]
                replica.nivel_servicio_pct = kpis["nivel_servicio_pct"]
                replica.probabilidad_quiebre_stock_pct = kpis["probabilidad_quiebre_stock_pct"]
                replica.dias_con_quiebre = kpis["dias_con_quiebre"]
                replica.inventario_promedio_tm = kpis["inventario_promedio_tm"]
                replica.inventario_minimo_tm = kpis["inventario_minimo_tm"]
                replica.autonomia_promedio_dias = kpis["autonomia_promedio_dias"]
                replica.demanda_insatisfecha_tm = kpis["demanda_insatisfecha_tm"]
                replica.disrupciones_totales = kpis["disrupciones_totales"]
            db.add(replica)
        db.commit()

        db.refresh(exp)
        stats = calcular_estadisticas_agregadas(exp.replicas)
        duration = time.time() - start_total

        if stats:
            sim = Simulacion(
                configuracion_id=exp.configuracion_id,
                estado="completed",
                nivel_servicio_pct=stats["nivel_servicio_mean"],
                probabilidad_quiebre_stock_pct=stats["probabilidad_quiebre_stock_mean"],
                dias_con_quiebre=int(stats["dias_con_quiebre_mean"]),
                inventario_promedio_tm=stats["inventario_promedio_mean"],
                inventario_minimo_tm=stats["inventario_minimo_mean"],
                inventario_std_tm=stats["inventario_promedio_std"],
                autonomia_promedio_dias=stats["autonomia_promedio_mean"],
                demanda_insatisfecha_tm=stats["demanda_insatisfecha_mean"],
                disrupciones_totales=int(stats["disrupciones_totales_mean"]),
                dias_simulados=params.get("duracion_simulacion_dias", 365),
                ejecutada_en=datetime.utcnow(),
                duracion_segundos=duration,
            )
            db.add(sim)
            db.commit()

        exp.estado = "completed"
        exp.progreso = 100
        exp.completado_en = datetime.utcnow()
        exp.duracion_segundos = duration
        exp.resultados_agregados = stats
        db.commit()
        db.refresh(exp)
        return exp

    except Exception as e:
        exp.estado = "failed"
        exp.error_mensaje = str(e)
        exp.completado_en = datetime.utcnow()
        db.commit()
        raise
    finally:
        db.close()
