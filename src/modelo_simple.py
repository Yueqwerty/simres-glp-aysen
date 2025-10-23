"""
Sistema:
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
    """
    Parámetros de configuración del sistema.

    FUENTES DE DATOS:
    - Informe CNE 2024: Vulnerabilidad de Suministro de GLP en Aysén
    - Datos operativos distribuidores (Abastible, Lipigas, Gasco)
    """
    # Parámetros ENDÓGENOS (controlables por inversión/política)
    capacidad_hub_tm: float = 431.0  # Status quo Aysén (150+240+41 TM)

    # Política (Q,R) calibrada para demanda real:
    # - Demanda durante lead time: 41.3 × 6 = 248 TM
    # - Punto de reorden: debe cubrir LT demand + buffer de seguridad
    # - Cantidad pedido: reponer sustancialmente para mantener autonomía
    punto_reorden_tm: float = 300.0  # 70% capacidad (~7.3 días autonomía)
    cantidad_pedido_tm: float = 280.0  # 65% capacidad (~6.8 días demanda)
    inventario_inicial_tm: float = 380.0  # 88% inicial (sistema bien abastecido)

    # Parámetros de demanda
    # FUENTE: Informe CNE 2024 - Aysén
    # Demanda GLP 2023: 15,061 TM/año → 41.3 TM/día promedio
    # Validación autonomía: 431 TM / 41.3 TM/día = 10.4 días ✓
    demanda_base_diaria_tm: float = 41.3  # Demanda promedio anual real
    variabilidad_demanda: float = 0.10  # ±10% variabilidad estocástica

    # Parámetros de suministro
    # FUENTE: Datos operativos distribuidores
    # Ruta Cabo Negro-Coyhaique: 5.5-7.5 días round trip
    # Ruta Neuquén-Coyhaique: similar
    # Simplificado a lead time promedio de entrega
    lead_time_nominal_dias: float = 6.0  # Tiempo normal de entrega (round trip promedio)

    # Parámetros EXÓGENOS (disrupciones - NO controlables)
    # FUENTE: Informe CNE 2024 - Matriz de Riesgos
    # Frecuencia Nivel 4: 4 eventos/año (nevadas, conflictos)
    # Duración histórica: 3-21 días (conflicto Argentina 2021: 21 días)
    tasa_disrupciones_anual: float = 4.0  # λ para Poisson (Nivel 4)
    duracion_disrupcion_min_dias: float = 3.0  # Mínimo histórico
    duracion_disrupcion_mode_dias: float = 7.0  # Valor más probable
    duracion_disrupcion_max_dias: float = 21.0  # Máximo histórico (Argentina)

    # Control de simulación
    duracion_simulacion_dias: int = 365
    semilla_aleatoria: int = 42

    def validar(self) -> None:
        """Valida que los parámetros sean consistentes."""
        assert self.capacidad_hub_tm > 0, "Capacidad debe ser positiva"
        assert self.punto_reorden_tm < self.capacidad_hub_tm, "ROP debe ser < capacidad"
        assert self.cantidad_pedido_tm > 0, "Cantidad de pedido debe ser positiva"
        assert self.inventario_inicial_tm <= self.capacidad_hub_tm, "Inventario inicial debe ser ≤ capacidad"
        assert self.demanda_base_diaria_tm > 0, "Demanda base debe ser positiva"
        assert 0 <= self.variabilidad_demanda < 1, "Variabilidad debe estar en [0,1)"
        assert self.lead_time_nominal_dias > 0, "Lead time debe ser positivo"
        assert self.tasa_disrupciones_anual >= 0, "Tasa de disrupciones debe ser ≥ 0"
        assert self.duracion_disrupcion_min_dias >= 0, "Duración mínima debe ser ≥ 0"
        assert self.duracion_disrupcion_min_dias <= self.duracion_disrupcion_mode_dias <= self.duracion_disrupcion_max_dias, \
            "Duraciones deben cumplir: min ≤ mode ≤ max"
        assert self.duracion_simulacion_dias > 0, "Duración de simulación debe ser positiva"


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

            # Variabilidad aleatoria (ruido estocástico diario)
            # Simplificado: SIN estacionalidad para facilitar análisis
            ruido = self.rng.normal(1.0, self.config.variabilidad_demanda)

            demanda_dia = max(0.0, demanda_base * ruido)

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
        """
        Gestiona política de reabastecimiento (Q,R).

        Regla: Cuando inventario ≤ R, pedir Q (máximo 2 pedidos simultáneos).
        """
        MAX_PEDIDOS_SIMULTANEOS = 2

        while True:
            # Verificar si necesita pedir
            if self.hub.necesita_reabastecimiento():
                # Permitir máximo 2 pedidos simultáneos para evitar colapso
                if len(self.pedidos_en_transito) < MAX_PEDIDOS_SIMULTANEOS:
                    # Verificar que la ruta esté operativa
                    if self.ruta.esta_operativa():
                        # Crear pedido
                        cantidad = self.config.cantidad_pedido_tm

                        # Calcular lead time (puede estar extendido por disrupción)
                        lead_time = self.ruta.calcular_lead_time()

                        logger.info(
                            f"Día {self.env.now:.0f}: Pedido creado - "
                            f"{cantidad:.0f} TM, ETA={lead_time:.1f} días "
                            f"(pedidos en tránsito: {len(self.pedidos_en_transito)})"
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
                else:
                    logger.debug(
                        f"Día {self.env.now:.0f}: Inventario bajo pero hay {len(self.pedidos_en_transito)} pedido(s) en tránsito (límite alcanzado)"
                    )

            # Verificar cada día
            yield self.env.timeout(1.0)

    def _llegada_suministro(self, cantidad_tm: float, lead_time_dias: float):
        """Simula la llegada de un pedido después del lead time."""
        # Guardar referencia al evento actual
        evento_actual = self.env.active_process

        yield self.env.timeout(lead_time_dias)

        # Llegó el suministro
        yield self.hub.recibir_suministro(cantidad_tm)

        # Actualizar métrica del día
        if self.metricas_diarias:
            self.metricas_diarias[-1].suministro_recibido_tm += cantidad_tm

        logger.info(
            f"Día {self.env.now:.0f}: Suministro recibido - {cantidad_tm:.0f} TM, "
            f"Inventario actual: {self.hub.inventario.level:.1f} TM"
        )

        # Remover de pedidos en tránsito
        if evento_actual in self.pedidos_en_transito:
            self.pedidos_en_transito.remove(evento_actual)

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
        """
        Calcula los KPIs principales para análisis de resiliencia.

        Returns:
            Diccionario con métricas de rendimiento del sistema.
        """
        # Nivel de Servicio (métrica principal de resiliencia)
        # NS = Demanda satisfecha / Demanda total
        nivel_servicio_pct = (
            (self.demanda_satisfecha_tm / self.demanda_total_tm * 100.0)
            if self.demanda_total_tm > 0 else 0.0
        )

        # Contar días con quiebre de stock
        dias_con_quiebre = sum(1 for m in self.metricas_diarias if m.quiebre_stock)
        dias_totales = len(self.metricas_diarias)

        # Inventario: estadísticas descriptivas
        inventarios = [m.inventario_tm for m in self.metricas_diarias]
        inventario_promedio = np.mean(inventarios) if inventarios else 0.0
        inventario_minimo = np.min(inventarios) if inventarios else 0.0
        inventario_maximo = np.max(inventarios) if inventarios else 0.0
        inventario_std = np.std(inventarios) if inventarios else 0.0

        # Demanda: estadísticas
        demandas = [m.demanda_tm for m in self.metricas_diarias]
        demanda_promedio = np.mean(demandas) if demandas else 0.0
        demanda_maxima = np.max(demandas) if demandas else 0.0

        # Autonomía promedio (días de inventario)
        autonomia_promedio_dias = (
            inventario_promedio / demanda_promedio
            if demanda_promedio > 0 else 0.0
        )

        return {
            'nivel_servicio_pct': round(nivel_servicio_pct, 2),
            'probabilidad_quiebre_stock_pct': round((dias_con_quiebre / dias_totales * 100.0), 2),
            'dias_con_quiebre': dias_con_quiebre,

            'inventario_promedio_tm': round(inventario_promedio, 2),
            'inventario_minimo_tm': round(inventario_minimo, 2),
            'inventario_maximo_tm': round(inventario_maximo, 2),
            'inventario_std_tm': round(inventario_std, 2),
            'autonomia_promedio_dias': round(autonomia_promedio_dias, 2),

            'demanda_total_tm': round(self.demanda_total_tm, 2),
            'demanda_satisfecha_tm': round(self.demanda_satisfecha_tm, 2),
            'demanda_insatisfecha_tm': round(self.demanda_total_tm - self.demanda_satisfecha_tm, 2),
            'demanda_promedio_diaria_tm': round(demanda_promedio, 2),
            'demanda_maxima_diaria_tm': round(demanda_maxima, 2),

            'disrupciones_totales': self.ruta.disrupciones_totales,
            'dias_bloqueados_total': round(self.ruta.dias_bloqueados_acumulados, 2),
            'pct_tiempo_bloqueado': round(
                (self.ruta.dias_bloqueados_acumulados / self.config.duracion_simulacion_dias * 100.0), 2
            ),

            'dias_simulados': dias_totales,
        }


# Función helper para ejecutar una simulación
def ejecutar_simulacion_simple(config: ConfiguracionSimulacion) -> Dict[str, Any]:
    """
    Ejecuta una simulación con la configuración dada.

    Args:
        config: Configuración de parámetros del sistema.

    Returns:
        Diccionario con KPIs de la simulación.

    Raises:
        AssertionError: Si la configuración tiene parámetros inválidos.
    """
    # Validar configuración antes de simular
    config.validar()

    # Ejecutar simulación
    sim = SimulacionMinimal(config)
    sim.run()

    # Retornar KPIs
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
