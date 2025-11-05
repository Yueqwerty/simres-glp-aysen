"""
Metricas y KPIs del Sistema de Suministro de GLP.

Author: Carlos Subiabre
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List
import numpy as np


@dataclass
class MetricasDiarias:
    """Registro de metricas operacionales de un dia."""

    dia: int
    inventarioTm: float
    demandaTm: float
    demandaSatisfechaTm: float
    suministroRecibidoTm: float
    quiebreStock: bool
    rutaBloqueada: bool
    pedidosPendientes: int
    diasAutonomia: float


def calcularKpis(
    metricasDiarias: List[MetricasDiarias],
    demandaTotalTm: float,
    demandaSatisfechaTm: float,
    inventarioInicialTm: float,
    inventarioFinalTm: float,
    totalRecibidoTm: float,
    totalDespachadoTm: float,
    disrupcionesTotales: int,
    diasBloqueadosTotal: float,
    duracionSimulacionDias: int
) -> Dict[str, Any]:
    """
    Calcula indicadores clave de desempeno.

    Returns:
        Dict con KPIs: nivel_servicio_pct, probabilidad_quiebre_stock_pct,
        inventario_promedio_tm, autonomia_promedio_dias, etc.
    """
    # Nivel de servicio
    nivelServicioPct = (
        (demandaSatisfechaTm / demandaTotalTm * 100.0)
        if demandaTotalTm > 0 else 0.0
    )

    # Quiebres de stock
    diasConQuiebre = sum(1 for m in metricasDiarias if m.quiebreStock)
    diasTotales = len(metricasDiarias)
    probabilidadQuiebrePct = (diasConQuiebre / diasTotales * 100.0) if diasTotales > 0 else 0.0

    # Estadisticas de inventario
    inventarios = [m.inventarioTm for m in metricasDiarias]
    inventarioPromedio = float(np.mean(inventarios)) if inventarios else 0.0
    inventarioMinimo = float(np.min(inventarios)) if inventarios else 0.0
    inventarioMaximo = float(np.max(inventarios)) if inventarios else 0.0
    inventarioStd = float(np.std(inventarios)) if inventarios else 0.0

    # Estadisticas de autonomia
    autonomias = [m.diasAutonomia for m in metricasDiarias]
    autonomiaPromedio = float(np.mean(autonomias)) if autonomias else 0.0
    autonomiaMinima = float(np.min(autonomias)) if autonomias else 0.0

    # Estadisticas de demanda
    demandas = [m.demandaTm for m in metricasDiarias]
    demandaPromedio = float(np.mean(demandas)) if demandas else 0.0
    demandaMaxima = float(np.max(demandas)) if demandas else 0.0
    demandaMinima = float(np.min(demandas)) if demandas else 0.0

    # Metricas de disrupciones
    pctTiempoBloqueado = (diasBloqueadosTotal / duracionSimulacionDias * 100.0) if duracionSimulacionDias > 0 else 0.0

    return {
        # Nivel de servicio
        'nivel_servicio_pct': round(nivelServicioPct, 4),
        'probabilidad_quiebre_stock_pct': round(probabilidadQuiebrePct, 4),
        'dias_con_quiebre': diasConQuiebre,

        # Inventario
        'inventario_promedio_tm': round(inventarioPromedio, 2),
        'inventario_minimo_tm': round(inventarioMinimo, 2),
        'inventario_maximo_tm': round(inventarioMaximo, 2),
        'inventario_final_tm': round(inventarioFinalTm, 2),
        'inventario_inicial_tm': round(inventarioInicialTm, 2),
        'inventario_std_tm': round(inventarioStd, 2),

        # Autonomia
        'autonomia_promedio_dias': round(autonomiaPromedio, 2),
        'autonomia_minima_dias': round(autonomiaMinima, 2),

        # Demanda
        'demanda_total_tm': round(demandaTotalTm, 2),
        'demanda_satisfecha_tm': round(demandaSatisfechaTm, 2),
        'demanda_insatisfecha_tm': round(demandaTotalTm - demandaSatisfechaTm, 2),
        'demanda_promedio_diaria_tm': round(demandaPromedio, 2),
        'demanda_maxima_diaria_tm': round(demandaMaxima, 2),
        'demanda_minima_diaria_tm': round(demandaMinima, 2),

        # Flujo
        'total_recibido_tm': round(totalRecibidoTm, 2),
        'total_despachado_tm': round(totalDespachadoTm, 2),

        # Disrupciones
        'disrupciones_totales': disrupcionesTotales,
        'dias_bloqueados_total': round(diasBloqueadosTotal, 2),
        'pct_tiempo_bloqueado': round(pctTiempoBloqueado, 2),

        # Control
        'dias_simulados': diasTotales,
    }
