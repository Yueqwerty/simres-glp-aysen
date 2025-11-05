"""
Modelo de Simulacion de Eventos Discretos para Sistema GLP Aysen.

Este es el modulo principal que re-exporta todos los componentes del modelo
de simulacion. Provee una interfaz unificada para importaciones simples.

El modelo esta organizado en modulos especializados:
    - configuracion: Parametros del sistema
    - entidades: HubCoyhaique y RutaSuministro
    - metricas: MetricasDiarias y calculo de KPIs
    - simulacion: Motor de simulacion SimPy

Author:
    Carlos Subiabre

Examples:
    >>> from modelo import ConfiguracionSimulacion, ejecutarSimulacion
    >>> config = ConfiguracionSimulacion()
    >>> resultados = ejecutarSimulacion(config)
    >>> print(f"Nivel de servicio: {resultados['nivel_servicio_pct']:.2f}%")
"""
from __future__ import annotations

import logging

# Re-exportar todos los componentes del modelo
from configuracion import ConfiguracionSimulacion
from entidades import HubCoyhaique, RutaSuministro
from metricas import MetricasDiarias, calcularKpis
from simulacion import SimulacionGlpAysen, ejecutarSimulacion

__all__ = [
    'ConfiguracionSimulacion',
    'HubCoyhaique',
    'RutaSuministro',
    'MetricasDiarias',
    'calcularKpis',
    'SimulacionGlpAysen',
    'ejecutarSimulacion',
]

# Logger para ejecucion directa
logger = logging.getLogger(__name__)


if __name__ == "__main__":
    # Script de prueba basica
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    config = ConfiguracionSimulacion()

    logger.info("="*70)
    logger.info("SIMULACION SISTEMA GLP AYSEN")
    logger.info("="*70)
    logger.info(str(config))

    resultados = ejecutarSimulacion(config)

    print("\n" + "="*70)
    print("RESULTADOS")
    print("="*70)
    print(f"Nivel de Servicio:            {resultados['nivel_servicio_pct']:.2f}%")
    print(f"Probabilidad Quiebre Stock:   {resultados['probabilidad_quiebre_stock_pct']:.2f}%")
    print(f"Dias con Quiebre:             {resultados['dias_con_quiebre']}")
    print(f"Autonomia Promedio:           {resultados['autonomia_promedio_dias']:.2f} dias")
    print(f"Inventario Promedio:          {resultados['inventario_promedio_tm']:.1f} TM")
    print(f"Disrupciones Totales:         {resultados['disrupciones_totales']}")
    print(f"% Tiempo Bloqueado:           {resultados['pct_tiempo_bloqueado']:.2f}%")
    print("="*70)
