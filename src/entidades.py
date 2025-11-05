"""
Entidades del Sistema de Suministro de GLP.

HubCoyhaique: Centro de almacenamiento y distribucion.
RutaSuministro: Sistema de transporte con disrupciones.

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
    Centro de almacenamiento de GLP (tanques Abastible + Lipigas + Gasco).

    Gestiona inventario con politica (Q,R) y registra quiebres de stock.
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
        """Recibe suministro y agrega al inventario."""
        self.totalRecibidoTm += cantidadTm
        return self.inventario.put(cantidadTm)

    def despacharAClientes(self, demandaTm: float) -> float:
        """Despacha demanda. Retorna cantidad efectivamente despachada."""
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
        """Verifica si inventario <= punto de reorden."""
        return self.inventario.level <= self.config.puntoReordenTm


class RutaSuministro:
    """
    Sistema de transporte con disrupciones aleatorias.

    Modela ruta Neuquen/Cabo Negro -> Coyhaique con bloqueos aleatorios.
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
        """Verifica si ruta esta operativa. Desbloquea automaticamente si corresponde."""
        if self.bloqueada and self.env.now >= self.tiempoDesbloqueo:
            self.bloqueada = False
            logger.info(f"Dia {self.env.now:.0f}: Ruta desbloqueada")
        return not self.bloqueada

    def bloquearPorDisrupcion(self, duracionDias: float) -> None:
        """Bloquea ruta por disrupcion durante duracionDias."""
        self.bloqueada = True
        self.tiempoDesbloqueo = self.env.now + duracionDias
        self.disrupcionesTotales += 1
        self.diasBloqueadosAcumulados += duracionDias

        logger.warning(
            f"Dia {self.env.now:.0f}: Disrupcion #{self.disrupcionesTotales} - "
            f"Ruta bloqueada por {duracionDias:.1f} dias (hasta dia {self.tiempoDesbloqueo:.0f})"
        )

    def calcularLeadTime(self) -> float:
        """Calcula lead time efectivo: nominal + tiempo restante de disrupcion."""
        leadTimeBase = self.config.leadTimeNominalDias

        if self.bloqueada:
            tiempoRestante = max(0, self.tiempoDesbloqueo - self.env.now)
            return leadTimeBase + tiempoRestante

        return leadTimeBase
