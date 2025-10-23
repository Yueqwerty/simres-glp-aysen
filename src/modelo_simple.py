"""
Modelo SIMPLIFICADO de simulación para prueba de hipótesis de tesis.
Enfoque: Probar sensibilidad de resiliencia a factores exógenos vs endógenos.

Sistema minimal:
- Hub Coyhaique (inventario único)
- Demanda estocástica (clientes agregados)
- Ruta de suministro con disrupciones
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List
from dataclasses import dataclass, field

import simpy
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MetricasDiarias:
    """Registro de métricas de un día de simulación."""
    dia: int
    inventario_tm: float
    demanda_tm: float
    demanda_satisfecha_tm: float
    suministro_recibido_tm: float
    quiebre_stock: bool
    ruta_bloqueada: bool
    pedidos_pendientes: int


@dataclass
class ConfiguracionSimulacion:
    """Parámetros de configuración del sistema."""
    # Parámetros ENDÓGENOS (controlables)
    capacidad_hub_tm: float = 431.0  # Status quo Aysén
    punto_reorden_tm: float = 216.0  # 50% de capacidad
    cantidad_pedido_tm: float = 216.0  # Tamaño fijo de pedido (Q)
    inventario_inicial_tm: float = 258.0  # 60% inicial

    # Parámetros de demanda
    # Ajustado para obtener autonomía ~8.2 días: 431 TM / 52.5 TM/día = 8.2 días
    # Pero con estacionalidad promedio ~1.0 (no siempre en pico), usamos factor menor
    demanda_base_diaria_tm: float = 52.5  # Demanda promedio diaria
    factor_estacionalidad: float = 1.4  # Pico invernal (pero promedio anual ~1.0)
    variabilidad_demanda: float = 0.1  # ±10%

    # Parámetros de suministro
    lead_time_nominal_dias: float = 3.0  # Tiempo normal de entrega

    # Parámetros EXÓGENOS (disrupciones - NO controlables)
    tasa_disrupciones_anual: float = 4.0  # λ para Poisson
    duracion_disrupcion_min_dias: float = 3.0
    duracion_disrupcion_mode_dias: float = 7.0  # Valor más probable
    duracion_disrupcion_max_dias: float = 21.0  # Caso extremo Argentina

    # Control de simulación
    duracion_simulacion_dias: int = 365
    semilla_aleatoria: int = 42


class HubCoyhaique:
    """Hub de almacenamiento de GLP en Coyhaique (modelo agregado)."""

    def __init__(self, env: simpy.Environment, config: ConfiguracionSimulacion):
        self.env = env
        self.config = config

        # Inventario como recurso continuo
        self.inventario = simpy.Container(
            env,
            capacity=config.capacidad_hub_tm,
            init=config.inventario_inicial_tm
        )

        # Métricas
        self.total_recibido_tm = 0.0
        self.total_despachado_tm = 0.0
        self.quiebres_stock = 0

    def recibir_suministro(self, cantidad_tm: float) -> simpy.Event:
        """Recibe suministro de la ruta."""
        self.total_recibido_tm += cantidad_tm
        return self.inventario.put(cantidad_tm)

    def despachar_a_clientes(self, demanda_tm: float) -> float:
        """
        Despacha GLP a clientes.
        Retorna: cantidad realmente despachada (puede ser < demanda si hay quiebre).
        """
        disponible = self.inventario.level

        if disponible >= demanda_tm:
            # Satisfacer demanda completa
            self.inventario.get(demanda_tm)
            self.total_despachado_tm += demanda_tm
            return demanda_tm
        else:
            # Quiebre de stock: solo despachar lo disponible
            if disponible > 0:
                self.inventario.get(disponible)
                self.total_despachado_tm += disponible
            self.quiebres_stock += 1
            return disponible

    def necesita_reabastecimiento(self) -> bool:
        """Verifica si el inventario alcanzó el punto de reorden."""
        return self.inventario.level <= self.config.punto_reorden_tm


class RutaSuministro:
    """
    Modelo de la ruta de suministro con disrupciones estocásticas.
    Representa el punto único de falla del sistema.
    """

    def __init__(
        self,
        env: simpy.Environment,
        config: ConfiguracionSimulacion,
        rng: np.random.Generator
    ):
        self.env = env
        self.config = config
        self.rng = rng

        # Estado de la ruta
        self.bloqueada = False
        self.tiempo_desbloqueo = 0.0

        # Métricas
        self.disrupciones_totales = 0
        self.dias_bloqueados_acumulados = 0.0

    def esta_operativa(self) -> bool:
        """Verifica si la ruta está operativa."""
        if self.bloqueada and self.env.now >= self.tiempo_desbloqueo:
            # Finaliza la disrupción
            self.bloqueada = False
            logger.info(f"Día {self.env.now:.0f}: Ruta desbloqueada")

        return not self.bloqueada

    def bloquear_por_disrupcion(self, duracion_dias: float) -> None:
        """Bloquea la ruta por una disrupción."""
        self.bloqueada = True
        self.tiempo_desbloqueo = self.env.now + duracion_dias
        self.disrupciones_totales += 1
        self.dias_bloqueados_acumulados += duracion_dias

        logger.warning(
            f"Día {self.env.now:.0f}: DISRUPCIÓN - Ruta bloqueada por {duracion_dias:.1f} días"
        )

    def calcular_lead_time(self) -> float:
        """
        Calcula el lead time efectivo considerando disrupciones.
        Si la ruta está bloqueada, el lead time se extiende.
        """
        lt_base = self.config.lead_time_nominal_dias

        if self.bloqueada:
            # Agregar el tiempo restante de bloqueo
            tiempo_restante = max(0, self.tiempo_desbloqueo - self.env.now)
            return lt_base + tiempo_restante

        return lt_base


class SimulacionMinimal:
    """
    Simulación minimal para prueba de hipótesis.

    Objetivo: Cuantificar sensibilidad de resiliencia a:
    - Factor ENDÓGENO: capacidad_hub_tm
    - Factor EXÓGENO: duracion_disrupcion_max_dias
    """

    def __init__(self, config: ConfiguracionSimulacion):
        self.config = config
        self.rng = np.random.default_rng(config.semilla_aleatoria)

        # Entorno SimPy
        self.env = simpy.Environment()

        # Entidades
        self.hub = HubCoyhaique(self.env, config)
        self.ruta = RutaSuministro(self.env, config, self.rng)

        # Tracking de pedidos en tránsito
        self.pedidos_en_transito: List[simpy.Event] = []

        # Métricas globales
        self.metricas_diarias: List[MetricasDiarias] = []
        self.demanda_total_tm = 0.0
        self.demanda_satisfecha_tm = 0.0

    def run(self) -> None:
        """Ejecuta la simulación."""
        # Procesos principales
        self.env.process(self._proceso_demanda_diaria())
        self.env.process(self._proceso_reabastecimiento())
        self.env.process(self._proceso_disrupciones())

        # Ejecutar
        logger.info(f"Iniciando simulación por {self.config.duracion_simulacion_dias} días")
        self.env.run(until=self.config.duracion_simulacion_dias)
        logger.info("Simulación completada")

    def _proceso_demanda_diaria(self):
        """Genera y satisface demanda diaria."""
        dia = 0

        while True:
            # Calcular demanda del día
            demanda_base = self.config.demanda_base_diaria_tm

            # Factor estacional (pico en invierno austral: junio-agosto)
            # Ajustado para que el promedio anual sea ~1.0
            dia_del_anio = dia % 365
            # Senoidal centrada en 1.0, con amplitud que da pico de 1.3 y valle de 0.7
            factor_estacional = 1.0 + 0.3 * np.sin(2 * np.pi * (dia_del_anio - 172) / 365.0)

            # Variabilidad aleatoria
            ruido = self.rng.normal(1.0, self.config.variabilidad_demanda)

            demanda_dia = demanda_base * factor_estacional * ruido

            # Intentar satisfacer demanda
            despachado = self.hub.despachar_a_clientes(demanda_dia)

            # Actualizar métricas
            self.demanda_total_tm += demanda_dia
            self.demanda_satisfecha_tm += despachado

            # Registrar métricas del día
            self.metricas_diarias.append(MetricasDiarias(
                dia=dia,
                inventario_tm=self.hub.inventario.level,
                demanda_tm=demanda_dia,
                demanda_satisfecha_tm=despachado,
                suministro_recibido_tm=0.0,  # Se actualiza en llegadas
                quiebre_stock=(despachado < demanda_dia),
                ruta_bloqueada=self.ruta.bloqueada,
                pedidos_pendientes=len(self.pedidos_en_transito)
            ))

            # Avanzar un día
            yield self.env.timeout(1.0)
            dia += 1

    def _proceso_reabastecimiento(self):
        """Gestiona política de reabastecimiento (Q,R)."""
        while True:
            # Verificar si necesita pedir
            if self.hub.necesita_reabastecimiento():
                # Verificar que la ruta esté operativa
                if self.ruta.esta_operativa():
                    # Crear pedido
                    cantidad = self.config.cantidad_pedido_tm

                    # Calcular lead time (puede estar extendido por disrupción)
                    lead_time = self.ruta.calcular_lead_time()

                    logger.info(
                        f"Día {self.env.now:.0f}: Pedido creado - "
                        f"{cantidad:.0f} TM, ETA={lead_time:.1f} días"
                    )

                    # Programar llegada
                    evento_llegada = self.env.process(
                        self._llegada_suministro(cantidad, lead_time)
                    )
                    self.pedidos_en_transito.append(evento_llegada)
                else:
                    logger.debug(
                        f"Día {self.env.now:.0f}: No se puede pedir (ruta bloqueada)"
                    )

            # Verificar cada día
            yield self.env.timeout(1.0)

    def _llegada_suministro(self, cantidad_tm: float, lead_time_dias: float):
        """Simula la llegada de un pedido después del lead time."""
        yield self.env.timeout(lead_time_dias)

        # Llegó el suministro
        yield self.hub.recibir_suministro(cantidad_tm)

        # Actualizar métrica del día
        if self.metricas_diarias:
            self.metricas_diarias[-1].suministro_recibido_tm += cantidad_tm

        logger.info(
            f"Día {self.env.now:.0f}: Suministro recibido - {cantidad_tm:.0f} TM"
        )

        # Remover de pedidos en tránsito
        if self in self.pedidos_en_transito:
            self.pedidos_en_transito.remove(self)

    def _proceso_disrupciones(self):
        """
        Genera disrupciones estocásticas en la ruta.

        Frecuencia: Proceso de Poisson con λ = config.tasa_disrupciones_anual
        Duración: Distribución Triangular(min, mode, max)
        """
        lambda_dias = self.config.tasa_disrupciones_anual / 365.0

        while True:
            # Tiempo hasta próxima disrupción (Exponencial)
            tiempo_hasta_proxima = self.rng.exponential(1.0 / lambda_dias)

            yield self.env.timeout(tiempo_hasta_proxima)

            # Generar disrupción
            duracion = self.rng.triangular(
                self.config.duracion_disrupcion_min_dias,
                self.config.duracion_disrupcion_mode_dias,
                self.config.duracion_disrupcion_max_dias
            )

            self.ruta.bloquear_por_disrupcion(duracion)

    def calcular_kpis(self) -> Dict[str, Any]:
        """Calcula los KPIs principales para análisis."""
        # Nivel de Servicio (métrica principal de resiliencia)
        nivel_servicio_pct = (
            (self.demanda_satisfecha_tm / self.demanda_total_tm * 100.0)
            if self.demanda_total_tm > 0 else 0.0
        )

        # Contar días con quiebre de stock
        dias_con_quiebre = sum(1 for m in self.metricas_diarias if m.quiebre_stock)

        # Inventario promedio y mínimo
        inventarios = [m.inventario_tm for m in self.metricas_diarias]
        inventario_promedio = np.mean(inventarios) if inventarios else 0.0
        inventario_minimo = np.min(inventarios) if inventarios else 0.0

        return {
            # KPI PRINCIPAL
            'nivel_servicio_pct': nivel_servicio_pct,

            # KPIs secundarios
            'probabilidad_quiebre_stock_pct': (dias_con_quiebre / len(self.metricas_diarias) * 100.0),
            'dias_con_quiebre': dias_con_quiebre,
            'inventario_promedio_tm': inventario_promedio,
            'inventario_minimo_tm': inventario_minimo,

            # Métricas de disrupciones
            'disrupciones_totales': self.ruta.disrupciones_totales,
            'dias_bloqueados_total': self.ruta.dias_bloqueados_acumulados,
            'pct_tiempo_bloqueado': (self.ruta.dias_bloqueados_acumulados / self.config.duracion_simulacion_dias * 100.0),

            # Validación
            'autonomia_promedio_dias': inventario_promedio / self.config.demanda_base_diaria_tm,
        }


# Función helper para ejecutar una simulación
def ejecutar_simulacion_simple(config: ConfiguracionSimulacion) -> Dict[str, Any]:
    """
    Ejecuta una simulación con la configuración dada.

    Returns:
        Diccionario con KPIs de la simulación.
    """
    sim = SimulacionMinimal(config)
    sim.run()
    return sim.calcular_kpis()


if __name__ == "__main__":
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    # Ejemplo: Simulación con parámetros por defecto
    config = ConfiguracionSimulacion()

    logger.info("="*60)
    logger.info("SIMULACIÓN MINIMAL - PRUEBA DE CONCEPTO")
    logger.info("="*60)

    resultados = ejecutar_simulacion_simple(config)

    print("\n" + "="*60)
    print("RESULTADOS")
    print("="*60)
    for kpi, valor in resultados.items():
        print(f"{kpi:.<40} {valor:.2f}")
