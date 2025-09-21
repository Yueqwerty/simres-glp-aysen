"""
Modelo principal de simulación con sistema integrado de disrupciones.
Implementa arquitectura modular con inyección de dependencias y gestión avanzada de estado.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import simpy
from numpy.random import Generator as NPGenerator

from .entidades import Camion, NodoDemanda, PlantaAlmacenamiento, ProveedorExterno
from .eventos import GestorDisrupciones

logger = logging.getLogger(__name__)


class Simulacion:
    """
    Clase principal que orquesta la simulación completa del sistema.
    Integra el gemelo digital base con el sistema de disrupciones.
    """
    
    def __init__(self,
        duracion: float,
        rng: NPGenerator,
        config: Dict[str, Any]):
        self.duracion = duracion
        self.rng = rng
        self.config = config
        
        # Entorno SimPy
        self.env = simpy.Environment()
        
        # Entidades del sistema
        self.camiones: Dict[str, Camion] = {}
        self.planta: Optional[PlantaAlmacenamiento] = None
        self.nodo_demanda: Optional[NodoDemanda] = None
        self.proveedor_externo: Optional[ProveedorExterno] = None
        
        # Sistema de disrupciones (se auto-inicializa con el catálogo completo)
        self.gestor_disrupciones = GestorDisrupciones(self.env, self.rng)
        
        # Estado de la simulación
        self.inicializada = False
        self.ejecutada = False
        
        # Inicializar componentes
        self._inicializar_sistema()
    
    def _inicializar_sistema(self) -> None:
        """Inicializa todos los componentes del sistema."""
        self._crear_entidades()
        self._configurar_disrupciones()
        self._conectar_sistema()
        self.inicializada = True
        logger.info("Sistema de simulación inicializado")
    
    def _crear_entidades(self) -> None:
        """Crea todas las entidades del sistema."""
        # Crear planta de almacenamiento
        planta_config = self.config['planta']
        self.planta = PlantaAlmacenamiento(
            env=self.env,
            planta_id="planta_principal",
            rng=self.rng,
            config=planta_config
        )
        
        # Crear proveedor externo
        proveedor_config = self.config.get('proveedor_externo', {})
        self.proveedor_externo = ProveedorExterno(
            env=self.env,
            proveedor_id="proveedor_principal",
            rng=self.rng,
            config=proveedor_config,
            planta=self.planta
        )
        
        # Crear camiones
        entidades_config = self.config['entidades']
        for camion_id, camion_config in entidades_config.items():
            self.camiones[camion_id] = Camion(
                env=self.env,
                camion_id=camion_id,
                rng=self.rng,
                config=camion_config
            )
        
        # Crear nodo de demanda
        demanda_config = self.config['demanda']
        self.nodo_demanda = NodoDemanda(
            env=self.env,
            nodo_id="demanda_regional",
            rng=self.rng,
            config=demanda_config,
            planta=self.planta
        )
        
        logger.info(f"Entidades creadas: {len(self.camiones)} camiones, 1 planta, 1 proveedor, 1 nodo demanda")
    
    def _configurar_disrupciones(self) -> None:
        """Configura el sistema de disrupciones."""
        # Registrar entidades para disrupciones
        if self.planta:
            self.gestor_disrupciones.registrar_entidad(self.planta)
        if self.nodo_demanda:
            self.gestor_disrupciones.registrar_entidad(self.nodo_demanda)
        if self.proveedor_externo:
            self.gestor_disrupciones.registrar_entidad(self.proveedor_externo)
        for camion in self.camiones.values():
            self.gestor_disrupciones.registrar_entidad(camion)
        
        # Configurar riesgos activos según configuración
        riesgos_config = self.config.get('riesgos', {})
        if riesgos_config:
            self.gestor_disrupciones.configurar_riesgos_yaml(riesgos_config)
            logger.info(f"Riesgos configurados: {len(riesgos_config)} tipos activos")
        else:
            logger.info("No se configuraron riesgos específicos, usando configuración por defecto")
    
    def _conectar_sistema(self) -> None:
        """Conecta los diferentes componentes del sistema."""
        # Aquí se pueden agregar conexiones específicas entre entidades
        # Por ejemplo, asignar rutas específicas a camiones
        pass
    
    def ejecutar(self) -> None:
        """Ejecuta la simulación completa."""
        if not self.inicializada:
            raise RuntimeError("Simulación no inicializada")
        
        logger.info(f"Iniciando simulación por {self.duracion} horas")
        
        # Ejecutar simulación
        self.env.run(until=self.duracion)
        self.ejecutada = True
        
        logger.info("Simulación completada")
    
    def get_entidades(self) -> List[Any]:
        """Retorna todas las entidades del sistema."""
        entidades = []
        if self.planta:
            entidades.append(self.planta)
        if self.nodo_demanda:
            entidades.append(self.nodo_demanda)
        if self.proveedor_externo:
            entidades.append(self.proveedor_externo)
        entidades.extend(self.camiones.values())
        return entidades
    
    def get_estado_final(self) -> Dict[str, Any]:
        """Obtiene el estado final de la simulación."""
        if not self.ejecutada:
            raise RuntimeError("Simulación no ejecutada")
        
        return {
            'duracion_simulada': self.env.now,
            'estado_disrupciones': self.gestor_disrupciones.get_estado_sistema(),
            'metricas_finales': self._recopilar_metricas_finales()
        }
    
    def _recopilar_metricas_finales(self) -> Dict[str, Any]:
        """Recopila métricas finales de todas las entidades."""
        metricas = {}
        
        # Métricas de camiones
        for camion_id, camion in self.camiones.items():
            metricas[camion_id] = camion.get_metricas()
        
        # Métricas de planta
        if self.planta:
            metricas['planta_principal'] = self.planta.get_metricas()
        
        # Métricas de proveedor
        if self.proveedor_externo:
            metricas['proveedor_principal'] = self.proveedor_externo.get_metricas()
        
        # Métricas de demanda
        if self.nodo_demanda:
            metricas['demanda_regional'] = self.nodo_demanda.get_metricas()
        
        # Métricas de disrupciones
        metricas['disrupciones'] = self.gestor_disrupciones.finalizar()
        
        return metricas