"""
Modelo de Simulacion de Eventos Discretos
Sistema de Suministro de GLP en Region de Aysen

Implementacion de simulacion estocastica para analisis de resiliencia
de la cadena de suministro de Gas Licuado de Petroleo.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List
from dataclasses import dataclass
import math

import simpy
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class MetricasDiarias:
    """Registro de metricas operacionales diarias."""
    dia: int
    inventarioTm: float
    demandaTm: float
    demandaSatisfechaTm: float
    suministroRecibidoTm: float
    quiebreStock: bool
    rutaBloqueada: bool
    pedidosPendientes: int
    diasAutonomia: float


@dataclass
class ConfiguracionSimulacion:
    """
    Parametros de configuracion del sistema de suministro.

    Fuentes:
    - Informe CNE 2024: Vulnerabilidad de Suministro de GLP en Aysen
    - Datos operativos de distribuidores regionales
    """

    # Parametros de capacidad
    capacidadHubTm: float = 431.0
    puntoReordenTm: float = 215.5
    cantidadPedidoTm: float = 215.5
    inventarioInicialTm: float = 258.6

    # Parametros de demanda
    demandaBaseDiariaTm: float = 52.5
    variabilidadDemanda: float = 0.15
    amplitudEstacional: float = 0.30
    diaPicoInvernal: int = 200

    # Parametros operacionales
    leadTimeNominalDias: float = 6.0

    # Parametros de riesgo
    tasaDisrupcionesAnual: float = 4.0
    duracionDisrupcionMinDias: float = 3.0
    duracionDisrupcionModeDias: float = 7.0
    duracionDisrupcionMaxDias: float = 21.0

    # Control de simulacion
    duracionSimulacionDias: int = 365
    semillaAleatoria: int = 42
    usarEstacionalidad: bool = True

    def validar(self) -> None:
        """Valida consistencia de parametros."""
        assert self.capacidadHubTm > 0, "Capacidad debe ser positiva"
        assert self.puntoReordenTm < self.capacidadHubTm, "Punto de reorden debe ser menor que capacidad"
        assert self.cantidadPedidoTm > 0, "Cantidad de pedido debe ser positiva"
        assert self.inventarioInicialTm <= self.capacidadHubTm, "Inventario inicial debe ser menor o igual a capacidad"
        assert self.demandaBaseDiariaTm > 0, "Demanda base debe ser positiva"
        assert 0 <= self.variabilidadDemanda < 1, "Variabilidad debe estar en [0,1)"
        assert 0 <= self.amplitudEstacional < 1, "Amplitud estacional debe estar en [0,1)"
        assert self.leadTimeNominalDias > 0, "Lead time debe ser positivo"
        assert self.tasaDisrupcionesAnual >= 0, "Tasa de disrupciones debe ser no negativa"
        assert self.duracionDisrupcionMinDias >= 0, "Duracion minima debe ser no negativa"
        assert self.duracionDisrupcionMinDias <= self.duracionDisrupcionModeDias <= self.duracionDisrupcionMaxDias, \
            "Duraciones deben cumplir: min <= mode <= max"
        assert self.duracionSimulacionDias > 0, "Duracion de simulacion debe ser positiva"


class HubCoyhaique:
    """Centro de almacenamiento y distribucion de GLP."""

    def __init__(self, env: simpy.Environment, config: ConfiguracionSimulacion):
        self.env = env
        self.config = config

        self.inventario = simpy.Container(
            env,
            capacity=config.capacidadHubTm,
            init=config.inventarioInicialTm
        )

        self.totalRecibidoTm = 0.0
        self.totalDespachadoTm = 0.0
        self.quiebresStock = 0

    def recibirSuministro(self, cantidadTm: float) -> simpy.Event:
        """Recibe suministro externo."""
        self.totalRecibidoTm += cantidadTm
        return self.inventario.put(cantidadTm)

    def despacharAClientes(self, demandaTm: float) -> float:
        """
        Despacha producto a clientes.
        Retorna cantidad efectivamente despachada.
        """
        disponible = self.inventario.level

        if disponible >= demandaTm:
            self.inventario.get(demandaTm)
            self.totalDespachadoTm += demandaTm
            return demandaTm
        else:
            if disponible > 0:
                self.inventario.get(disponible)
                self.totalDespachadoTm += disponible
            self.quiebresStock += 1
            return disponible

    def necesitaReabastecimiento(self) -> bool:
        """Verifica si se alcanzo el punto de reorden."""
        return self.inventario.level <= self.config.puntoReordenTm


class RutaSuministro:
    """Sistema de transporte con disrupciones estocasticas."""

    def __init__(
        self,
        env: simpy.Environment,
        config: ConfiguracionSimulacion,
        rng: np.random.Generator
    ):
        self.env = env
        self.config = config
        self.rng = rng

        self.bloqueada = False
        self.tiempoDesbloqueo = 0.0

        self.disrupcionesTotales = 0
        self.diasBloqueadosAcumulados = 0.0

    def estaOperativa(self) -> bool:
        """Verifica estado operacional de la ruta."""
        if self.bloqueada and self.env.now >= self.tiempoDesbloqueo:
            self.bloqueada = False
            logger.info(f"Dia {self.env.now:.0f}: Ruta desbloqueada")

        return not self.bloqueada

    def bloquearPorDisrupcion(self, duracionDias: float) -> None:
        """Registra evento de disrupcion."""
        self.bloqueada = True
        self.tiempoDesbloqueo = self.env.now + duracionDias
        self.disrupcionesTotales += 1
        self.diasBloqueadosAcumulados += duracionDias

        logger.warning(
            f"Dia {self.env.now:.0f}: Disrupcion #{self.disrupcionesTotales} - "
            f"Ruta bloqueada por {duracionDias:.1f} dias (hasta dia {self.tiempoDesbloqueo:.0f})"
        )

    def calcularLeadTime(self) -> float:
        """Calcula lead time efectivo considerando disrupciones."""
        leadTimeBase = self.config.leadTimeNominalDias

        if self.bloqueada:
            tiempoRestante = max(0, self.tiempoDesbloqueo - self.env.now)
            return leadTimeBase + tiempoRestante

        return leadTimeBase


class SimulacionGlpAysen:
    """
    Simulacion de eventos discretos del sistema de suministro.

    Implementa politica de inventario (Q,R) con disrupciones estocasticas
    y demanda con estacionalidad invernal.
    """

    def __init__(self, config: ConfiguracionSimulacion):
        self.config = config
        self.rng = np.random.default_rng(config.semillaAleatoria)

        self.env = simpy.Environment()

        self.hub = HubCoyhaique(self.env, config)
        self.ruta = RutaSuministro(self.env, config, self.rng)

        self.pedidosEnTransito: List[simpy.Event] = []

        self.metricasDiarias: List[MetricasDiarias] = []
        self.demandaTotalTm = 0.0
        self.demandaSatisfechaTm = 0.0

    def calcularDemandaDia(self, dia: int) -> float:
        """
        Calcula demanda diaria con estacionalidad y variabilidad estocastica.

        Modelo: D(t) = D_base * (1 + A*sin(2*pi*(t - t_peak)/365)) * epsilon
        """
        demandaBase = self.config.demandaBaseDiariaTm

        if self.config.usarEstacionalidad:
            fase = 2 * math.pi * (dia - self.config.diaPicoInvernal) / 365.0
            factorEstacional = 1.0 + self.config.amplitudEstacional * math.sin(fase)
        else:
            factorEstacional = 1.0

        ruido = self.rng.normal(1.0, self.config.variabilidadDemanda)

        demanda = max(0.0, demandaBase * factorEstacional * ruido)

        return demanda

    def run(self) -> None:
        """Ejecuta la simulacion."""
        self.env.process(self._procesoDemandaDiaria())
        self.env.process(self._procesoReabastecimiento())
        self.env.process(self._procesoDisrupciones())

        logger.info(f"Iniciando simulacion por {self.config.duracionSimulacionDias} dias")
        logger.info(f"Configuracion: Cap={self.config.capacidadHubTm:.0f} TM, "
                   f"ROP={self.config.puntoReordenTm:.0f} TM, "
                   f"Q={self.config.cantidadPedidoTm:.0f} TM")
        self.env.run(until=self.config.duracionSimulacionDias)
        logger.info("Simulacion completada")

    def _procesoDemandaDiaria(self):
        """Procesa demanda diaria y despachos."""
        dia = 0

        while True:
            demandaDia = self.calcularDemandaDia(dia)
            despachado = self.hub.despacharAClientes(demandaDia)

            self.demandaTotalTm += demandaDia
            self.demandaSatisfechaTm += despachado

            inventarioActual = self.hub.inventario.level
            diasAutonomia = inventarioActual / demandaDia if demandaDia > 0 else 0.0

            self.metricasDiarias.append(MetricasDiarias(
                dia=dia,
                inventarioTm=inventarioActual,
                demandaTm=demandaDia,
                demandaSatisfechaTm=despachado,
                suministroRecibidoTm=0.0,
                quiebreStock=(despachado < demandaDia),
                rutaBloqueada=self.ruta.bloqueada,
                pedidosPendientes=len(self.pedidosEnTransito),
                diasAutonomia=diasAutonomia
            ))

            yield self.env.timeout(1.0)
            dia += 1

    def _procesoReabastecimiento(self):
        """Gestiona politica de reabastecimiento (Q,R)."""
        maxPedidosSimultaneos = 2

        while True:
            if self.hub.necesitaReabastecimiento():
                if len(self.pedidosEnTransito) < maxPedidosSimultaneos:
                    if self.ruta.estaOperativa():
                        cantidad = self.config.cantidadPedidoTm
                        leadTime = self.ruta.calcularLeadTime()

                        logger.info(
                            f"Dia {self.env.now:.0f}: Pedido creado - "
                            f"{cantidad:.0f} TM, LT={leadTime:.1f} dias, "
                            f"Inventario={self.hub.inventario.level:.0f} TM, "
                            f"Pedidos en transito={len(self.pedidosEnTransito)}"
                        )

                        eventoLlegada = self.env.process(
                            self._llegadaSuministro(cantidad, leadTime)
                        )
                        self.pedidosEnTransito.append(eventoLlegada)
                    else:
                        logger.debug(
                            f"Dia {self.env.now:.0f}: No se puede crear pedido (ruta bloqueada)"
                        )
                else:
                    logger.debug(
                        f"Dia {self.env.now:.0f}: Inventario bajo pero limite de pedidos alcanzado "
                        f"({len(self.pedidosEnTransito)} en transito)"
                    )

            yield self.env.timeout(1.0)

    def _llegadaSuministro(self, cantidadTm: float, leadTimeDias: float):
        """Procesa llegada de pedido."""
        eventoActual = self.env.active_process

        yield self.env.timeout(leadTimeDias)

        yield self.hub.recibirSuministro(cantidadTm)

        if self.metricasDiarias:
            self.metricasDiarias[-1].suministroRecibidoTm += cantidadTm

        logger.info(
            f"Dia {self.env.now:.0f}: Suministro recibido - {cantidadTm:.0f} TM, "
            f"Inventario={self.hub.inventario.level:.1f} TM"
        )

        if eventoActual in self.pedidosEnTransito:
            self.pedidosEnTransito.remove(eventoActual)

    def _procesoDisrupciones(self):
        """
        Genera disrupciones estocasticas.

        Frecuencia: Proceso de Poisson
        Duracion: Distribucion Triangular
        """
        lambdaDias = self.config.tasaDisrupcionesAnual / 365.0

        while True:
            tiempoHastaProxima = self.rng.exponential(1.0 / lambdaDias)

            yield self.env.timeout(tiempoHastaProxima)

            duracion = self.rng.triangular(
                self.config.duracionDisrupcionMinDias,
                self.config.duracionDisrupcionModeDias,
                self.config.duracionDisrupcionMaxDias
            )

            self.ruta.bloquearPorDisrupcion(duracion)

    def calcularKpis(self) -> Dict[str, Any]:
        """Calcula indicadores de desempeno del sistema."""
        nivelServicioPct = (
            (self.demandaSatisfechaTm / self.demandaTotalTm * 100.0)
            if self.demandaTotalTm > 0 else 0.0
        )

        diasConQuiebre = sum(1 for m in self.metricasDiarias if m.quiebreStock)
        diasTotales = len(self.metricasDiarias)

        inventarios = [m.inventarioTm for m in self.metricasDiarias]
        inventarioPromedio = np.mean(inventarios) if inventarios else 0.0
        inventarioMinimo = np.min(inventarios) if inventarios else 0.0
        inventarioMaximo = np.max(inventarios) if inventarios else 0.0
        inventarioStd = np.std(inventarios) if inventarios else 0.0

        autonomias = [m.diasAutonomia for m in self.metricasDiarias]
        autonomiaPromedio = np.mean(autonomias) if autonomias else 0.0
        autonomiaMinima = np.min(autonomias) if autonomias else 0.0

        demandas = [m.demandaTm for m in self.metricasDiarias]
        demandaPromedio = np.mean(demandas) if demandas else 0.0
        demandaMaxima = np.max(demandas) if demandas else 0.0
        demandaMinima = np.min(demandas) if demandas else 0.0

        return {
            'nivel_servicio_pct': round(nivelServicioPct, 4),
            'probabilidad_quiebre_stock_pct': round((diasConQuiebre / diasTotales * 100.0), 4),
            'dias_con_quiebre': diasConQuiebre,
            'inventario_promedio_tm': round(inventarioPromedio, 2),
            'inventario_minimo_tm': round(inventarioMinimo, 2),
            'inventario_maximo_tm': round(inventarioMaximo, 2),
            'inventario_std_tm': round(inventarioStd, 2),
            'autonomia_promedio_dias': round(autonomiaPromedio, 2),
            'autonomia_minima_dias': round(autonomiaMinima, 2),
            'demanda_total_tm': round(self.demandaTotalTm, 2),
            'demanda_satisfecha_tm': round(self.demandaSatisfechaTm, 2),
            'demanda_insatisfecha_tm': round(self.demandaTotalTm - self.demandaSatisfechaTm, 2),
            'demanda_promedio_diaria_tm': round(demandaPromedio, 2),
            'demanda_maxima_diaria_tm': round(demandaMaxima, 2),
            'demanda_minima_diaria_tm': round(demandaMinima, 2),
            'disrupciones_totales': self.ruta.disrupcionesTotales,
            'dias_bloqueados_total': round(self.ruta.diasBloqueadosAcumulados, 2),
            'pct_tiempo_bloqueado': round(
                (self.ruta.diasBloqueadosAcumulados / self.config.duracionSimulacionDias * 100.0), 2
            ),
            'dias_simulados': diasTotales,
        }


def ejecutarSimulacion(config: ConfiguracionSimulacion) -> Dict[str, Any]:
    """
    Ejecuta simulacion con configuracion especificada.

    Args:
        config: Parametros de configuracion del sistema

    Returns:
        Diccionario con indicadores de desempeno
    """
    config.validar()

    sim = SimulacionGlpAysen(config)
    sim.run()

    return sim.calcularKpis()


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(levelname)s: %(message)s'
    )

    config = ConfiguracionSimulacion()

    logger.info("="*70)
    logger.info("SIMULACION SISTEMA GLP AYSEN")
    logger.info("="*70)
    logger.info(f"Capacidad: {config.capacidadHubTm:.0f} TM")
    logger.info(f"Autonomia teorica: {config.capacidadHubTm / config.demandaBaseDiariaTm:.1f} dias")
    logger.info(f"Demanda base: {config.demandaBaseDiariaTm:.1f} TM/dia")
    logger.info(f"Estacionalidad: {'ACTIVADA' if config.usarEstacionalidad else 'DESACTIVADA'}")

    resultados = ejecutarSimulacion(config)

    print("\n" + "="*70)
    print("RESULTADOS")
    print("="*70)
    for kpi, valor in resultados.items():
        print(f"{kpi:.<50} {valor}")
