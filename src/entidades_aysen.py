"""
Entidades específicas para el modelo SCOR de la cadena de suministro de GLP en Aysén.
Basado en el informe "GLP Y COMBUSTIBLES LIQUIDOS Vulnerabilidad de la cadena de suministro".
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Generator, List, Optional

import simpy
from numpy.random import Generator as NPGenerator

logger = logging.getLogger(__name__)


class EstadoCamion(Enum):
    """Estados posibles de un camión cisterna."""
    INACTIVO = "inactivo"
    CARGANDO = "cargando"
    EN_TRANSITO = "en_transito"
    DESCARGANDO = "descargando"
    EN_MANTENIMIENTO = "en_mantenimiento"


@dataclass
class Viaje:
    """Estructura para registrar un viaje de camión."""
    camion_id: str
    origen: str
    destino: str
    volumen_tm: float
    tiempo_inicio: float
    tiempo_fin: Optional[float] = None
    exitoso: bool = False


class FuenteSuministro:
    """
    Fuente de suministro de GLP (ENAP Cabo Negro o proveedores en Neuquén).
    Capacidad ilimitada para la escala de Aysén.
    """

    def __init__(self, env: simpy.Environment, fuente_id: str, pais: str, config: Dict[str, Any]):
        self.env = env
        self.fuente_id = fuente_id
        self.pais = pais
        self.config = config
        self.operativa = True

        # Métricas
        self.metricas = {
            'camiones_despachados': 0,
            'volumen_total_despachado_tm': 0.0,
            'tiempo_total_operativo': 0.0
        }

        logger.info(f"Fuente {fuente_id} ({pais}) inicializada")

    def despachar_camion(self, volumen_tm: float) -> bool:
        """Despacha un camión con GLP."""
        if not self.operativa:
            logger.warning(f"Fuente {self.fuente_id} no operativa, no puede despachar")
            return False

        self.metricas['camiones_despachados'] += 1
        self.metricas['volumen_total_despachado_tm'] += volumen_tm

        logger.debug(f"Fuente {self.fuente_id} despachó {volumen_tm} TM")
        return True

    def interrumpir(self) -> None:
        """Marca la fuente como no operativa."""
        self.operativa = False
        logger.warning(f"Fuente {self.fuente_id} interrumpida")

    def restaurar(self) -> None:
        """Restaura la operación de la fuente."""
        self.operativa = True
        logger.info(f"Fuente {self.fuente_id} restaurada")


class HubCoyhaique:
    """
    Hub central de Coyhaique que agrupa las 3 plantas (Abastible, Gasco, Lipigas).
    Maneja inventario de granel y envasado.
    """

    def __init__(self, env: simpy.Environment, hub_id: str, config: Dict[str, Any]):
        self.env = env
        self.hub_id = hub_id
        self.config = config

        # Capacidades
        self.capacidad_granel_tm = config.get('capacidad_granel_tm', 431)
        self.capacidad_envasado_tm = config.get('capacidad_envasado_tm', 140)

        # Inventarios (SimPy Containers)
        self.inventario_granel = simpy.Container(
            env,
            capacity=self.capacidad_granel_tm,
            init=config.get('inventario_inicial_granel_tm', 215)  # 50% inicial
        )

        self.inventario_envasado = simpy.Container(
            env,
            capacity=self.capacidad_envasado_tm,
            init=config.get('inventario_inicial_envasado_tm', 70)  # 50% inicial
        )

        # Métricas
        self.metricas = {
            'camiones_recibidos': 0,
            'volumen_total_recibido_tm': 0.0,
            'despachos_granel_tm': 0.0,
            'despachos_envasado_tm': 0.0,
            'volumen_envasado_tm': 0.0,
            'quiebres_stock_granel': 0,
            'quiebres_stock_envasado': 0,
            'nivel_minimo_granel_tm': config.get('inventario_inicial_granel_tm', 215),
            'nivel_minimo_envasado_tm': config.get('inventario_inicial_envasado_tm', 70)
        }

        logger.info(f"Hub {hub_id} inicializado: {self.capacidad_granel_tm} TM granel, {self.capacidad_envasado_tm} TM envasado")

    def recibir_camion(self, volumen_tm: float) -> Generator:
        """Recibe un camión con GLP granel."""
        espacio_disponible = self.inventario_granel.capacity - self.inventario_granel.level
        volumen_real = min(volumen_tm, espacio_disponible)

        if volumen_real < volumen_tm:
            logger.warning(
                f"Hub {self.hub_id}: Solo se pueden recibir {volumen_real:.2f} TM de {volumen_tm:.2f} TM"
            )

        if volumen_real > 0:
            yield self.inventario_granel.put(volumen_real)
            self.metricas['camiones_recibidos'] += 1
            self.metricas['volumen_total_recibido_tm'] += volumen_real

            logger.debug(
                f"Hub {self.hub_id} recibió {volumen_real:.2f} TM. "
                f"Inventario granel: {self.inventario_granel.level:.2f} TM"
            )

        return volumen_real

    def despachar_granel(self, volumen_tm: float) -> Generator:
        """Despacha GLP a granel (para clientes con tanques fijos)."""
        volumen_disponible = min(volumen_tm, self.inventario_granel.level)

        if volumen_disponible > 0:
            yield self.inventario_granel.get(volumen_disponible)
            self.metricas['despachos_granel_tm'] += volumen_disponible

            # Actualizar nivel mínimo
            if self.inventario_granel.level < self.metricas['nivel_minimo_granel_tm']:
                self.metricas['nivel_minimo_granel_tm'] = self.inventario_granel.level

            logger.debug(f"Hub {self.hub_id} despachó {volumen_disponible:.2f} TM granel")
        else:
            self.metricas['quiebres_stock_granel'] += 1
            logger.warning(f"Hub {self.hub_id}: Quiebre de stock granel")

        return volumen_disponible

    def despachar_envasado(self, volumen_tm: float) -> Generator:
        """Despacha GLP envasado (para CDEs)."""
        volumen_disponible = min(volumen_tm, self.inventario_envasado.level)

        if volumen_disponible > 0:
            yield self.inventario_envasado.get(volumen_disponible)
            self.metricas['despachos_envasado_tm'] += volumen_disponible

            # Actualizar nivel mínimo
            if self.inventario_envasado.level < self.metricas['nivel_minimo_envasado_tm']:
                self.metricas['nivel_minimo_envasado_tm'] = self.inventario_envasado.level

            logger.debug(f"Hub {self.hub_id} despachó {volumen_disponible:.2f} TM envasado")
        else:
            self.metricas['quiebres_stock_envasado'] += 1
            logger.warning(f"Hub {self.hub_id}: Quiebre de stock envasado")

        return volumen_disponible

    def procesar_envasado(self, volumen_tm: float) -> Generator:
        """Procesa GLP de granel a envasado."""
        # Verificar disponibilidad en granel
        volumen_granel_disponible = min(volumen_tm, self.inventario_granel.level)

        # Verificar espacio en envasado
        espacio_envasado = self.inventario_envasado.capacity - self.inventario_envasado.level
        volumen_real = min(volumen_granel_disponible, espacio_envasado)

        if volumen_real > 0:
            # Sacar de granel
            yield self.inventario_granel.get(volumen_real)

            # Agregar a envasado
            yield self.inventario_envasado.put(volumen_real)

            self.metricas['volumen_envasado_tm'] += volumen_real

            logger.debug(f"Hub {self.hub_id} procesó {volumen_real:.2f} TM granel -> envasado")

        return volumen_real


class RedCDE:
    """
    Red de Centros de Distribución Envasado (46 CDEs en 7 comunas).
    Agregado como un único nodo para simplicidad.
    """

    def __init__(self, env: simpy.Environment, red_id: str, config: Dict[str, Any]):
        self.env = env
        self.red_id = red_id
        self.config = config

        # Capacidad total de la red
        self.capacidad_total_tm = config.get('capacidad_total_tm', 161.3)

        # Inventario
        self.inventario = simpy.Container(
            env,
            capacity=self.capacidad_total_tm,
            init=config.get('inventario_inicial_tm', 80)  # 50% inicial
        )

        # Métricas
        self.metricas = {
            'reabastecimientos_totales': 0,
            'volumen_total_recibido_tm': 0.0,
            'despachos_clientes_tm': 0.0,
            'quiebres_stock': 0,
            'nivel_minimo_tm': config.get('inventario_inicial_tm', 80)
        }

        logger.info(f"Red {red_id} inicializada: {self.capacidad_total_tm} TM capacidad")

    def recibir_desde_hub(self, volumen_tm: float) -> Generator:
        """Recibe GLP envasado desde el hub."""
        espacio_disponible = self.inventario.capacity - self.inventario.level
        volumen_real = min(volumen_tm, espacio_disponible)

        if volumen_real > 0:
            yield self.inventario.put(volumen_real)
            self.metricas['reabastecimientos_totales'] += 1
            self.metricas['volumen_total_recibido_tm'] += volumen_real

            logger.debug(f"Red {self.red_id} recibió {volumen_real:.2f} TM desde hub")

        return volumen_real

    def despachar_a_clientes(self, volumen_tm: float) -> Generator:
        """Despacha GLP envasado a clientes finales."""
        volumen_disponible = min(volumen_tm, self.inventario.level)

        if volumen_disponible > 0:
            yield self.inventario.get(volumen_disponible)
            self.metricas['despachos_clientes_tm'] += volumen_disponible

            # Actualizar nivel mínimo
            if self.inventario.level < self.metricas['nivel_minimo_tm']:
                self.metricas['nivel_minimo_tm'] = self.inventario.level

            logger.debug(f"Red {self.red_id} despachó {volumen_disponible:.2f} TM a clientes")
        else:
            self.metricas['quiebres_stock'] += 1

        return volumen_disponible


class ClientesFinales:
    """
    Clientes finales que representan el inventario distribuido en la región.
    Incluye clientes granel (tanques fijos) y envasado (cilindros en hogares).
    """

    def __init__(self, env: simpy.Environment, clientes_id: str, config: Dict[str, Any]):
        self.env = env
        self.clientes_id = clientes_id
        self.config = config

        # Capacidades
        self.capacidad_granel_tm = config.get('capacidad_granel_tm', 911)
        self.capacidad_envasado_hogares_tm = config.get('capacidad_envasado_hogares_tm', 660)

        # Inventarios
        self.inventario_granel = simpy.Container(
            env,
            capacity=self.capacidad_granel_tm,
            init=config.get('inventario_inicial_granel_tm', 455)  # 50% inicial
        )

        self.inventario_envasado_hogares = simpy.Container(
            env,
            capacity=self.capacidad_envasado_hogares_tm,
            init=config.get('inventario_inicial_envasado_tm', 330)  # 50% inicial
        )

        # Demanda anual y cálculo de demanda diaria
        self.demanda_anual_granel_tm = config.get('demanda_anual_granel_tm', 7270)
        self.demanda_anual_envasado_tm = config.get('demanda_anual_envasado_tm', 7791)

        self.demanda_diaria_base_granel_tm = self.demanda_anual_granel_tm / 365.0
        self.demanda_diaria_base_envasado_tm = self.demanda_anual_envasado_tm / 365.0

        # Métricas
        self.metricas = {
            'demanda_total_granel_tm': 0.0,
            'demanda_total_envasado_tm': 0.0,
            'demanda_satisfecha_granel_tm': 0.0,
            'demanda_satisfecha_envasado_tm': 0.0,
            'eventos_desabastecimiento_granel': 0,
            'eventos_desabastecimiento_envasado': 0
        }

        logger.info(
            f"Clientes {clientes_id} inicializados: "
            f"Demanda diaria granel={self.demanda_diaria_base_granel_tm:.2f} TM, "
            f"envasado={self.demanda_diaria_base_envasado_tm:.2f} TM"
        )

    def consumir_granel(self, demanda_tm: float) -> Generator:
        """Consume GLP a granel."""
        volumen_consumido = min(demanda_tm, self.inventario_granel.level)

        self.metricas['demanda_total_granel_tm'] += demanda_tm

        if volumen_consumido > 0:
            yield self.inventario_granel.get(volumen_consumido)
            self.metricas['demanda_satisfecha_granel_tm'] += volumen_consumido

        if volumen_consumido < demanda_tm:
            deficit = demanda_tm - volumen_consumido
            self.metricas['eventos_desabastecimiento_granel'] += 1
            logger.warning(f"Clientes: Desabastecimiento granel de {deficit:.2f} TM")

        return volumen_consumido

    def consumir_envasado(self, demanda_tm: float) -> Generator:
        """Consume GLP envasado."""
        volumen_consumido = min(demanda_tm, self.inventario_envasado_hogares.level)

        self.metricas['demanda_total_envasado_tm'] += demanda_tm

        if volumen_consumido > 0:
            yield self.inventario_envasado_hogares.get(volumen_consumido)
            self.metricas['demanda_satisfecha_envasado_tm'] += volumen_consumido

        if volumen_consumido < demanda_tm:
            deficit = demanda_tm - volumen_consumido
            self.metricas['eventos_desabastecimiento_envasado'] += 1
            logger.warning(f"Clientes: Desabastecimiento envasado de {deficit:.2f} TM")

        return volumen_consumido

    def reabastecer_granel(self, volumen_tm: float) -> Generator:
        """Reabastecer inventario granel desde hub."""
        espacio_disponible = self.inventario_granel.capacity - self.inventario_granel.level
        volumen_real = min(volumen_tm, espacio_disponible)

        if volumen_real > 0:
            yield self.inventario_granel.put(volumen_real)
            logger.debug(f"Clientes reabastecidos granel: {volumen_real:.2f} TM")

        return volumen_real

    def reabastecer_envasado(self, volumen_tm: float) -> Generator:
        """Reabastecer inventario envasado desde red CDEs."""
        espacio_disponible = self.inventario_envasado_hogares.capacity - self.inventario_envasado_hogares.level
        volumen_real = min(volumen_tm, espacio_disponible)

        if volumen_real > 0:
            yield self.inventario_envasado_hogares.put(volumen_real)
            logger.debug(f"Clientes reabastecidos envasado: {volumen_real:.2f} TM")

        return volumen_real


class CamionCisterna:
    """
    Camión cisterna para transporte primario desde fuentes a Hub Coyhaique.
    Capacidad: 22 TM, tiempo de viaje variable según estación.
    """

    def __init__(
        self,
        env: simpy.Environment,
        camion_id: str,
        rng: NPGenerator,
        config: Dict[str, Any]
    ):
        self.env = env
        self.camion_id = camion_id
        self.rng = rng
        self.config = config

        # Configuración
        self.capacidad_tm = config.get('capacidad_tm', 22)
        self.fuente_asignada = config.get('fuente_asignada', 'cabo_negro')

        # Tiempos de viaje según estación (en días)
        self.tiempo_viaje_temporada_calida_dias = config.get('tiempo_viaje_temporada_calida_dias', (5.5, 6.0))
        self.tiempo_viaje_temporada_fria_dias = config.get('tiempo_viaje_temporada_fria_dias', (5.7, 7.5))

        # Estado
        self.estado = EstadoCamion.INACTIVO
        self.carga_actual_tm = 0.0

        # Métricas
        self.metricas = {
            'viajes_completados': 0,
            'volumen_total_transportado_tm': 0.0,
            'tiempo_total_viaje_dias': 0.0,
            'tiempo_total_inactivo_dias': 0.0
        }

        # Historial de viajes
        self.viajes: List[Viaje] = []

        logger.info(f"Camión {camion_id} inicializado: {self.capacidad_tm} TM, fuente={self.fuente_asignada}")

    def calcular_tiempo_viaje(self) -> float:
        """Calcula tiempo de viaje (ida y vuelta) según estación."""
        # Determinar estación según día del año
        dia_del_año = (self.env.now % 365)

        # Temporada fría: abril a septiembre (días 90-273)
        if 90 <= dia_del_año <= 273:
            tiempo_min, tiempo_max = self.tiempo_viaje_temporada_fria_dias
        else:
            tiempo_min, tiempo_max = self.tiempo_viaje_temporada_calida_dias

        # Tiempo aleatorio dentro del rango
        return self.rng.uniform(tiempo_min, tiempo_max)

    def realizar_viaje(self, fuente: FuenteSuministro, hub: HubCoyhaique) -> Generator:
        """Realiza un viaje completo desde fuente hasta hub."""
        # Registrar inicio de viaje
        viaje = Viaje(
            camion_id=self.camion_id,
            origen=fuente.fuente_id,
            destino=hub.hub_id,
            volumen_tm=self.capacidad_tm,
            tiempo_inicio=self.env.now
        )

        # Cargar
        self.estado = EstadoCamion.CARGANDO
        if not fuente.despachar_camion(self.capacidad_tm):
            logger.warning(f"Camión {self.camion_id}: Fuente {fuente.fuente_id} no disponible")
            return

        self.carga_actual_tm = self.capacidad_tm
        yield self.env.timeout(0.1)  # Tiempo de carga (10% de un día)

        # Viaje
        self.estado = EstadoCamion.EN_TRANSITO
        tiempo_viaje = self.calcular_tiempo_viaje()
        yield self.env.timeout(tiempo_viaje)

        self.metricas['tiempo_total_viaje_dias'] += tiempo_viaje

        # Descargar
        self.estado = EstadoCamion.DESCARGANDO
        volumen_descargado = yield self.env.process(hub.recibir_camion(self.carga_actual_tm))

        # Finalizar viaje
        viaje.tiempo_fin = self.env.now
        viaje.exitoso = True
        self.viajes.append(viaje)

        self.carga_actual_tm = 0.0
        self.metricas['viajes_completados'] += 1
        self.metricas['volumen_total_transportado_tm'] += volumen_descargado

        self.estado = EstadoCamion.INACTIVO

        logger.info(
            f"Camión {self.camion_id} completó viaje {self.metricas['viajes_completados']}: "
            f"{volumen_descargado:.2f} TM en {tiempo_viaje:.2f} días"
        )
