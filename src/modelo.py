"""
Modelo principal de simulación con sistema integrado de disrupciones.
Implementa arquitectura modular con inyección de dependencias y gestión avanzada de estado.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import simpy
from numpy.random import Generator as NPGenerator

from .entidades import Camion, NodoDemanda, PlantaAlmacenamiento
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
        
        # Sistema de disrupciones
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
        
        logger.info(f"Entidades creadas: {len(self.camiones)} camiones, 1 planta, 1 nodo demanda")
    
    def _configurar_disrupciones(self) -> None:
        """Configura el sistema de disrupciones."""
        # Registrar entidades para disrupciones
        self.gestor_disrupciones.registrar_entidad(self.planta)
        for camion in self.camiones.values():
            self.gestor_disrupciones.registrar_entidad(camion)
        
        # Configurar riesgos activos
        riesgos_config = self.config.get('riesgos', {})
        if riesgos_config:
            self.gestor_disrupciones.configurar_riesgos(riesgos_config)
            logger.info(f"Riesgos configurados: {len(riesgos_config)} tipos activos")
    
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
            metricas['planta_principal'] = self.planta.metricas.copy()
        
        # Métricas de demanda
        if self.nodo_demanda:
            metricas['demanda_regional'] = self.nodo_demanda.get_metricas()
        
        # Métricas de disrupciones
        metricas['disrupciones'] = self.gestor_disrupciones.finalizar()
        
        return metricas
    

def _cargar_catalogo_riesgos_real(self) -> None:
    """Carga el catálogo real de 77 riesgos identificados en el estudio."""
    
    # ========================================================================
    # RIESGOS DE NIVEL ALTO (Factor de Riesgo ≥ 16) - 5 riesgos
    # ========================================================================
    riesgos_alto = [
        {
            "tag": "8-PT-SC", "evento": "Cierre Puerto por Mal tiempo",
            "proceso": "Puerto Maritimo", "locacion": "P. Chacabuco",
            "prob": 4, "consec": 4, "riesgo": 21,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "57-ST-CU", "evento": "Nevadas / Cierre cruce fronterizo", 
            "proceso": "Suministro Terrestre Neuquen", "locacion": "Cruce Fronterizo",
            "prob": 4, "consec": 4, "riesgo": 21,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "58-ST-CU", "evento": "Mantencion Tramo Lago Blanco - Balmaceda",
            "proceso": "Suministro Terrestre Neuquen", "locacion": "Ruta Lago Blanco",
            "prob": 4, "consec": 4, "riesgo": 21,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "62-ST-CU", "evento": "Mantencion Tramo Lago Blanco - Balmaceda",
            "proceso": "Suministro Terrestre Cabo Negro", "locacion": "Ruta Lago Blanco", 
            "prob": 4, "consec": 4, "riesgo": 21,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "63-ST-CU", "evento": "Nevadas / Cierre cruce fronterizo",
            "proceso": "Suministro Terrestre Cabo Negro", "locacion": "Cruce Fronterizo",
            "prob": 4, "consec": 4, "riesgo": 21,
            "categoria": CategoriaRiesgo.CLIMATICO
        }
    ]
    
    # ========================================================================
    # RIESGOS SIGNIFICATIVOS (Factor de Riesgo 12-18) - 21 riesgos  
    # ========================================================================
    riesgos_significativo = [
        {
            "tag": "1-AP-SC", "evento": "Cierre Puerto por Mal tiempo",
            "proceso": "Aprovisionamiento San Vicente", "locacion": "San Vicente",
            "prob": 4, "consec": 3, "riesgo": 17,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "4-AP-CU", "evento": "Paro laboral / Toma / Bloqueo ruta", 
            "proceso": "Aprovisionamiento San Vicente", "locacion": "San Vicente",
            "prob": 2, "consec": 4, "riesgo": 14,
            "categoria": CategoriaRiesgo.SOCIAL
        },
        {
            "tag": "9-PT-MA", "evento": "Contaminacion ambiental",
            "proceso": "Puerto Maritimo", "locacion": "P. Chacabuco",
            "prob": 1, "consec": 5, "riesgo": 15,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "10-PT-CU", "evento": "Falla de Terminal Maritimo",
            "proceso": "Puerto Maritimo", "locacion": "P. Chacabuco", 
            "prob": 2, "consec": 5, "riesgo": 19,
            "categoria": CategoriaRiesgo.TECNICO
        },
        {
            "tag": "12-SM-CU", "evento": "Averia gruesa",
            "proceso": "Suministro Maritimo", "locacion": "Nave P. Aysen",
            "prob": 1, "consec": 5, "riesgo": 15,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "13-SM-CU", "evento": "Indisponibilidad de nave",
            "proceso": "Suministro Maritimo", "locacion": "Nave P. Aysen",
            "prob": 2, "consec": 4, "riesgo": 14,
            "categoria": CategoriaRiesgo.LOGISTICO
        },
        {
            "tag": "16-SM-CU", "evento": "Indisponibilidad de oferta",
            "proceso": "Suministro Maritimo", "locacion": "Barcaza",
            "prob": 3, "consec": 4, "riesgo": 18,
            "categoria": CategoriaRiesgo.LOGISTICO
        },
        {
            "tag": "17-SM-CU", "evento": "Mal Tiempo",
            "proceso": "Suministro Maritimo", "locacion": "Barcaza",
            "prob": 3, "consec": 4, "riesgo": 18,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "34-TA-CU", "evento": "Accidente / Incendio",
            "proceso": "Planta Almac.", "locacion": "P. Chacabuco",
            "prob": 1, "consec": 5, "riesgo": 15,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "37-TA-CU", "evento": "Quiebre stock de cilindros",
            "proceso": "Planta Almac.", "locacion": "Ciudad Coyahique",
            "prob": 2, "consec": 4, "riesgo": 14,
            "categoria": CategoriaRiesgo.LOGISTICO
        },
        {
            "tag": "39-TA-CU", "evento": "Falla Planta de envasado",
            "proceso": "Planta Almac.", "locacion": "Ciudad Coyahique",
            "prob": 2, "consec": 4, "riesgo": 14,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "45-ST-CU", "evento": "Cortes de ruta por conflicto social",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "Ruta Balmaceda",
            "prob": 2, "consec": 4, "riesgo": 14,
            "categoria": CategoriaRiesgo.SOCIAL
        },
        {
            "tag": "46-ST-CU", "evento": "Nevadas / Cierre cruce fronterizo",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "Cruce Fronterizo",
            "prob": 2, "consec": 4, "riesgo": 14,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "47-ST-CU", "evento": "Mantencion Tramo Lago Blanco - Balmaceda",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "Ruta Lago Blanco",
            "prob": 4, "consec": 3, "riesgo": 17,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "48-ST-CU", "evento": "Aluviones",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "Ruta Balmaceda",
            "prob": 2, "consec": 4, "riesgo": 14,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "56-ST-CU", "evento": "Cortes de ruta por conflicto social",
            "proceso": "Suministro Terrestre Neuquen", "locacion": "Ruta Neuquen",
            "prob": 3, "consec": 4, "riesgo": 18,
            "categoria": CategoriaRiesgo.SOCIAL
        },
        {
            "tag": "64-ST-CU", "evento": "Aluviones",
            "proceso": "Suministro Terrestre Cabo Negro", "locacion": "Ruta Cabo Negro",
            "prob": 2, "consec": 4, "riesgo": 14,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "71-CA-CU", "evento": "Inhabilitacion B/T o T.M.",
            "proceso": "Control Autoridad", "locacion": "P. Chacabuco",
            "prob": 1, "consec": 5, "riesgo": 15,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "73-DI-CU", "evento": "Restriccion capacidad ruta Queulat",
            "proceso": "Distribucion", "locacion": "Rutas Regionales",
            "prob": 4, "consec": 3, "riesgo": 17,
            "categoria": CategoriaRiesgo.LOGISTICO
        },
        {
            "tag": "74-DI-CU", "evento": "Restriccion capacidad ruta el Diablo",
            "proceso": "Distribucion", "locacion": "Rutas Regionales",
            "prob": 4, "consec": 3, "riesgo": 17,
            "categoria": CategoriaRiesgo.LOGISTICO
        },
        {
            "tag": "75-DI-CU", "evento": "Restriccion capacidad puentes (< 45 Ton)",
            "proceso": "Distribucion", "locacion": "Rutas Regionales",
            "prob": 5, "consec": 2, "riesgo": 16,
            "categoria": CategoriaRiesgo.LOGISTICO
        }
    ]
    
    # ========================================================================
    # RIESGOS MEDIANOS Y BAJOS (Factor de Riesgo ≤ 12) - 51 riesgos
    # ========================================================================
    riesgos_mediano_bajo = [
        # Medianos (factor 6-12)
        {
            "tag": "2-AP-MA", "evento": "Contaminacion ambiental",
            "proceso": "Aprovisionamiento San Vicente", "locacion": "San Vicente",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "3-AP-CU", "evento": "Falla de mantenimiento", 
            "proceso": "Aprovisionamiento San Vicente", "locacion": "San Vicente",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "6-AP-CU", "evento": "Falla de mantenimiento",
            "proceso": "Aprovisionamiento Cabo Negro", "locacion": "Cabo Negro",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "7-AP-CU", "evento": "Paro laboral / Toma / Bloqueo ruta",
            "proceso": "Aprovisionamiento Cabo Negro", "locacion": "Cabo Negro",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.SOCIAL
        },
        {
            "tag": "11-PT-CU", "evento": "Paro laboral / Toma / Bloqueo ruta",
            "proceso": "Puerto Maritimo", "locacion": "P. Chacabuco",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.SOCIAL
        },
        {
            "tag": "15-SM-CU", "evento": "En otra ruta",
            "proceso": "Suministro Maritimo", "locacion": "Nave Don Gonzalo",
            "prob": 4, "consec": 2, "riesgo": 12,
            "categoria": CategoriaRiesgo.LOGISTICO
        },
        {
            "tag": "18-AP-CU", "evento": "Falla Refineria",
            "proceso": "Aprovisionamiento Refineria Biobio", "locacion": "Refineria Biobio",
            "prob": 2, "consec": 3, "riesgo": 9,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "27-AP-CU", "evento": "Mantenimiento estanque",
            "proceso": "Aprovisionamiento Cabo Negro", "locacion": "Cabo Negro",
            "prob": 1, "consec": 3, "riesgo": 6,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "28-AP-CU", "evento": "Falla Patio de Carga",
            "proceso": "Aprovisionamiento Cabo Negro", "locacion": "Cabo Negro", 
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "29-AP-CU", "evento": "Accidente / Incendio",
            "proceso": "Aprovisionamiento Cabo Negro", "locacion": "Cabo Negro",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "30-AP-CU", "evento": "Contaminacion ambiental",
            "proceso": "Aprovisionamiento Cabo Negro", "locacion": "Cabo Negro",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "31-TA-CU", "evento": "Falla Planta",
            "proceso": "Planta Almac.", "locacion": "P. Chacabuco",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "32-TA-CU", "evento": "Mantenimiento tanque",
            "proceso": "Planta Almac.", "locacion": "P. Chacabuco",
            "prob": 1, "consec": 3, "riesgo": 6,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "33-TA-CU", "evento": "Falla Patio de Carga",
            "proceso": "Planta Almac.", "locacion": "P. Chacabuco",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "35-TA-CU", "evento": "Contaminacion ambiental",
            "proceso": "Planta Almac.", "locacion": "P. Chacabuco",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "36-TA-CU", "evento": "Mantenimiento tanque",
            "proceso": "Planta Almac.", "locacion": "Ciudad Coyahique",
            "prob": 1, "consec": 3, "riesgo": 6,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "38-TA-CU", "evento": "Falla Patio de Carga",
            "proceso": "Planta Almac.", "locacion": "Ciudad Coyahique",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "40-TA-CU", "evento": "Accidente / Incendio",
            "proceso": "Planta Almac.", "locacion": "Ciudad Coyahique",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "41-TA-CU", "evento": "Contaminacion ambiental",
            "proceso": "Planta Almac.", "locacion": "Ciudad Coyahique",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "42-ST-CU", "evento": "Mantenimiento tanque",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "T. Aereo Balmaceda",
            "prob": 1, "consec": 3, "riesgo": 6,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "43-ST-CU", "evento": "Accidente / Incendio",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "T. Aereo Balmaceda",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "44-ST-CU", "evento": "Contaminacion ambiental",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "T. Aereo Balmaceda",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "49-ST-CU", "evento": "Mal Tiempo",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "Ruta Balmaceda",
            "prob": 2, "consec": 3, "riesgo": 9,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "52-ST-CU", "evento": "Mantencion Tramo Lago Blanco - Balmaceda",
            "proceso": "Suministro Terrestre Ruta Origen Pureo", "locacion": "Ruta Lago Blanco",
            "prob": 4, "consec": 2, "riesgo": 12,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "59-ST-CU", "evento": "Aluviones",
            "proceso": "Suministro Terrestre Neuquen", "locacion": "Ruta Neuquen",
            "prob": 2, "consec": 3, "riesgo": 9,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "72-CA-CU", "evento": "Inhabilitacion de Planta",
            "proceso": "Control Autoridad", "locacion": "Ciudad Coyahique",
            "prob": 1, "consec": 4, "riesgo": 10,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "76-DI-CU", "evento": "Restriccion capacidad paso Las Llaves",
            "proceso": "Distribucion", "locacion": "Rutas Regionales",
            "prob": 3, "consec": 2, "riesgo": 8,
            "categoria": CategoriaRiesgo.LOGISTICO
        },
        {
            "tag": "77-DI-CU", "evento": "Restriccion capacidad puente Los Palos",
            "proceso": "Distribucion", "locacion": "Rutas Regionales",
            "prob": 3, "consec": 2, "riesgo": 8,
            "categoria": CategoriaRiesgo.LOGISTICO
        },
        
        # Bajos (factor ≤ 5)
        {
            "tag": "5-AP-MA", "evento": "Contaminacion ambiental",
            "proceso": "Aprovisionamiento Cabo Negro", "locacion": "Cabo Negro",
            "prob": 1, "consec": 1, "riesgo": 1,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "14-SM-CU", "evento": "Averia gruesa",
            "proceso": "Suministro Maritimo", "locacion": "Nave Don Gonzalo",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "19-AP-CU", "evento": "Mantenimiento estanque",
            "proceso": "Aprovisionamiento Refineria Biobio", "locacion": "Refineria Biobio",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "20-AP-CU", "evento": "Falla Patio de Carga",
            "proceso": "Aprovisionamiento Refineria Biobio", "locacion": "Refineria Biobio",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "21-AP-CU", "evento": "Contaminacion ambiental",
            "proceso": "Aprovisionamiento Refineria Biobio", "locacion": "Refineria Biobio",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "22-AP-CU", "evento": "Mantenimiento estanque",
            "proceso": "Aprovisionamiento Planta Pureo", "locacion": "Planta Pureo",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "23-AP-CU", "evento": "Falla Patio de Carga",
            "proceso": "Aprovisionamiento Planta Pureo", "locacion": "Planta Pureo",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "24-AP-CU", "evento": "Contaminacion ambiental",
            "proceso": "Aprovisionamiento Planta Pureo", "locacion": "Planta Pureo",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.REGULATORIO
        },
        {
            "tag": "25-AP-CU", "evento": "Accidente / Incendio",
            "proceso": "Aprovisionamiento Planta Pureo", "locacion": "Planta Pureo",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "26-AP-CU", "evento": "Falla planta separadora de gas",
            "proceso": "Aprovisionamiento Cabo Negro", "locacion": "Cabo Negro",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "50-ST-CU", "evento": "Cortes de ruta por conflicto social",
            "proceso": "Suministro Terrestre Ruta Origen Pureo", "locacion": "Ruta Pureo",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.SOCIAL
        },
        {
            "tag": "51-ST-CU", "evento": "Nevadas / Cierre cruce fronterizo",
            "proceso": "Suministro Terrestre Ruta Origen Pureo", "locacion": "Cruce Fronterizo",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "53-ST-CU", "evento": "Nevadas / Cierre cruce fronterizo",
            "proceso": "Suministro Terrestre Ruta Origen Pureo", "locacion": "Cruce Fronterizo",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "54-ST-CU", "evento": "Aluviones",
            "proceso": "Suministro Terrestre Ruta Origen Pureo", "locacion": "Ruta Pureo",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.CLIMATICO
        },
        {
            "tag": "55-ST-CU", "evento": "Accidente / Incendio",
            "proceso": "Suministro Terrestre Ruta Origen Pureo", "locacion": "Ruta Pureo",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "60-ST-CU", "evento": "Accidente / Incendio",
            "proceso": "Suministro Terrestre Neuquen", "locacion": "Ruta Neuquen",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "61-ST-CU", "evento": "Cortes de ruta por conflicto social",
            "proceso": "Suministro Terrestre Cabo Negro", "locacion": "Ruta Cabo Negro",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.SOCIAL
        },
        {
            "tag": "65-ST-CU", "evento": "Accidente / Incendio",
            "proceso": "Suministro Terrestre Cabo Negro", "locacion": "Ruta Cabo Negro",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "66-ST-CU", "evento": "Accidente / Incendio",
            "proceso": "Suministro Terrestre T. Aereo Balmaceda", "locacion": "Ruta Balmaceda",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "67-ST-CU", "evento": "Falla de mantenimiento",
            "proceso": "Suministro Terrestre Camiones", "locacion": "Camiones",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "68-ST-CU", "evento": "Accidente / Incendio",
            "proceso": "Suministro Terrestre Camiones", "locacion": "Camiones",
            "prob": 2, "consec": 2, "riesgo": 5,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "69-RC-CU", "evento": "Accidente / Incendio",
            "proceso": "Retail Combustible EESS", "locacion": "EESS",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.OPERACIONAL
        },
        {
            "tag": "70-RG-CU", "evento": "Accidente / Incendio",
            "proceso": "Retail GLP", "locacion": "Punto Distribucion GLP",
            "prob": 1, "consec": 2, "riesgo": 3,
            "categoria": CategoriaRiesgo.OPERACIONAL
        }
    ]
    
    # Procesar todos los riesgos y crear perfiles
    todos_riesgos = riesgos_alto + riesgos_significativo + riesgos_mediano_bajo
    
    for riesgo_data in todos_riesgos:
        # Mapear nivel de clasificación a severidad
        if riesgo_data["riesgo"] >= 16:
            severidad = SeveridadDisrupcion.CRITICA
        elif riesgo_data["riesgo"] >= 12:
            severidad = SeveridadDisrupcion.ALTA  
        elif riesgo_data["riesgo"] >= 6:
            severidad = SeveridadDisrupcion.MEDIA
        else:
            severidad = SeveridadDisrupcion.BAJA
        
        # Determinar targets basado en el proceso
        targets = self._determinar_targets_segun_proceso(riesgo_data["proceso"])
        
        # Calcular distribuciones basadas en probabilidad y consecuencia reales
        distribuciones = self._calcular_distribuciones_reales(
            riesgo_data["prob"], 
            riesgo_data["consec"],
            riesgo_data["categoria"]
        )
        
        # Crear perfil de riesgo
        perfil = PerfilRiesgo(
            codigo=riesgo_data["tag"],
            nombre=riesgo_data["evento"],
            categoria=riesgo_data["categoria"],
            severidad_base=severidad,
            descripcion=f"{riesgo_data['evento']} - {riesgo_data['proceso']} en {riesgo_data['locacion']}",
            targets_permitidos=targets,
            parametros_distribucion=distribuciones,
            efectos_secundarios=[],
            dependencies=[]
        )
        
        self._registrar_riesgo(perfil)

def _determinar_targets_segun_proceso(self, proceso: str) -> Set[str]:
    """Mapea procesos del estudio a targets de simulación."""
    mapeo_targets = {
        # Aprovisionamiento -> Planta
        "aprovisionamiento": {"PlantaAlmacenamiento"},
        "planta almac": {"PlantaAlmacenamiento"}, 
        "puerto maritimo": {"PlantaAlmacenamiento"},
        
        # Suministro/Distribucion -> Camiones
        "suministro terrestre": {"Camion"},
        "suministro maritimo": {"PlantaAlmacenamiento"},
        "distribucion": {"Camion"},
        
        # Control/Retail -> Sistema completo
        "control autoridad": {"PlantaAlmacenamiento", "Camion"},
        "retail": {"NodoDemanda"}
    }
    
    proceso_lower = proceso.lower()
    
    for key, targets in mapeo_targets.items():
        if key in proceso_lower:
            return targets
    
    # Default: afecta a todo el sistema
    return {"PlantaAlmacenamiento", "Camion", "NodoDemanda"}

def _calcular_distribuciones_reales(self, probabilidad: int, consecuencia: int, categoria: CategoriaRiesgo) -> Dict[str, Dict[str, float]]:
    """Calcula distribuciones basadas en datos reales del estudio."""
    
    # Factor de probabilidad: mayor probabilidad = menor tiempo entre arribos
    factor_prob = {1: 8760, 2: 4380, 3: 2190, 4: 1095, 5: 365}  # Horas por año
    tiempo_base_arribo = factor_prob[probabilidad]
    
    # Factor de consecuencia: mayor consecuencia = mayor duración
    factor_consec = {1: 1, 2: 4, 3: 12, 4: 24, 5: 72}  # Horas base
    duracion_base = factor_consec[consecuencia]
    
    # Ajustes por categoría de riesgo
    ajustes_categoria = {
        CategoriaRiesgo.CLIMATICO: {"variabilidad_tba": 0.5, "variabilidad_dur": 0.8},
        CategoriaRiesgo.OPERACIONAL: {"variabilidad_tba": 0.3, "variabilidad_dur": 0.6},
        CategoriaRiesgo.SOCIAL: {"variabilidad_tba": 0.7, "variabilidad_dur": 1.2},
        CategoriaRiesgo.TECNICO: {"variabilidad_tba": 0.4, "variabilidad_dur": 0.5},
        CategoriaRiesgo.LOGISTICO: {"variabilidad_tba": 0.6, "variabilidad_dur": 0.7},
        CategoriaRiesgo.REGULATORIO: {"variabilidad_tba": 0.2, "variabilidad_dur": 2.0},
        CategoriaRiesgo.ECONOMICO: {"variabilidad_tba": 0.8, "variabilidad_dur": 1.5}
    }
    
    ajuste = ajustes_categoria.get(categoria, {"variabilidad_tba": 0.5, "variabilidad_dur": 0.8})
    
    return {
        "tba": {
            "tipo": "exponential",
            "parametros": {"scale": tiempo_base_arribo * ajuste["variabilidad_tba"]}
        },
        "duracion": {
            "tipo": "lognormal", 
            "parametros": {
                "mu": np.log(duracion_base),
                "sigma": ajuste["variabilidad_dur"]
            }
        }
    }

logger.info(f"Catálogo de riesgos real cargado: 77 riesgos del estudio de Aysén")