"""
Entidades del sistema de simulación de cadena de suministro de GLP.
Implementa patrones de diseño avanzados y programación estocástica.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass
from enum import Enum, auto
from typing import Any, Dict, Generator, List, Optional, Protocol, Union

import numpy as np
import simpy
from numpy.random import Generator as NPGenerator

logger = logging.getLogger(__name__)


class EstadoEntidad(Enum):
    """Estados posibles de las entidades del sistema."""
    INACTIVO = auto()
    ACTIVO = auto()
    EN_TRANSITO = auto()
    CARGANDO = auto()
    DESCARGANDO = auto()
    FUERA_DE_SERVICIO = auto()


class TipoEvento(Enum):
    """Tipos de eventos del sistema."""
    INICIO_VIAJE = "inicio_viaje"
    FIN_VIAJE = "fin_viaje"
    INICIO_CARGA = "inicio_carga"
    FIN_CARGA = "fin_carga"
    INICIO_DESCARGA = "inicio_descarga"
    FIN_DESCARGA = "fin_descarga"
    QUIEBRE_STOCK = "quiebre_stock"
    REABASTECIMIENTO = "reabastecimiento"
    INICIO_DISRUPCION = "inicio_disrupcion"
    FIN_DISRUPCION = "fin_disrupcion"
    DEMANDA_SATISFECHA = "demanda_satisfecha"
    DEMANDA_NO_SATISFECHA = "demanda_no_satisfecha"


@dataclass(frozen=True)
class EventoSistema:
    """Estructura inmutable para eventos del sistema."""
    timestamp: float
    tipo: TipoEvento
    entidad_id: str
    detalles: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el evento a diccionario para serialización."""
        return {
            'timestamp': self.timestamp,
            'event_type': self.tipo.value,
            'entity_id': self.entidad_id,
            'details_json': json.dumps(self.detalles)
        }


class DistribucionEstocastica:
    """
    Wrapper para distribuciones estocásticas con validación y memoización.
    Implementa el patrón Strategy para diferentes tipos de distribuciones.
    """
    
    def __init__(self, rng: NPGenerator, tipo: str, parametros: Dict[str, float]):
        self.rng = rng
        self.tipo = tipo.lower()
        self.parametros = parametros
        self._validate_parameters()
        
        # Memoización de funciones de distribución (patrón Flyweight)
        self._distribution_cache: Dict[str, callable] = {
            'normal': lambda: self.rng.normal(
                self.parametros['media'], 
                self.parametros['desviacion']
            ),
            'lognormal': lambda: self.rng.lognormal(
                self.parametros['mu'], 
                self.parametros['sigma']
            ),
            'exponential': lambda: self.rng.exponential(
                self.parametros['scale']
            ),
            'uniform': lambda: self.rng.uniform(
                self.parametros['low'], 
                self.parametros['high']
            ),
            'gamma': lambda: self.rng.gamma(
                self.parametros['shape'], 
                self.parametros['scale']
            ),
            'weibull': lambda: self.rng.weibull(
                self.parametros['a']
            ) * self.parametros['scale']
        }
    
    def _validate_parameters(self) -> None:
        """Validación robusta de parámetros usando guards."""
        required_params = {
            'normal': ['media', 'desviacion'],
            'lognormal': ['mu', 'sigma'],
            'exponential': ['scale'],
            'uniform': ['low', 'high'],
            'gamma': ['shape', 'scale'],
            'weibull': ['a', 'scale']
        }
        
        if self.tipo not in required_params:
            raise ValueError(f"Distribución no soportada: {self.tipo}")
        
        missing = set(required_params[self.tipo]) - set(self.parametros.keys())
        if missing:
            raise ValueError(f"Parámetros faltantes para {self.tipo}: {missing}")
    
    def sample(self) -> float:
        """Genera una muestra de la distribución con clipping automático."""
        try:
            value = self._distribution_cache[self.tipo]()
            # Clipping para evitar valores negativos en tiempos
            return max(0.01, float(value)) if 'tiempo' in str(self.parametros) else float(value)
        except Exception as e:
            logger.error(f"Error sampling {self.tipo}: {e}")
            return 1.0  # Fallback seguro


class Observable(ABC):
    """Patrón Observer para notificación de eventos."""
    
    def __init__(self):
        self._observers: List[Observer] = []
    
    def add_observer(self, observer: Observer) -> None:
        if observer not in self._observers:
            self._observers.append(observer)
    
    def remove_observer(self, observer: Observer) -> None:
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self, evento: EventoSistema) -> None:
        for observer in self._observers:
            observer.update(evento)


class Observer(Protocol):
    """Protocolo para observadores de eventos."""
    
    def update(self, evento: EventoSistema) -> None:
        """Recibe notificación de evento."""
        ...


class EntidadBase(Observable):
    """Clase base para todas las entidades del sistema."""
    
    def __init__(self, 
                 env: simpy.Environment,
                 entity_id: str,
                 rng: NPGenerator,
                 config: Dict[str, Any]):
        super().__init__()
        self.env = env
        self.entity_id = entity_id
        self.rng = rng
        self.config = config
        self.estado = EstadoEntidad.INACTIVO
        self.activo = True
        self.metricas: Dict[str, float] = {}
    
    def _emit_event(self, tipo: TipoEvento, detalles: Optional[Dict[str, Any]] = None) -> None:
        """Emite un evento al sistema de monitoreo."""
        evento = EventoSistema(
            timestamp=self.env.now,
            tipo=tipo,
            entidad_id=self.entity_id,
            detalles=detalles or {}
        )
        self.notify_observers(evento)


class Camion(EntidadBase):
    """
    Camión de transporte con capacidades estocásticas avanzadas.
    Implementa el patrón State para manejo de estados complejos.
    """
    
    def __init__(self, 
                 env: simpy.Environment,
                 camion_id: str,
                 rng: NPGenerator,
                 config: Dict[str, Any]):
        super().__init__(env, camion_id, rng, config)
        
        # Configuración estocástica
        self.capacidad = config['capacidad']
        self.carga_actual = 0.0
        
        # Distribuciones estocásticas
        self._init_distributions()
        
        # Recursos SimPy
        self.disponible = simpy.Resource(env, capacity=1)
        
        # Métricas de desempeño
        self.metricas = {
            'viajes_completados': 0,
            'tiempo_total_viaje': 0.0,
            'tiempo_total_carga': 0.0,
            'tiempo_total_descarga': 0.0,
            'tiempo_inactivo': 0.0,
            'volumen_transportado': 0.0
        }
        
        # Inicio del proceso principal
        self.proceso = env.process(self.run())
    
    def _init_distributions(self) -> None:
        """Inicializa las distribuciones estocásticas."""
        dist_config = self.config.get('distribuciones', {})
        
        self.dist_tiempo_viaje = DistribucionEstocastica(
            self.rng,
            dist_config.get('tiempo_viaje', {}).get('tipo', 'lognormal'),
            dist_config.get('tiempo_viaje', {}).get('parametros', {'mu': 2.0, 'sigma': 0.3})
        )
        
        self.dist_tiempo_carga = DistribucionEstocastica(
            self.rng,
            dist_config.get('tiempo_carga', {}).get('tipo', 'gamma'),
            dist_config.get('tiempo_carga', {}).get('parametros', {'shape': 2.0, 'scale': 1.5})
        )
        
        self.dist_tiempo_descarga = DistribucionEstocastica(
            self.rng,
            dist_config.get('tiempo_descarga', {}).get('tipo', 'normal'),
            dist_config.get('tiempo_descarga', {}).get('parametros', {'media': 1.0, 'desviacion': 0.2})
        )
    
    def run(self) -> Generator:
        """Proceso principal del camión con manejo robusto de estados."""
        while self.activo:
            try:
                yield from self._ciclo_operativo()
            except simpy.Interrupt as interrupt:
                logger.info(f"Camión {self.entity_id} interrumpido: {interrupt.cause}")
                yield self.env.timeout(self.rng.exponential(0.5))  # Tiempo de recuperación
            except Exception as e:
                logger.error(f"Error en camión {self.entity_id}: {e}")
                yield self.env.timeout(1.0)  # Tiempo de gracia antes de reintentar
    
    def _ciclo_operativo(self) -> Generator:
        """Ciclo operativo completo del camión."""
        # Fase 1: Esperar disponibilidad
        with self.disponible.request() as request:
            yield request
            
            # Fase 2: Proceso de carga
            yield from self._proceso_carga()
            
            # Fase 3: Viaje
            yield from self._proceso_viaje()
            
            # Fase 4: Proceso de descarga  
            yield from self._proceso_descarga()
            
            # Fase 5: Tiempo de descanso/mantenimiento
            yield from self._tiempo_descanso()
    
    def _proceso_carga(self) -> Generator:
        """Proceso estocástico de carga."""
        self.estado = EstadoEntidad.CARGANDO
        inicio_carga = self.env.now
        
        self._emit_event(TipoEvento.INICIO_CARGA, {
            'capacidad_maxima': self.capacidad,
            'estado_anterior': self.estado.name
        })
        
        # Tiempo de carga estocástico
        tiempo_carga = self.dist_tiempo_carga.sample()
        yield self.env.timeout(tiempo_carga)
        
        # Simular carga (podría variar estocásticamente)
        self.carga_actual = self.capacidad * self.rng.uniform(0.95, 1.0)
        
        self.metricas['tiempo_total_carga'] += tiempo_carga
        
        self._emit_event(TipoEvento.FIN_CARGA, {
            'volumen_cargado': self.carga_actual,
            'tiempo_carga': tiempo_carga,
            'utilizacion': self.carga_actual / self.capacidad
        })
    
    def _proceso_viaje(self) -> Generator:
        """Proceso estocástico de viaje."""
        self.estado = EstadoEntidad.EN_TRANSITO
        inicio_viaje = self.env.now
        
        self._emit_event(TipoEvento.INICIO_VIAJE, {
            'carga_transportada': self.carga_actual
        })
        
        # Tiempo de viaje estocástico (puede ser afectado por disrupciones)
        tiempo_base = self.dist_tiempo_viaje.sample()
        factor_disrupcion = self._calcular_factor_disrupcion()
        tiempo_viaje = tiempo_base * factor_disrupcion
        
        yield self.env.timeout(tiempo_viaje)
        
        self.metricas['tiempo_total_viaje'] += tiempo_viaje
        self.metricas['volumen_transportado'] += self.carga_actual
        
        self._emit_event(TipoEvento.FIN_VIAJE, {
            'tiempo_viaje': tiempo_viaje,
            'factor_disrupcion': factor_disrupcion,
            'distancia_estimada': tiempo_viaje * 60  # Asumiendo 60 km/h promedio
        })
    
    def _proceso_descarga(self) -> Generator:
        """Proceso estocástico de descarga."""
        self.estado = EstadoEntidad.DESCARGANDO
        
        self._emit_event(TipoEvento.INICIO_DESCARGA, {
            'volumen_a_descargar': self.carga_actual
        })
        
        tiempo_descarga = self.dist_tiempo_descarga.sample()
        yield self.env.timeout(tiempo_descarga)
        
        volumen_descargado = self.carga_actual
        self.carga_actual = 0.0
        self.metricas['viajes_completados'] += 1
        self.metricas['tiempo_total_descarga'] += tiempo_descarga
        
        self._emit_event(TipoEvento.FIN_DESCARGA, {
            'volumen_descargado': volumen_descargado,
            'tiempo_descarga': tiempo_descarga,
            'viajes_acumulados': self.metricas['viajes_completados']
        })
    
    def _tiempo_descanso(self) -> Generator:
        """Tiempo de descanso entre ciclos."""
        tiempo_descanso = self.rng.exponential(0.5)  # Media de 0.5 horas
        inicio_descanso = self.env.now
        
        self.estado = EstadoEntidad.INACTIVO
        yield self.env.timeout(tiempo_descanso)
        
        self.metricas['tiempo_inactivo'] += tiempo_descanso
    
    def _calcular_factor_disrupcion(self) -> float:
        """Calcula el factor de impacto de disrupciones activas."""
        # Placeholder - será implementado en Fase 2
        return 1.0
    
    def get_metricas(self) -> Dict[str, float]:
        """Retorna métricas de desempeño actualizadas."""
        tiempo_total = self.env.now
        if tiempo_total > 0:
            self.metricas['utilizacion_temporal'] = (
                (self.metricas['tiempo_total_viaje'] + 
                 self.metricas['tiempo_total_carga'] + 
                 self.metricas['tiempo_total_descarga']) / tiempo_total
            )
            
            if self.metricas['viajes_completados'] > 0:
                self.metricas['tiempo_promedio_ciclo'] = (
                    tiempo_total / self.metricas['viajes_completados']
                )
        
        return self.metricas.copy()


class PlantaAlmacenamiento(EntidadBase):
    """
    Planta de almacenamiento con gestión avanzada de inventario.
    Implementa patrones de gestión de recursos con notificaciones push.
    """
    
    def __init__(self, 
                 env: simpy.Environment,
                 planta_id: str,
                 rng: NPGenerator,
                 config: Dict[str, Any]):
        super().__init__(env, planta_id, rng, config)
        
        # Configuración de capacidad
        self.capacidad_maxima = config['capacidad_maxima']
        self.nivel_critico = config.get('nivel_critico', 0.2 * self.capacidad_maxima)
        self.nivel_reabastecimiento = config.get('nivel_reabastecimiento', 0.8 * self.capacidad_maxima)
        
        # Container de SimPy para inventario
        self.inventario = simpy.Container(
            env, 
            capacity=self.capacidad_maxima, 
            init=config.get('inventario_inicial', self.capacidad_maxima * 0.5)
        )
        
        # Eventos para gestión de inventario
        self.necesita_reabastecimiento = simpy.Event(env)
        self.stock_critico = simpy.Event(env)
        
        # Métricas de inventario
        self.metricas = {
            'nivel_minimo_registrado': float('inf'),
            'nivel_maximo_registrado': 0.0,
            'tiempo_bajo_critico': 0.0,
            'numero_quiebres_stock': 0,
            'numero_reabastecimientos': 0,
            'volumen_total_suministrado': 0.0
        }
        
        # Proceso de monitoreo continuo
        self.proceso_monitor = env.process(self._monitorear_inventario())
    
    def _monitorear_inventario(self) -> Generator:
        """Monitoreo continuo del nivel de inventario."""
        ultimo_timestamp = self.env.now
        
        while True:
            nivel_actual = self.inventario.level
            
            # Actualizar métricas
            self.metricas['nivel_minimo_registrado'] = min(
                self.metricas['nivel_minimo_registrado'], nivel_actual
            )
            self.metricas['nivel_maximo_registrado'] = max(
                self.metricas['nivel_maximo_registrado'], nivel_actual
            )
            
            # Verificar condiciones críticas
            if nivel_actual <= self.nivel_critico:
                tiempo_transcurrido = self.env.now - ultimo_timestamp
                self.metricas['tiempo_bajo_critico'] += tiempo_transcurrido
                
                if not self.stock_critico.triggered:
                    self.stock_critico.succeed()
                    self._emit_event(TipoEvento.QUIEBRE_STOCK, {
                        'nivel_actual': nivel_actual,
                        'nivel_critico': self.nivel_critico,
                        'porcentaje_ocupacion': nivel_actual / self.capacidad_maxima * 100
                    })
            
            # Verificar necesidad de reabastecimiento
            if nivel_actual <= self.nivel_reabastecimiento:
                if not self.necesita_reabastecimiento.triggered:
                    self.necesita_reabastecimiento.succeed()
            
            ultimo_timestamp = self.env.now
            yield self.env.timeout(0.1)  # Monitoreo cada 6 minutos (0.1 horas)
    
    def reabastecer(self, volumen: float) -> Generator:
        """Proceso de reabastecimiento de inventario."""
        try:
            yield self.inventario.put(volumen)
            self.metricas['numero_reabastecimientos'] += 1
            self.metricas['volumen_total_suministrado'] += volumen
            
            # Reset de eventos
            self.necesita_reabastecimiento = simpy.Event(self.env)
            self.stock_critico = simpy.Event(self.env)
            
            self._emit_event(TipoEvento.REABASTECIMIENTO, {
                'volumen_añadido': volumen,
                'nivel_resultante': self.inventario.level,
                'porcentaje_ocupacion': self.inventario.level / self.capacidad_maxima * 100
            })
            
        except simpy.ContainerPut as e:
            logger.warning(f"Reabastecimiento excede capacidad en {self.entity_id}: {e}")
    
    def consumir(self, volumen: float) -> Generator:
        """Proceso de consumo de inventario."""
        try:
            yield self.inventario.get(volumen)
            return volumen
        except simpy.ContainerGet:
            # Consumo parcial si no hay suficiente inventario
            disponible = self.inventario.level
            if disponible > 0:
                yield self.inventario.get(disponible)
                return disponible
            return 0.0


class NodoDemanda(EntidadBase):
    """
    Nodo generador de demanda estocástica con patrones temporales.
    Implementa algoritmos de predicción de demanda y gestión de patrones estacionales.
    """
    
    def __init__(self, 
                 env: simpy.Environment,
                 nodo_id: str,
                 rng: NPGenerator,
                 config: Dict[str, Any],
                 planta: PlantaAlmacenamiento):
        super().__init__(env, nodo_id, rng, config)
        self.planta = planta
        
        # Configuración de demanda
        self.intervalo_demanda = config.get('intervalo_demanda', 24.0)  # horas
        
        # Distribuciones de demanda
        self._init_demand_distributions(config.get('distribuciones_demanda', {}))
        
        # Patrones temporales (implementación de series de tiempo)
        self.patron_estacional = self._init_seasonal_pattern(config.get('patron_estacional', {}))
        
        # Métricas de demanda
        self.metricas = {
            'demanda_total_generada': 0.0,
            'demanda_total_satisfecha': 0.0,
            'numero_eventos_demanda': 0,
            'numero_eventos_no_satisfechos': 0,
            'tiempo_acumulado_desabastecimiento': 0.0
        }
        
        # Iniciar proceso de generación de demanda
        self.proceso = env.process(self.run())
    
    def _init_demand_distributions(self, config: Dict[str, Any]) -> None:
        """Inicializa distribuciones de demanda."""
        base_config = config.get('base', {})
        self.dist_demanda_base = DistribucionEstocastica(
            self.rng,
            base_config.get('tipo', 'lognormal'),
            base_config.get('parametros', {'mu': 1.5, 'sigma': 0.4})
        )
        
        # Distribución para variabilidad temporal
        variability_config = config.get('variabilidad', {})
        self.dist_variabilidad = DistribucionEstocastica(
            self.rng,
            variability_config.get('tipo', 'normal'),
            variability_config.get('parametros', {'media': 1.0, 'desviacion': 0.15})
        )
    
    def _init_seasonal_pattern(self, config: Dict[str, Any]) -> callable:
        """Inicializa patrón estacional usando funciones trigonométricas."""
        amplitud = config.get('amplitud', 0.2)
        fase = config.get('fase', 0.0)
        periodo = config.get('periodo', 24.0 * 7)  # Semanal por defecto
        
        return lambda t: 1.0 + amplitud * np.sin(2 * np.pi * t / periodo + fase)
    
    def run(self) -> Generator:
        """Proceso principal de generación de demanda."""
        while True:
            try:
                # Esperar próximo evento de demanda
                yield self.env.timeout(self.intervalo_demanda)
                
                # Generar demanda estocástica
                demanda = self._generar_demanda()
                
                # Intentar satisfacer demanda
                yield from self._procesar_demanda(demanda)
                
            except Exception as e:
                logger.error(f"Error en nodo de demanda {self.entity_id}: {e}")
                yield self.env.timeout(1.0)
    
    def _generar_demanda(self) -> float:
        """Genera demanda estocástica con patrones temporales."""
        # Demanda base estocástica
        demanda_base = self.dist_demanda_base.sample()
        
        # Factor estacional
        factor_estacional = self.patron_estacional(self.env.now)
        
        # Variabilidad adicional
        factor_variabilidad = self.dist_variabilidad.sample()
        
        # Demanda final con todos los componentes
        demanda_total = demanda_base * factor_estacional * factor_variabilidad
        
        return max(0.1, demanda_total)  # Evitar demanda negativa o cero
    
    def _procesar_demanda(self, demanda: float) -> Generator:
        """Procesa un evento de demanda contra el inventario disponible."""
        inicio_evento = self.env.now
        
        self.metricas['demanda_total_generada'] += demanda
        self.metricas['numero_eventos_demanda'] += 1
        
        try:
            # Intentar consumir de la planta
            volumen_satisfecho = yield from self.planta.consumir(demanda)
            
            if volumen_satisfecho >= demanda * 0.99:  # Tolerancia del 1%
                # Demanda completamente satisfecha
                self.metricas['demanda_total_satisfecha'] += volumen_satisfecho
                
                self._emit_event(TipoEvento.DEMANDA_SATISFECHA, {
                    'demanda_solicitada': demanda,
                    'volumen_suministrado': volumen_satisfecho,
                    'nivel_inventario_restante': self.planta.inventario.level,
                    'tiempo_procesamiento': self.env.now - inicio_evento
                })
            else:
                # Demanda parcialmente satisfecha o no satisfecha
                deficit = demanda - volumen_satisfecho
                self.metricas['numero_eventos_no_satisfechos'] += 1
                self.metricas['demanda_total_satisfecha'] += volumen_satisfecho
                
                self._emit_event(TipoEvento.DEMANDA_NO_SATISFECHA, {
                    'demanda_solicitada': demanda,
                    'volumen_suministrado': volumen_satisfecho,
                    'deficit': deficit,
                    'porcentaje_satisfaccion': (volumen_satisfecho / demanda) * 100,
                    'nivel_inventario_restante': self.planta.inventario.level
                })
                
                # Calcular tiempo de desabastecimiento
                self.metricas['tiempo_acumulado_desabastecimiento'] += (
                    self.env.now - inicio_evento
                )
                
        except Exception as e:
            logger.error(f"Error procesando demanda en {self.entity_id}: {e}")
    
    def get_metricas(self) -> Dict[str, float]:
        """Retorna métricas de demanda actualizadas."""
        metricas = self.metricas.copy()
        
        if metricas['demanda_total_generada'] > 0:
            metricas['tasa_satisfaccion'] = (
                metricas['demanda_total_satisfecha'] / metricas['demanda_total_generada']
            ) * 100
            
        if metricas['numero_eventos_demanda'] > 0:
            metricas['demanda_promedio_por_evento'] = (
                metricas['demanda_total_generada'] / metricas['numero_eventos_demanda']
            )
            
            metricas['tasa_eventos_no_satisfechos'] = (
                metricas['numero_eventos_no_satisfechos'] / metricas['numero_eventos_demanda']
            ) * 100
        
        return metricas