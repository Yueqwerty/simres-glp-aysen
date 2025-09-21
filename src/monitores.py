"""
Sistema robusto de monitoreo y recolección de datos para simulación.
Implementa patrones Observer, Strategy y Repository para gestión eficiente de datos.
"""
from __future__ import annotations

import logging
import threading
from abc import ABC, abstractmethod
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Set, Union
from weakref import WeakSet

import pandas as pd

from .entidades import EventoSistema, Observer, TipoEvento

logger = logging.getLogger(__name__)


@dataclass
class MetricasAcumuladas:
    """Estructura para métricas acumuladas del sistema."""
    eventos_por_tipo: Dict[TipoEvento, int] = field(default_factory=lambda: defaultdict(int))
    eventos_por_entidad: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    timestamps_eventos: List[float] = field(default_factory=list)
    duraciones_procesos: Dict[str, List[float]] = field(default_factory=lambda: defaultdict(list))
    niveles_inventario: List[float] = field(default_factory=list)
    metricas_kpi: Dict[str, float] = field(default_factory=dict)


class EstrategiaAggregacion(ABC):
    """Estrategia abstracta para agregación de datos."""
    
    @abstractmethod
    def agregar(self, eventos: List[EventoSistema]) -> Dict[str, Any]:
        """Agrega una lista de eventos según la estrategia específica."""
        pass


class AggregacionTemporal(EstrategiaAggregacion):
    """Agregación temporal con ventanas deslizantes."""
    
    def __init__(self, tamaño_ventana: float = 24.0):
        self.tamaño_ventana = tamaño_ventana
    
    def agregar(self, eventos: List[EventoSistema]) -> Dict[str, Any]:
        """Agrega eventos en ventanas temporales."""
        if not eventos:
            return {}
        
        # Ordenar eventos por timestamp
        eventos_ordenados = sorted(eventos, key=lambda e: e.timestamp)
        
        # Crear ventanas temporales
        ventanas = []
        inicio_ventana = eventos_ordenados[0].timestamp
        eventos_ventana = []
        
        for evento in eventos_ordenados:
            if evento.timestamp <= inicio_ventana + self.tamaño_ventana:
                eventos_ventana.append(evento)
            else:
                # Procesar ventana actual
                if eventos_ventana:
                    ventanas.append(self._procesar_ventana(eventos_ventana, inicio_ventana))
                
                # Iniciar nueva ventana
                inicio_ventana = evento.timestamp
                eventos_ventana = [evento]
        
        # Procesar última ventana
        if eventos_ventana:
            ventanas.append(self._procesar_ventana(eventos_ventana, inicio_ventana))
        
        return {'ventanas_temporales': ventanas, 'num_ventanas': len(ventanas)}
    
    def _procesar_ventana(self, eventos: List[EventoSistema], inicio: float) -> Dict[str, Any]:
        """Procesa eventos dentro de una ventana temporal."""
        return {
            'inicio_ventana': inicio,
            'fin_ventana': inicio + self.tamaño_ventana,
            'num_eventos': len(eventos),
            'tipos_evento': list(set(e.tipo for e in eventos)),
            'entidades_activas': list(set(e.entidad_id for e in eventos))
        }


class AggregacionPorTipo(EstrategiaAggregacion):
    """Agregación por tipo de evento."""
    
    def agregar(self, eventos: List[EventoSistema]) -> Dict[str, Any]:
        """Agrega eventos por tipo."""
        agregacion = defaultdict(list)
        
        for evento in eventos:
            agregacion[evento.tipo].append({
                'timestamp': evento.timestamp,
                'entidad': evento.entidad_id,
                'detalles': evento.detalles
            })
        
        # Calcular estadísticas por tipo
        stats = {}
        for tipo, eventos_tipo in agregacion.items():
            stats[tipo.value] = {
                'count': len(eventos_tipo),
                'entidades_unicas': len(set(e['entidad'] for e in eventos_tipo)),
                'primer_evento': min(e['timestamp'] for e in eventos_tipo),
                'ultimo_evento': max(e['timestamp'] for e in eventos_tipo)
            }
        
        return {'estadisticas_por_tipo': stats, 'eventos_agrupados': dict(agregacion)}


class RepositorioEventos:
    """
    Repositorio thread-safe para almacenamiento eficiente de eventos.
    Implementa patrones Repository y Singleton con optimizaciones de memoria.
    """
    
    _instance: Optional[RepositorioEventos] = None
    _lock = threading.Lock()
    
    def __new__(cls) -> RepositorioEventos:
        """Implementación thread-safe del patrón Singleton."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._eventos: Deque[EventoSistema] = deque(maxlen=100000)  # Circular buffer
            self._indices: Dict[str, Set[int]] = defaultdict(set)  # Índices para búsquedas rápidas
            self._metricas = MetricasAcumuladas()
            self._estrategias: Dict[str, EstrategiaAggregacion] = {
                'temporal': AggregacionTemporal(),
                'por_tipo': AggregacionPorTipo()
            }
            self._lock = threading.RLock()
            self._initialized = True
    
    @contextmanager
    def _transaction(self):
        """Context manager para operaciones thread-safe."""
        with self._lock:
            yield
    
    def add_evento(self, evento: EventoSistema) -> None:
        """Añade un evento al repositorio de forma thread-safe."""
        with self._transaction():
            # Añadir al buffer circular
            idx = len(self._eventos)
            self._eventos.append(evento)
            
            # Actualizar índices
            self._indices[evento.tipo.value].add(idx)
            self._indices[f"entidad_{evento.entidad_id}"].add(idx)
            
            # Actualizar métricas acumuladas
            self._actualizar_metricas(evento)
    
    def _actualizar_metricas(self, evento: EventoSistema) -> None:
        """Actualiza métricas acumuladas de forma eficiente."""
        self._metricas.eventos_por_tipo[evento.tipo] += 1
        self._metricas.eventos_por_entidad[evento.entidad_id] += 1
        self._metricas.timestamps_eventos.append(evento.timestamp)
        
        # Procesar detalles específicos por tipo de evento
        if 'tiempo_viaje' in evento.detalles:
            self._metricas.duraciones_procesos['viaje'].append(evento.detalles['tiempo_viaje'])
        
        if 'nivel_inventario_restante' in evento.detalles:
            self._metricas.niveles_inventario.append(
                evento.detalles['nivel_inventario_restante']
            )
    
    def get_eventos(self, 
                   filtro_tipo: Optional[TipoEvento] = None,
                   filtro_entidad: Optional[str] = None,
                   rango_temporal: Optional[tuple] = None) -> List[EventoSistema]:
        """Recupera eventos con filtros opcionales."""
        with self._transaction():
            eventos = list(self._eventos)
        
        # Aplicar filtros
        if filtro_tipo:
            eventos = [e for e in eventos if e.tipo == filtro_tipo]
        
        if filtro_entidad:
            eventos = [e for e in eventos if e.entidad_id == filtro_entidad]
        
        if rango_temporal:
            inicio, fin = rango_temporal
            eventos = [e for e in eventos if inicio <= e.timestamp <= fin]
        
        return eventos
    
    def get_metricas(self) -> MetricasAcumuladas:
        """Retorna métricas acumuladas actualizadas."""
        with self._transaction():
            return self._metricas
    
    def agregar_datos(self, estrategia: str = 'temporal') -> Dict[str, Any]:
        """Agrega datos usando la estrategia especificada."""
        if estrategia not in self._estrategias:
            raise ValueError(f"Estrategia no válida: {estrategia}")
        
        with self._transaction():
            eventos = list(self._eventos)
        
        return self._estrategias[estrategia].agregar(eventos)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convierte eventos a DataFrame para análisis."""
        with self._transaction():
            eventos = list(self._eventos)
        
        if not eventos:
            return pd.DataFrame()
        
        # Convertir eventos a registros
        registros = [evento.to_dict() for evento in eventos]
        df = pd.DataFrame(registros)
        
        # Optimizaciones de tipos de datos
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='h')
            df['event_type'] = df['event_type'].astype('category')
            df['entity_id'] = df['entity_id'].astype('category')
        
        return df
    
    def clear(self) -> None:
        """Limpia el repositorio (útil para testing)."""
        with self._transaction():
            self._eventos.clear()
            self._indices.clear()
            self._metricas = MetricasAcumuladas()


class MonitorSistema(Observer):
    """
    Monitor principal del sistema que implementa el patrón Observer.
    Optimizado para alta frecuencia de eventos con buffering inteligente.
    """
    
    def __init__(self, 
                 buffer_size: int = 1000,
                 auto_flush: bool = True,
                 flush_interval: float = 10.0):
        self.repositorio = RepositorioEventos()
        self.buffer_size = buffer_size
        self.auto_flush = auto_flush
        self.flush_interval = flush_interval
        
        # Buffer local para escritura en batch
        self._buffer: List[EventoSistema] = []
        self._buffer_lock = threading.Lock()
        self._ultimo_flush = 0.0
        
        # Estadísticas de performance
        self.stats = {
            'eventos_recibidos': 0,
            'eventos_bufferizados': 0,
            'flushes_realizados': 0,
            'tiempo_ultimo_flush': 0.0
        }
    
    def update(self, evento: EventoSistema) -> None:
        """Recibe notificación de evento (patrón Observer)."""
        with self._buffer_lock:
            self._buffer.append(evento)
            self.stats['eventos_recibidos'] += 1
            
            # Auto-flush si es necesario
            if (self.auto_flush and 
                (len(self._buffer) >= self.buffer_size or 
                 self._debe_hacer_flush(evento.timestamp))):
                self._flush_buffer()
    
    def _debe_hacer_flush(self, timestamp: float) -> bool:
        """Determina si debe hacer flush basado en tiempo."""
        return timestamp - self._ultimo_flush >= self.flush_interval
    
    def _flush_buffer(self) -> None:
        """Vuelca el buffer al repositorio principal."""
        if not self._buffer:
            return
        
        # Copiar y limpiar buffer
        eventos_a_procesar = self._buffer.copy()
        self._buffer.clear()
        
        # Procesar en batch (más eficiente)
        for evento in eventos_a_procesar:
            self.repositorio.add_evento(evento)
        
        # Actualizar estadísticas
        self.stats['eventos_bufferizados'] += len(eventos_a_procesar)
        self.stats['flushes_realizados'] += 1
        self.stats['tiempo_ultimo_flush'] = eventos_a_procesar[-1].timestamp if eventos_a_procesar else 0.0
        
        self._ultimo_flush = self.stats['tiempo_ultimo_flush']
    
    def flush(self) -> None:
        """Fuerza el flush del buffer."""
        with self._buffer_lock:
            self._flush_buffer()
    
    def get_datos_simulacion(self) -> Dict[str, Any]:
        """Retorna todos los datos de la simulación para export."""
        self.flush()  # Asegurar que todos los datos estén persistidos
        
        return {
            'eventos': self.repositorio.to_dataframe(),
            'metricas': self.repositorio.get_metricas(),
            'agregacion_temporal': self.repositorio.agregar_datos('temporal'),
            'agregacion_por_tipo': self.repositorio.agregar_datos('por_tipo'),
            'stats_monitor': self.stats.copy()
        }
    
    def reset(self) -> None:
        """Reinicia el monitor (útil entre simulaciones)."""
        with self._buffer_lock:
            self._buffer.clear()
            self.repositorio.clear()
            self.stats = {
                'eventos_recibidos': 0,
                'eventos_bufferizados': 0,
                'flushes_realizados': 0,
                'tiempo_ultimo_flush': 0.0
            }
            self._ultimo_flush = 0.0


class AnalizadorRealTime:
    """
    Analizador en tiempo real para detección de anomalías y patrones.
    Utiliza algoritmos online para análisis streaming.
    """
    
    def __init__(self, ventana_analisis: int = 100):
        self.ventana_analisis = ventana_analisis
        self.historia_eventos: Deque[EventoSistema] = deque(maxlen=ventana_analisis)
        self.alertas_activas: Set[str] = set()
        
        # Umbrales adaptativos para detección de anomalías
        self.umbrales = {
            'tasa_eventos_alta': 10.0,  # eventos por hora
            'tiempo_entre_reabastecimientos_max': 48.0,  # horas
            'nivel_inventario_critico': 0.1  # 10% de capacidad
        }
    
    def procesar_evento(self, evento: EventoSistema) -> List[str]:
        """Procesa un evento y retorna alertas generadas."""
        self.historia_eventos.append(evento)
        alertas = []
        
        # Análisis 1: Tasa de eventos anómala
        if self._detectar_tasa_eventos_alta():
            alerta = f"Tasa de eventos alta detectada en {evento.timestamp}"
            if alerta not in self.alertas_activas:
                alertas.append(alerta)
                self.alertas_activas.add(alerta)
        
        # Análisis 2: Patrones de quiebre de stock
        if evento.tipo == TipoEvento.QUIEBRE_STOCK:
            alertas.extend(self._analizar_quiebre_stock(evento))
        
        # Análisis 3: Eficiencia operacional
        if evento.tipo == TipoEvento.FIN_VIAJE:
            alertas.extend(self._analizar_eficiencia_viaje(evento))
        
        return alertas
    
    def _detectar_tasa_eventos_alta(self) -> bool:
        """Detecta si la tasa de eventos es anómalamente alta."""
        if len(self.historia_eventos) < 10:
            return False
        
        # Calcular tasa en la ventana actual
        tiempo_ventana = (self.historia_eventos[-1].timestamp - 
                         self.historia_eventos[0].timestamp)
        if tiempo_ventana <= 0:
            return False
        
        tasa_actual = len(self.historia_eventos) / tiempo_ventana
        return tasa_actual > self.umbrales['tasa_eventos_alta']
    
    def _analizar_quiebre_stock(self, evento: EventoSistema) -> List[str]:
        """Analiza eventos de quiebre de stock para patrones."""
        alertas = []
        
        # Buscar quiebres de stock recientes
        quiebres_recientes = [
            e for e in self.historia_eventos 
            if e.tipo == TipoEvento.QUIEBRE_STOCK and 
               evento.timestamp - e.timestamp <= 24.0
        ]
        
        if len(quiebres_recientes) >= 3:
            alertas.append(f"Patrón de quiebres de stock recurrentes detectado")
        
        return alertas
    
    def _analizar_eficiencia_viaje(self, evento: EventoSistema) -> List[str]:
        """Analiza eficiencia de viajes."""
        alertas = []
        
        if 'tiempo_viaje' in evento.detalles:
            tiempo_viaje = evento.detalles['tiempo_viaje']
            
            # Calcular tiempo promedio de viajes recientes
            tiempos_recientes = [
                e.detalles.get('tiempo_viaje', 0) 
                for e in self.historia_eventos 
                if e.tipo == TipoEvento.FIN_VIAJE and 
                   'tiempo_viaje' in e.detalles
            ]
            
            if tiempos_recientes:
                tiempo_promedio = sum(tiempos_recientes) / len(tiempos_recientes)
                
                if tiempo_viaje > tiempo_promedio * 1.5:
                    alertas.append(f"Tiempo de viaje anómalamente alto: {tiempo_viaje:.2f}h")
        
        return alertas