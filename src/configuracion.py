"""
Configuracion del Sistema de Suministro de GLP.

Parametros calibrados con datos CNE 2024 para Region de Aysen.

Author: Carlos Subiabre
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ConfiguracionSimulacion:
    """
    Parametros del modelo de simulacion.

    Valores por defecto representan escenario "status quo" (capacidad 431 TM).

    Nota critica: ROP debe cumplir ROP >= demanda_durante_LT + stock_seguridad
    ROP = 52.5 TM/dia × 6 dias + 1.5 dias SS = 394 TM
    """

    # Parametros de capacidad
    capacidadHubTm: float = 431.0
    puntoReordenTm: float = 394.0
    cantidadPedidoTm: float = 230.0
    inventarioInicialTm: float = 258.6

    # Parametros de demanda
    demandaBaseDiariaTm: float = 52.5
    variabilidadDemanda: float = 0.15
    amplitudEstacional: float = 0.30
    diaPicoInvernal: int = 200

    # Parametros operacionales
    leadTimeNominalDias: float = 6.0

    # Parametros de riesgo (disrupciones)
    tasaDisrupcionesAnual: float = 4.0
    duracionDisrupcionMinDias: float = 3.0
    duracionDisrupcionModeDias: float = 7.0
    duracionDisrupcionMaxDias: float = 21.0

    # Control de simulacion
    duracionSimulacionDias: int = 365
    semillaAleatoria: int = 42
    usarEstacionalidad: bool = True

    def validar(self) -> None:
        """Valida consistencia de parametros. Lanza AssertionError si hay errores."""
        assert self.capacidadHubTm > 0, \
            "Capacidad debe ser positiva"

        assert self.puntoReordenTm < self.capacidadHubTm, \
            f"Punto de reorden ({self.puntoReordenTm}) debe ser menor que capacidad ({self.capacidadHubTm})"

        assert self.cantidadPedidoTm > 0, \
            "Cantidad de pedido debe ser positiva"

        assert self.inventarioInicialTm <= self.capacidadHubTm, \
            f"Inventario inicial ({self.inventarioInicialTm}) no puede exceder capacidad ({self.capacidadHubTm})"

        assert self.demandaBaseDiariaTm > 0, \
            "Demanda base debe ser positiva"

        assert 0 <= self.variabilidadDemanda < 1, \
            "Variabilidad debe estar en [0,1)"

        assert 0 <= self.amplitudEstacional < 1, \
            "Amplitud estacional debe estar en [0,1)"

        assert self.leadTimeNominalDias > 0, \
            "Lead time debe ser positivo"

        assert self.tasaDisrupcionesAnual >= 0, \
            "Tasa de disrupciones debe ser no negativa"

        assert self.duracionDisrupcionMinDias >= 0, \
            "Duracion minima debe ser no negativa"

        assert self.duracionDisrupcionMinDias <= self.duracionDisrupcionModeDias <= self.duracionDisrupcionMaxDias, \
            f"Duraciones deben cumplir: min ({self.duracionDisrupcionMinDias}) <= " \
            f"mode ({self.duracionDisrupcionModeDias}) <= max ({self.duracionDisrupcionMaxDias})"

        assert self.duracionSimulacionDias > 0, \
            "Duracion de simulacion debe ser positiva"

        # Validacion de consistencia de politica (Q,R)
        demandaDuranteLeadTime = self.demandaBaseDiariaTm * self.leadTimeNominalDias

        if self.puntoReordenTm < demandaDuranteLeadTime:
            logger.warning(
                f"Punto de reorden ({self.puntoReordenTm:.1f} TM) es menor que la demanda "
                f"durante lead time ({demandaDuranteLeadTime:.1f} TM). "
                f"Esto puede causar quiebres de stock sistematicos."
            )

    def calcularAutonomiaTeoriacaDias(self) -> float:
        """Calcula autonomia teorica: capacidad / demanda_diaria."""
        return self.capacidadHubTm / self.demandaBaseDiariaTm

    def calcularStockSeguridadDias(self) -> float:
        """Calcula dias de stock de seguridad: (ROP - demanda_durante_LT) / demanda_diaria."""
        demandaDuranteLeadTime = self.demandaBaseDiariaTm * self.leadTimeNominalDias
        stockSeguridad = self.puntoReordenTm - demandaDuranteLeadTime
        return stockSeguridad / self.demandaBaseDiariaTm

    def __str__(self) -> str:
        """Representacion legible de parametros clave."""
        autonomia = self.calcularAutonomiaTeoriacaDias()
        ss_dias = self.calcularStockSeguridadDias()

        return (
            f"ConfiguracionSimulacion(\n"
            f"  Capacidad: {self.capacidadHubTm:.0f} TM\n"
            f"  Autonomia teorica: {autonomia:.1f} dias\n"
            f"  Punto reorden (R): {self.puntoReordenTm:.0f} TM ({self.puntoReordenTm/self.capacidadHubTm*100:.1f}%)\n"
            f"  Cantidad pedido (Q): {self.cantidadPedidoTm:.0f} TM\n"
            f"  Stock seguridad: {ss_dias:.1f} dias\n"
            f"  Lead time: {self.leadTimeNominalDias:.0f} dias\n"
            f"  Tasa disrupciones: {self.tasaDisrupcionesAnual:.1f} eventos/ano\n"
            f"  Duracion disrupcion: [{self.duracionDisrupcionMinDias:.0f}, "
            f"{self.duracionDisrupcionModeDias:.0f}, {self.duracionDisrupcionMaxDias:.0f}] dias\n"
            f")"
        )
