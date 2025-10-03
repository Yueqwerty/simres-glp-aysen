"""
Modelo principal de simulación para la cadena de suministro de GLP en Aysén.
Implementa simulación basada en eventos discretos con paso de tiempo diario.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Generator

import simpy
from numpy.random import Generator as NPGenerator

from .entidades_aysen import ClientesFinales, FuenteSuministro, HubCoyhaique, RedCDE
from .transporte import GestorDistribucionRegional, GestorTransportePrimario
from .monitores import MonitorSimulacion, RegistroDiario

logger = logging.getLogger(__name__)


class SimulacionAysen:
    """
    Simulación completa de la cadena de suministro de GLP en Aysén.
    Paso de tiempo: diario.
    Orden de operaciones por día:
    1. Calcular y consumir demanda diaria
    2. Intentar reabastecer clientes finales
    3. Intentar reabastecer CDEs
    4. Procesar llegadas de transporte primario
    5. Gestionar nuevos despachos primarios
    """

    def __init__(
        self,
        duracion_dias: float,
        rng: NPGenerator,
        config: Dict[str, Any]
    ):
        self.duracion_dias = duracion_dias
        self.rng = rng
        self.config = config

        # Entorno SimPy
        self.env = simpy.Environment()

        # Entidades del sistema (inicializadas en _inicializar_sistema)
        self.fuentes: Dict[str, FuenteSuministro] = {}
        self.hub: HubCoyhaique = None
        self.red_cdes: RedCDE = None
        self.clientes: ClientesFinales = None

        # Gestores de transporte
        self.gestor_transporte_primario: GestorTransportePrimario = None
        self.gestor_distribucion_regional: GestorDistribucionRegional = None

        # Proceso de generación de demanda
        self.proceso_demanda = None

        # Estado
        self.inicializada = False
        self.ejecutada = False

        # Métricas globales
        self.metricas_globales = {
            'dias_simulados': 0,
            'dias_con_desabastecimiento': 0,
            'tasa_satisfaccion_global': 0.0
        }

        # Monitor para series temporales
        self.monitor = MonitorSimulacion()

        # Variables para rastrear métricas del día anterior (para calcular incrementos)
        self.metricas_dia_anterior = {
            'volumen_hub_recibido': 0,
            'despachos_hub_granel': 0,
            'despachos_hub_envasado': 0,
            'volumen_envasado_procesado': 0,
            'volumen_cdes_recibido': 0,
            'viajes_completados': 0,
        }

        # Inicializar sistema
        self._inicializar_sistema()

    def _inicializar_sistema(self) -> None:
        """Inicializa todos los componentes del sistema."""
        logger.info("Inicializando sistema de simulación Aysén...")

        # 1. Crear fuentes de suministro
        self._crear_fuentes()

        # 2. Crear hub central
        self._crear_hub()

        # 3. Crear red de CDEs
        self._crear_red_cdes()

        # 4. Crear clientes finales
        self._crear_clientes()

        # 5. Crear gestor de transporte primario
        self._crear_gestor_transporte_primario()

        # 6. Crear gestor de distribución regional
        self._crear_gestor_distribucion_regional()

        # 7. Iniciar proceso de generación de demanda
        self.proceso_demanda = self.env.process(self._run_generacion_demanda())

        self.inicializada = True
        logger.info("Sistema inicializado correctamente")

    def _crear_fuentes(self) -> None:
        """Crea las fuentes de suministro."""
        fuentes_config = self.config.get('fuentes', {})

        # Fuente 1: ENAP Cabo Negro
        self.fuentes['cabo_negro'] = FuenteSuministro(
            env=self.env,
            fuente_id='cabo_negro',
            pais='Chile',
            config=fuentes_config.get('cabo_negro', {})
        )

        # Fuente 2: Neuquén
        self.fuentes['neuquen'] = FuenteSuministro(
            env=self.env,
            fuente_id='neuquen',
            pais='Argentina',
            config=fuentes_config.get('neuquen', {})
        )

        logger.info(f"Fuentes creadas: {list(self.fuentes.keys())}")

    def _crear_hub(self) -> None:
        """Crea el hub central de Coyhaique."""
        hub_config = self.config.get('hub_coyhaique', {})

        self.hub = HubCoyhaique(
            env=self.env,
            hub_id='hub_coyhaique',
            config=hub_config
        )

        logger.info("Hub Coyhaique creado")

    def _crear_red_cdes(self) -> None:
        """Crea la red de Centros de Distribución Envasado."""
        red_cdes_config = self.config.get('red_cdes', {})

        self.red_cdes = RedCDE(
            env=self.env,
            red_id='red_cdes_aysen',
            config=red_cdes_config
        )

        logger.info("Red CDEs creada")

    def _crear_clientes(self) -> None:
        """Crea los clientes finales."""
        clientes_config = self.config.get('clientes_finales', {})

        self.clientes = ClientesFinales(
            env=self.env,
            clientes_id='clientes_aysen',
            config=clientes_config
        )

        logger.info("Clientes finales creados")

    def _crear_gestor_transporte_primario(self) -> None:
        """Crea el gestor de transporte primario."""
        transporte_primario_config = self.config.get('transporte_primario', {})

        self.gestor_transporte_primario = GestorTransportePrimario(
            env=self.env,
            rng=self.rng,
            fuentes=self.fuentes,
            hub=self.hub,
            config=transporte_primario_config
        )

        logger.info("Gestor Transporte Primario creado")

    def _crear_gestor_distribucion_regional(self) -> None:
        """Crea el gestor de distribución regional."""
        distribucion_regional_config = self.config.get('distribucion_regional', {})

        self.gestor_distribucion_regional = GestorDistribucionRegional(
            env=self.env,
            rng=self.rng,
            hub=self.hub,
            red_cdes=self.red_cdes,
            clientes=self.clientes,
            config=distribucion_regional_config
        )

        logger.info("Gestor Distribución Regional creado")

    def _run_generacion_demanda(self) -> Generator:
        """
        Proceso principal de generación de demanda diaria.
        Aplica factor de estacionalidad para simular variación invernal.
        """
        while True:
            # Esperar un día
            yield self.env.timeout(1.0)

            # Calcular factor estacional (mayor demanda en invierno austral)
            dia_del_año = self.env.now % 365

            # Factor estacional: pico en junio-agosto (días 150-240)
            import numpy as np
            factor_estacional = 1.0 + 0.4 * np.sin(
                2 * np.pi * (dia_del_año - 172) / 365.0
            )
            factor_estacional = max(0.6, factor_estacional)  # Mínimo 60% de demanda base

            # Agregar variabilidad diaria
            variabilidad = self.rng.normal(1.0, 0.1)  # ±10%
            factor_total = factor_estacional * variabilidad

            # Generar demanda granel
            demanda_granel_tm = self.clientes.demanda_diaria_base_granel_tm * factor_total

            # Generar demanda envasado
            demanda_envasado_tm = self.clientes.demanda_diaria_base_envasado_tm * factor_total

            # Consumir demanda (orden de operación #1)
            yield self.env.process(self.clientes.consumir_granel(demanda_granel_tm))
            yield self.env.process(self.clientes.consumir_envasado(demanda_envasado_tm))

            # Verificar desabastecimientos
            desabastecimiento_granel = self.clientes.metricas['eventos_desabastecimiento_granel'] > 0
            desabastecimiento_envasado = self.clientes.metricas['eventos_desabastecimiento_envasado'] > 0

            if desabastecimiento_granel or desabastecimiento_envasado:
                self.metricas_globales['dias_con_desabastecimiento'] += 1

            self.metricas_globales['dias_simulados'] += 1

            # Registrar métricas diarias
            self._registrar_metricas_diarias(
                dia=int(self.env.now),
                demanda_granel=demanda_granel_tm,
                demanda_envasado=demanda_envasado_tm,
                desabastecimiento_granel=desabastecimiento_granel,
                desabastecimiento_envasado=desabastecimiento_envasado
            )

            # Log periódico (cada 30 días)
            if self.env.now % 30 == 0:
                self._log_estado_sistema()

    def _registrar_metricas_diarias(
        self,
        dia: int,
        demanda_granel: float,
        demanda_envasado: float,
        desabastecimiento_granel: bool,
        desabastecimiento_envasado: bool
    ) -> None:
        """Registra las métricas diarias del sistema en el monitor."""
        # Calcular satisfacción diaria
        satisfaccion_granel = 1.0 if not desabastecimiento_granel else 0.0
        satisfaccion_envasado = 1.0 if not desabastecimiento_envasado else 0.0

        # Obtener valores acumulados actuales
        vol_hub_actual = self.hub.metricas.get('volumen_total_recibido_tm', 0)
        desp_granel_actual = self.hub.metricas.get('despachos_granel_tm', 0)
        desp_envasado_actual = self.hub.metricas.get('despachos_envasado_tm', 0)
        vol_env_actual = self.hub.metricas.get('volumen_envasado_tm', 0)
        vol_cdes_actual = self.red_cdes.metricas.get('volumen_total_recibido_tm', 0)
        viajes_actual = self.gestor_transporte_primario.metricas.get('viajes_totales', 0)

        # Calcular incrementos diarios (flujos del día)
        flujo_recepcion_dia = vol_hub_actual - self.metricas_dia_anterior['volumen_hub_recibido']
        flujo_despacho_granel_dia = desp_granel_actual - self.metricas_dia_anterior['despachos_hub_granel']
        flujo_despacho_envasado_dia = desp_envasado_actual - self.metricas_dia_anterior['despachos_hub_envasado']
        flujo_envasado_dia = vol_env_actual - self.metricas_dia_anterior['volumen_envasado_procesado']
        flujo_cdes_dia = vol_cdes_actual - self.metricas_dia_anterior['volumen_cdes_recibido']
        viajes_dia = viajes_actual - self.metricas_dia_anterior['viajes_completados']

        # Actualizar valores para el próximo día
        self.metricas_dia_anterior['volumen_hub_recibido'] = vol_hub_actual
        self.metricas_dia_anterior['despachos_hub_granel'] = desp_granel_actual
        self.metricas_dia_anterior['despachos_hub_envasado'] = desp_envasado_actual
        self.metricas_dia_anterior['volumen_envasado_procesado'] = vol_env_actual
        self.metricas_dia_anterior['volumen_cdes_recibido'] = vol_cdes_actual
        self.metricas_dia_anterior['viajes_completados'] = viajes_actual

        # Crear registro diario
        registro = RegistroDiario(
            dia=dia,
            inv_hub_granel=self.hub.inventario_granel.level,
            inv_hub_envasado=self.hub.inventario_envasado.level,
            inv_cdes=self.red_cdes.inventario.level,
            flujo_recepcion_hub=flujo_recepcion_dia,
            flujo_despacho_granel=flujo_despacho_granel_dia,
            flujo_despacho_envasado=flujo_despacho_envasado_dia,
            flujo_envasado_procesado=flujo_envasado_dia,
            flujo_reabastecimiento_cdes=flujo_cdes_dia,
            demanda_granel=demanda_granel,
            demanda_envasado=demanda_envasado,
            satisfaccion_granel=satisfaccion_granel,
            satisfaccion_envasado=satisfaccion_envasado,
            camiones_en_ruta=self.gestor_transporte_primario.metricas.get('camiones_en_ruta', 0),
            viajes_completados=viajes_dia,
            desabastecimiento_granel=desabastecimiento_granel,
            desabastecimiento_envasado=desabastecimiento_envasado,
            quiebre_stock_hub_granel=self.hub.inventario_granel.level == 0,
            quiebre_stock_hub_envasado=self.hub.inventario_envasado.level == 0,
            quiebre_stock_cdes=self.red_cdes.inventario.level == 0
        )

        # Agregar al monitor
        self.monitor.registrar_dia(registro)

    def _log_estado_sistema(self) -> None:
        """Registra el estado actual del sistema."""
        logger.info(
            f"Día {self.env.now:.0f}: "
            f"Hub granel={self.hub.inventario_granel.level:.1f} TM, "
            f"Hub envasado={self.hub.inventario_envasado.level:.1f} TM, "
            f"CDEs={self.red_cdes.inventario.level:.1f} TM, "
            f"Clientes granel={self.clientes.inventario_granel.level:.1f} TM, "
            f"Clientes envasado={self.clientes.inventario_envasado_hogares.level:.1f} TM"
        )

    def ejecutar(self) -> None:
        """Ejecuta la simulación completa."""
        if not self.inicializada:
            raise RuntimeError("Simulación no inicializada")

        logger.info(f"Iniciando simulación por {self.duracion_dias} días")

        # Ejecutar simulación
        self.env.run(until=self.duracion_dias)
        self.ejecutada = True

        # Calcular métricas finales
        self._calcular_metricas_finales()

        logger.info("Simulación completada")

    def _calcular_metricas_finales(self) -> None:
        """Calcula métricas finales del sistema."""
        # Tasa de satisfacción global
        demanda_total_granel = self.clientes.metricas['demanda_total_granel_tm']
        demanda_satisfecha_granel = self.clientes.metricas['demanda_satisfecha_granel_tm']

        demanda_total_envasado = self.clientes.metricas['demanda_total_envasado_tm']
        demanda_satisfecha_envasado = self.clientes.metricas['demanda_satisfecha_envasado_tm']

        demanda_total = demanda_total_granel + demanda_total_envasado
        demanda_satisfecha = demanda_satisfecha_granel + demanda_satisfecha_envasado

        if demanda_total > 0:
            self.metricas_globales['tasa_satisfaccion_global'] = (
                demanda_satisfecha / demanda_total * 100
            )

    def get_resultados(self) -> Dict[str, Any]:
        """Obtiene los resultados de la simulación."""
        if not self.ejecutada:
            raise RuntimeError("Simulación no ejecutada")

        return {
            'metricas_globales': self.metricas_globales,
            'hub': self.hub.metricas,
            'red_cdes': self.red_cdes.metricas,
            'clientes': self.clientes.metricas,
            'transporte_primario': self.gestor_transporte_primario.metricas,
            'distribucion_regional': self.gestor_distribucion_regional.metricas,
            'fuentes': {
                fuente_id: fuente.metricas
                for fuente_id, fuente in self.fuentes.items()
            }
        }

    def get_resumen(self) -> Dict[str, Any]:
        """Obtiene un resumen ejecutivo de la simulación."""
        if not self.ejecutada:
            raise RuntimeError("Simulación no ejecutada")

        resultados = self.get_resultados()

        return {
            'duracion_simulada_dias': self.metricas_globales['dias_simulados'],
            'tasa_satisfaccion_demanda_pct': self.metricas_globales['tasa_satisfaccion_global'],
            'dias_con_desabastecimiento': self.metricas_globales['dias_con_desabastecimiento'],
            'porcentaje_dias_desabastecimiento': (
                self.metricas_globales['dias_con_desabastecimiento'] /
                self.metricas_globales['dias_simulados'] * 100
            ),
            'viajes_transporte_primario': resultados['transporte_primario']['viajes_totales'],
            'volumen_transportado_tm': resultados['transporte_primario']['volumen_total_transportado_tm'],
            'quiebres_stock_hub_granel': resultados['hub']['quiebres_stock_granel'],
            'quiebres_stock_hub_envasado': resultados['hub']['quiebres_stock_envasado'],
            'quiebres_stock_cdes': resultados['red_cdes']['quiebres_stock'],
            'nivel_minimo_hub_granel_tm': resultados['hub']['nivel_minimo_granel_tm'],
            'nivel_minimo_hub_envasado_tm': resultados['hub']['nivel_minimo_envasado_tm']
        }
