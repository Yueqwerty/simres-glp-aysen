"""
Simulador del sistema GLP Aysen.

Corre tres procesos en paralelo: demanda, reabastecimiento y disrupciones.

Author: Carlos Subiabre
"""
from __future__ import annotations

import logging
import math
from typing import Any, Dict, List

import simpy
import numpy as np

from configuracion import ConfiguracionSimulacion
from entidades import HubCoyhaique, RutaSuministro
from metricas import MetricasDiarias, calcularKpis

logger = logging.getLogger(__name__)


class SimulacionGlpAysen:
    """
    Simulacion del sistema de suministro de GLP.

    Corre tres cosas en paralelo:
    1. Demanda diaria que sube en invierno
    2. Pedidos cuando el inventario baja (politica Q,R)
    3. Disrupciones que bloquean la ruta aleatoriamente
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
        Calcula la demanda del dia. Sube en invierno, tiene variacion aleatoria.

        Formula: D(t) = D_base × [1 + A × sin(2π(t - t_peak)/365)] × ruido
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
        """Corre la simulacion."""
        self.env.process(self._procesoDemandaDiaria())
        self.env.process(self._procesoReabastecimiento())
        self.env.process(self._procesoDisrupciones())

        logger.info(f"Iniciando simulacion por {self.config.duracionSimulacionDias} dias")
        logger.info(
            f"Configuracion: Cap={self.config.capacidadHubTm:.0f} TM, "
            f"ROP={self.config.puntoReordenTm:.0f} TM, "
            f"Q={self.config.cantidadPedidoTm:.0f} TM"
        )

        self.env.run(until=self.config.duracionSimulacionDias)

        logger.info("Simulacion completada")

    def _procesoDemandaDiaria(self):
        """Proceso que genera la demanda diaria y despacha a clientes."""
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
        """Proceso que crea pedidos cuando el inventario baja del punto de reorden."""
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
        """Espera el lead time y luego recibe el pedido."""
        eventoActual = self.env.active_process

        yield self.env.timeout(leadTimeDias)

        yield self.hub.recibirSuministro(cantidadTm)

        # Actualizar metricas del dia actual
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
        Proceso que genera disrupciones que bloquean la ruta.

        La frecuencia es aleatoria (Poisson) y la duracion varia (Triangular).
        """
        if self.config.duracionDisrupcionMaxDias <= 0:
            return

        lambdaDias = self.config.tasaDisrupcionesAnual / 365.0

        while True:
            tiempoHastaProxima = self.rng.exponential(1.0 / lambdaDias)
            yield self.env.timeout(tiempoHastaProxima)

            # Duracion de disrupcion
            if (self.config.duracionDisrupcionMinDias == self.config.duracionDisrupcionModeDias ==
                self.config.duracionDisrupcionMaxDias):
                duracion = self.config.duracionDisrupcionMaxDias
            else:
                duracion = self.rng.triangular(
                    self.config.duracionDisrupcionMinDias,
                    self.config.duracionDisrupcionModeDias,
                    self.config.duracionDisrupcionMaxDias
                )

            self.ruta.bloquearPorDisrupcion(duracion)

    def calcularKpis(self) -> Dict[str, Any]:
        """Calcula los indicadores de desempeno."""
        return calcularKpis(
            metricasDiarias=self.metricasDiarias,
            demandaTotalTm=self.demandaTotalTm,
            demandaSatisfechaTm=self.demandaSatisfechaTm,
            inventarioInicialTm=self.config.inventarioInicialTm,
            inventarioFinalTm=self.hub.inventario.level,
            totalRecibidoTm=self.hub.totalRecibidoTm,
            totalDespachadoTm=self.hub.totalDespachadoTm,
            disrupcionesTotales=self.ruta.disrupcionesTotales,
            diasBloqueadosTotal=self.ruta.diasBloqueadosAcumulados,
            duracionSimulacionDias=self.config.duracionSimulacionDias
        )


def ejecutarSimulacion(config: ConfiguracionSimulacion) -> Dict[str, Any]:
    """
    Corre la simulacion con los parametros dados.

    Valida, simula y retorna los resultados.
    """
    config.validar()

    sim = SimulacionGlpAysen(config)
    sim.run()

    return sim.calcularKpis()
