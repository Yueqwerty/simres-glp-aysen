"""
Gestores de transporte para la cadena de suministro de GLP en Aysén.
Incluye transporte primario (desde fuentes a hub) y distribución regional (desde hub a clientes).
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Generator, List

import simpy
from numpy.random import Generator as NPGenerator

from .entidades_aysen import (
    CamionCisterna, ClientesFinales, FuenteSuministro, HubCoyhaique, RedCDE
)

logger = logging.getLogger(__name__)


class GestorTransportePrimario:
    """
    Gestiona el transporte primario desde fuentes de suministro hasta Hub Coyhaique.
    Implementa política de reabastecimiento basada en nivel de inventario.
    """

    def __init__(
        self,
        env: simpy.Environment,
        rng: NPGenerator,
        fuentes: Dict[str, FuenteSuministro],
        hub: HubCoyhaique,
        config: Dict[str, Any]
    ):
        self.env = env
        self.rng = rng
        self.fuentes = fuentes
        self.hub = hub
        self.config = config

        # Flota de camiones cisterna
        self.flota: Dict[str, CamionCisterna] = {}
        self._crear_flota()

        # Política de reabastecimiento
        self.nivel_activacion_tm = config.get('nivel_activacion_tm', 200)  # Cuando pedir camiones
        self.nivel_objetivo_tm = config.get('nivel_objetivo_tm', 350)  # Nivel objetivo

        # Métricas
        self.metricas = {
            'viajes_totales': 0,
            'volumen_total_transportado_tm': 0.0,
            'camiones_en_ruta': 0,
            'solicitudes_viaje': 0
        }

        # Iniciar proceso de monitoreo
        self.proceso = env.process(self.run())

        logger.info(
            f"Gestor Transporte Primario inicializado: {len(self.flota)} camiones, "
            f"nivel activación={self.nivel_activacion_tm} TM"
        )

    def _crear_flota(self) -> None:
        """Crea la flota de camiones cisterna."""
        flota_config = self.config.get('flota', {})
        num_camiones = flota_config.get('num_camiones', 10)

        for i in range(num_camiones):
            camion_id = f"cisterna_{i+1:03d}"

            # Asignar fuente (alternar entre disponibles)
            fuentes_disponibles = list(self.fuentes.keys())
            fuente_asignada = fuentes_disponibles[i % len(fuentes_disponibles)]

            camion_config = {
                'capacidad_tm': flota_config.get('capacidad_tm', 22),
                'fuente_asignada': fuente_asignada,
                'tiempo_viaje_temporada_calida_dias': flota_config.get(
                    'tiempo_viaje_temporada_calida_dias', (5.5, 6.0)
                ),
                'tiempo_viaje_temporada_fria_dias': flota_config.get(
                    'tiempo_viaje_temporada_fria_dias', (5.7, 7.5)
                )
            }

            self.flota[camion_id] = CamionCisterna(
                env=self.env,
                camion_id=camion_id,
                rng=self.rng,
                config=camion_config
            )

    def run(self) -> Generator:
        """Proceso principal: monitorea inventario y despacha camiones."""
        while True:
            # Esperar un día antes de verificar
            yield self.env.timeout(1.0)  # 1 día

            nivel_actual = self.hub.inventario_granel.level

            # Verificar si necesita reabastecimiento
            if nivel_actual < self.nivel_activacion_tm:
                # Calcular cuánto GLP necesitamos
                deficit_tm = self.nivel_objetivo_tm - nivel_actual

                # Calcular cuántos camiones necesitamos
                capacidad_camion = self.config.get('flota', {}).get('capacidad_tm', 22)
                num_camiones_necesarios = int(deficit_tm / capacidad_camion) + 1

                # Despachar camiones disponibles
                self._despachar_camiones_disponibles(num_camiones_necesarios)

    def _despachar_camiones_disponibles(self, num_camiones: int) -> None:
        """Despacha camiones disponibles para reabastecimiento."""
        camiones_despachados = 0

        for camion in self.flota.values():
            if camion.estado.value == "inactivo" and camiones_despachados < num_camiones:
                # Obtener fuente asignada
                fuente = self.fuentes.get(camion.fuente_asignada)

                if fuente:
                    # Iniciar viaje
                    self.env.process(self._gestionar_viaje_camion(camion, fuente))
                    camiones_despachados += 1
                    self.metricas['solicitudes_viaje'] += 1

        if camiones_despachados > 0:
            logger.info(
                f"Despachados {camiones_despachados} camiones. "
                f"Inventario hub: {self.hub.inventario_granel.level:.2f} TM"
            )

    def _gestionar_viaje_camion(
        self,
        camion: CamionCisterna,
        fuente: FuenteSuministro
    ) -> Generator:
        """Gestiona un viaje completo de un camión."""
        self.metricas['camiones_en_ruta'] += 1

        try:
            yield self.env.process(camion.realizar_viaje(fuente, self.hub))

            self.metricas['viajes_totales'] += 1
            self.metricas['volumen_total_transportado_tm'] += camion.capacidad_tm

        except Exception as e:
            logger.error(f"Error en viaje de camión {camion.camion_id}: {e}")

        finally:
            self.metricas['camiones_en_ruta'] -= 1


class GestorDistribucionRegional:
    """
    Gestiona la distribución regional desde Hub Coyhaique hacia clientes finales.
    Incluye dos sub-cadenas: granel y envasado.
    """

    def __init__(
        self,
        env: simpy.Environment,
        rng: NPGenerator,
        hub: HubCoyhaique,
        red_cdes: RedCDE,
        clientes: ClientesFinales,
        config: Dict[str, Any]
    ):
        self.env = env
        self.rng = rng
        self.hub = hub
        self.red_cdes = red_cdes
        self.clientes = clientes
        self.config = config

        # Flotas
        self.num_camiones_granel = config.get('num_camiones_granel', 10)
        self.num_camiones_jaula = config.get('num_camiones_jaula', 12)

        # Capacidades de camiones
        self.capacidad_camion_granel_tm = config.get('capacidad_camion_granel_tm', 8)  # Promedio 3.5-12
        self.capacidad_camion_jaula_tm = config.get('capacidad_camion_jaula_tm', 5)

        # Políticas de reabastecimiento
        self.umbral_reabasto_granel = config.get('umbral_reabasto_granel_pct', 0.3)  # 30%
        self.umbral_reabasto_envasado = config.get('umbral_reabasto_envasado_pct', 0.3)

        # Métricas
        self.metricas = {
            'despachos_granel': 0,
            'despachos_envasado': 0,
            'volumen_granel_despachado_tm': 0.0,
            'volumen_envasado_despachado_tm': 0.0,
            'reabastecimientos_cdes': 0,
            'volumen_envasado_procesado_tm': 0.0
        }

        # Iniciar procesos
        self.proceso_granel = env.process(self.run_distribucion_granel())
        self.proceso_envasado = env.process(self.run_distribucion_envasado())
        self.proceso_envasado_hub = env.process(self.run_procesamiento_envasado())

        logger.info(
            f"Gestor Distribución Regional inicializado: "
            f"{self.num_camiones_granel} granel, {self.num_camiones_jaula} jaula"
        )

    def run_distribucion_granel(self) -> Generator:
        """Proceso de distribución a granel (clientes con tanques fijos) - Lógica PULL."""
        while True:
            # Verificar diariamente
            yield self.env.timeout(1.0)

            # Calcular déficit basado en demanda esperada
            nivel_clientes = self.clientes.inventario_granel.level
            capacidad_clientes = self.clientes.inventario_granel.capacity

            # Demanda diaria promedio (estimación conservadora)
            demanda_diaria_estimada = self.clientes.demanda_diaria_base_granel_tm * 1.4  # Factor estacional máximo

            # Días de cobertura actual
            dias_cobertura = nivel_clientes / demanda_diaria_estimada if demanda_diaria_estimada > 0 else float('inf')

            # Reabastecer si cobertura < 7 días (objetivo: mantener ~14 días)
            dias_objetivo = 14
            dias_minimos = 7

            if dias_cobertura < dias_minimos:
                # Calcular volumen necesario para llegar a días_objetivo
                volumen_necesario = demanda_diaria_estimada * dias_objetivo - nivel_clientes

                # Limitar al espacio disponible
                espacio_disponible = capacidad_clientes - nivel_clientes
                volumen_a_enviar = min(volumen_necesario, espacio_disponible)

                if volumen_a_enviar > 5:  # Mínimo económico de 5 TM
                    # Despachar desde hub
                    volumen_despachado_hub = yield self.env.process(
                        self.hub.despachar_granel(volumen_a_enviar)
                    )

                    # Reabastecer clientes
                    if volumen_despachado_hub > 0:
                        yield self.env.process(
                            self.clientes.reabastecer_granel(volumen_despachado_hub)
                        )

                        self.metricas['despachos_granel'] += 1
                        self.metricas['volumen_granel_despachado_tm'] += volumen_despachado_hub

                        logger.debug(
                            f"Distribución granel: {volumen_despachado_hub:.2f} TM a clientes "
                            f"(cobertura: {dias_cobertura:.1f} días)"
                        )

    def run_distribucion_envasado(self) -> Generator:
        """Proceso de distribución envasado (CDEs y hogares) - Lógica PULL."""
        while True:
            # Verificar diariamente
            yield self.env.timeout(1.0)

            # PASO 1: CDEs -> Clientes finales (primero satisfacer demanda downstream)
            nivel_hogares = self.clientes.inventario_envasado_hogares.level
            capacidad_hogares = self.clientes.inventario_envasado_hogares.capacity

            # Demanda diaria estimada envasado (con factor estacional)
            demanda_diaria_envasado = self.clientes.demanda_diaria_base_envasado_tm * 1.4

            # Días de cobertura en hogares
            dias_cobertura_hogares = nivel_hogares / demanda_diaria_envasado if demanda_diaria_envasado > 0 else float('inf')

            # Reabastecer hogares si cobertura < 5 días (objetivo: 10 días)
            if dias_cobertura_hogares < 5:
                volumen_necesario_hogares = demanda_diaria_envasado * 10 - nivel_hogares
                espacio_disponible_hogares = capacidad_hogares - nivel_hogares
                volumen_a_enviar_hogares = min(volumen_necesario_hogares, espacio_disponible_hogares)

                if volumen_a_enviar_hogares > 5:  # Mínimo económico
                    volumen_despachado_cdes = yield self.env.process(
                        self.red_cdes.despachar_a_clientes(volumen_a_enviar_hogares)
                    )

                    if volumen_despachado_cdes > 0:
                        yield self.env.process(
                            self.clientes.reabastecer_envasado(volumen_despachado_cdes)
                        )

                        self.metricas['despachos_envasado'] += 1
                        self.metricas['volumen_envasado_despachado_tm'] += volumen_despachado_cdes

                        logger.debug(
                            f"Distribución envasado: {volumen_despachado_cdes:.2f} TM a hogares "
                            f"(cobertura: {dias_cobertura_hogares:.1f} días)"
                        )

            # PASO 2: Hub -> CDEs (reponer lo que CDEs necesitan para atender demanda)
            nivel_cdes = self.red_cdes.inventario.level
            capacidad_cdes = self.red_cdes.inventario.capacity

            # Días de cobertura en CDEs
            dias_cobertura_cdes = nivel_cdes / demanda_diaria_envasado if demanda_diaria_envasado > 0 else float('inf')

            # Reabastecer CDEs si cobertura < 7 días (objetivo: 14 días)
            if dias_cobertura_cdes < 7:
                volumen_necesario_cdes = demanda_diaria_envasado * 14 - nivel_cdes
                espacio_disponible_cdes = capacidad_cdes - nivel_cdes
                volumen_a_enviar_cdes = min(volumen_necesario_cdes, espacio_disponible_cdes)

                if volumen_a_enviar_cdes > 5:  # Mínimo económico
                    volumen_despachado_hub = yield self.env.process(
                        self.hub.despachar_envasado(volumen_a_enviar_cdes)
                    )

                    if volumen_despachado_hub > 0:
                        yield self.env.process(
                            self.red_cdes.recibir_desde_hub(volumen_despachado_hub)
                        )

                        self.metricas['reabastecimientos_cdes'] += 1

                        logger.debug(
                            f"Reabastecimiento CDEs: {volumen_despachado_hub:.2f} TM "
                            f"(cobertura: {dias_cobertura_cdes:.1f} días)"
                        )

    def run_procesamiento_envasado(self) -> Generator:
        """Proceso de envasado en el hub (granel -> envasado) - Lógica PULL."""
        while True:
            # Procesar diariamente
            yield self.env.timeout(1.0)

            # Verificar demanda downstream para determinar cuánto procesar
            nivel_envasado_hub = self.hub.inventario_envasado.level
            capacidad_envasado_hub = self.hub.inventario_envasado.capacity

            # Demanda diaria estimada envasado total (con factor estacional)
            demanda_diaria_envasado = self.clientes.demanda_diaria_base_envasado_tm * 1.4

            # Días de cobertura en inventario envasado del Hub
            dias_cobertura_hub = nivel_envasado_hub / demanda_diaria_envasado if demanda_diaria_envasado > 0 else float('inf')

            # Procesar si cobertura < 10 días (objetivo: mantener 21 días = 3 semanas)
            dias_objetivo_hub = 21
            dias_minimos_hub = 10

            if dias_cobertura_hub < dias_minimos_hub:
                # Calcular volumen a procesar basado en demanda
                volumen_necesario = demanda_diaria_envasado * dias_objetivo_hub - nivel_envasado_hub

                # Limitar por espacio disponible en inventario envasado
                espacio_disponible = capacidad_envasado_hub - nivel_envasado_hub
                volumen_a_procesar = min(volumen_necesario, espacio_disponible)

                if volumen_a_procesar > 5:  # Mínimo económico de procesamiento
                    volumen_procesado = yield self.env.process(
                        self.hub.procesar_envasado(volumen_a_procesar)
                    )

                    if volumen_procesado > 0:
                        self.metricas['volumen_envasado_procesado_tm'] += volumen_procesado

                        logger.debug(
                            f"Procesamiento envasado: {volumen_procesado:.2f} TM "
                            f"(cobertura: {dias_cobertura_hub:.1f} días)"
                        )
