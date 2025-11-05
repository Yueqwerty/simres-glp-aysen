"""
Entidades del sistema de suministro de GLP.

HubCoyhaique: Tanques de almacenamiento.
RutaSuministro: Ruta de transporte con disrupciones.

Author: Carlos Subiabre
"""
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import simpy
import numpy as np

if TYPE_CHECKING:
    from configuracion import ConfiguracionSimulacion

logger = logging.getLogger(__name__)


class HubCoyhaique:
    """
    Tanques de GLP en Coyhaique (Abastible + Lipigas + Gasco).

    Maneja el inventario y registra cuando hay quiebres.
    """

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
        """Recibe suministro y lo agrega al inventario."""
        self.totalRecibidoTm += cantidadTm
        return self.inventario.put(cantidadTm)

    def despacharAClientes(self, demandaTm: float) -> float:
        """Despacha lo que se pueda. Retorna cuanto se despacho realmente."""
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
        """Verifica si el inventario ya bajo del punto de reorden."""
        return self.inventario.level <= self.config.puntoReordenTm


class RutaSuministro:
    """
    Ruta de transporte con disrupciones aleatorias.

    Ruta Neuquen/Cabo Negro -> Coyhaique que se bloquea a veces.
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

        self.bloqueada = False
        self.tiempoDesbloqueo = 0.0

        self.disrupcionesTotales = 0
        self.diasBloqueadosAcumulados = 0.0

    def estaOperativa(self) -> bool:
        """Verifica si la ruta esta libre. Se desbloquea sola cuando termina el tiempo."""
        if self.bloqueada and self.env.now >= self.tiempoDesbloqueo:
            self.bloqueada = False
            logger.info(f"Dia {self.env.now:.0f}: Ruta desbloqueada")
        return not self.bloqueada

    def bloquearPorDisrupcion(self, duracionDias: float) -> None:
        """Bloquea la ruta por X dias."""
        self.bloqueada = True
        self.tiempoDesbloqueo = self.env.now + duracionDias
        self.disrupcionesTotales += 1
        self.diasBloqueadosAcumulados += duracionDias

        logger.warning(
            f"Dia {self.env.now:.0f}: Disrupcion #{self.disrupcionesTotales} - "
            f"Ruta bloqueada por {duracionDias:.1f} dias (hasta dia {self.tiempoDesbloqueo:.0f})"
        )

    def calcularLeadTime(self) -> float:
        """Calcula cuanto tarda en llegar un pedido (incluye tiempo de bloqueo)."""
        leadTimeBase = self.config.leadTimeNominalDias

        if self.bloqueada:
            tiempoRestante = max(0, self.tiempoDesbloqueo - self.env.now)
            return leadTimeBase + tiempoRestante

        return leadTimeBase
