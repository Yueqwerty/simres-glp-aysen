"""
Sistema avanzado de eventos y disrupciones para simulación de resiliencia.
Implementa patrones Strategy, State y Chain of Responsibility para manejo robusto de 77 tipos de disrupciones.
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Generator, List, Optional, Set, Type, Union

import numpy as np
import simpy
from numpy.random import Generator as NPGenerator

from .entidades import DistribucionEstocastica, EntidadBase, EstadoEntidad, EventoSistema, TipoEvento

logger = logging.getLogger(__name__)


class CategoriaRiesgo(Enum):
    """Categorías principales de riesgos identificados."""
    CLIMATICO = "climatico"
    OPERACIONAL = "operacional"
    SOCIAL = "social"
    TECNICO = "tecnico"
    LOGISTICO = "logistico"
    REGULATORIO = "regulatorio"
    ECONOMICO = "economico"


class SeveridadDisrupcion(Enum):
    """Niveles de severidad de disrupciones."""
    BAJA = 1
    MEDIA = 2
    ALTA = 3
    CRITICA = 4


class EstadoDisrupcion(Enum):
    """Estados posibles de una disrupción."""
    INACTIVA = auto()
    PREPARANDO = auto()
    ACTIVA = auto()
    RECUPERANDO = auto()
    FINALIZADA = auto()


@dataclass(frozen=True)
class PerfilRiesgo:
    """Perfil inmutable que define las características de un riesgo específico."""
    codigo: str
    nombre: str
    categoria: CategoriaRiesgo
    severidad_base: SeveridadDisrupcion
    descripcion: str
    targets_permitidos: Set[str]
    parametros_distribucion: Dict[str, Dict[str, float]]
    efectos_secundarios: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validación post-inicialización."""
        if not self.codigo or not self.nombre:
            raise ValueError("Código y nombre son requeridos")
        
        if not self.targets_permitidos:
            raise ValueError("Debe especificar al menos un target permitido")


class RegistroRiesgos:
    """
    Registro central de los 77 tipos de riesgos identificados.
    Implementa patrón Singleton con carga lazy y cache inteligente.
    """
    
    _instance: Optional[RegistroRiesgos] = None
    _initialized: bool = False
    
    def __new__(cls) -> RegistroRiesgos:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._riesgos: Dict[str, PerfilRiesgo] = {}
            self._riesgos_por_categoria: Dict[CategoriaRiesgo, List[str]] = {}
            self._dependencias: Dict[str, List[str]] = {}
            self._cargar_catalogo_riesgos()
            RegistroRiesgos._initialized = True
    
    def _cargar_catalogo_riesgos(self) -> None:
        """Carga el catálogo completo de 77 riesgos identificados."""
        
        # Riesgos Climáticos (15 tipos)
        riesgos_climaticos = [
            ("CLIM_001", "Temporal de Viento Severo", {"tba": {"tipo": "exponential", "parametros": {"scale": 168.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.0, "scale": 8.0}}}),
            ("CLIM_002", "Lluvia Torrencial", {"tba": {"tipo": "exponential", "parametros": {"scale": 72.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 1.5, "sigma": 0.8}}}),
            ("CLIM_003", "Nieve Intensa", {"tba": {"tipo": "exponential", "parametros": {"scale": 240.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 3.0, "scale": 12.0}}}),
            ("CLIM_004", "Hielo en Rutas", {"tba": {"tipo": "exponential", "parametros": {"scale": 120.0}}, "duracion": {"tipo": "uniform", "parametros": {"low": 4.0, "high": 24.0}}}),
            ("CLIM_005", "Niebla Densa", {"tba": {"tipo": "exponential", "parametros": {"scale": 48.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 6.0, "desviacion": 2.0}}}),
            ("CLIM_006", "Vendaval", {"tba": {"tipo": "exponential", "parametros": {"scale": 336.0}}, "duracion": {"tipo": "weibull", "parametros": {"a": 2.0, "scale": 12.0}}}),
            ("CLIM_007", "Granizada", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 1.5, "scale": 2.0}}}),
            ("CLIM_008", "Helada Extrema", {"tba": {"tipo": "exponential", "parametros": {"scale": 168.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 8.0, "desviacion": 3.0}}}),
            ("CLIM_009", "Aluvion", {"tba": {"tipo": "exponential", "parametros": {"scale": 8760.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.0, "sigma": 1.0}}}),
            ("CLIM_010", "Deslizamiento por Lluvia", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.5, "scale": 24.0}}}),
            ("CLIM_011", "Inundación Localizada", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.0, "sigma": 0.6}}}),
            ("CLIM_012", "Sequia Operacional", {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 4.0, "sigma": 0.8}}}),
            ("CLIM_013", "Tormenta Electrica", {"tba": {"tipo": "exponential", "parametros": {"scale": 168.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 1.8, "scale": 4.0}}}),
            ("CLIM_014", "Cambio Climatico Abrupto", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.5, "sigma": 1.2}}}),
            ("CLIM_015", "Microrafaga", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 1.2, "scale": 1.5}}})
        ]
        
        for codigo, nombre, distribuciones in riesgos_climaticos:
            self._registrar_riesgo(PerfilRiesgo(
                codigo=codigo,
                nombre=nombre,
                categoria=CategoriaRiesgo.CLIMATICO,
                severidad_base=SeveridadDisrupcion.MEDIA,
                descripcion=f"Evento climatico: {nombre}",
                targets_permitidos={"Camion", "Ruta", "PlantaAlmacenamiento"},
                parametros_distribucion=distribuciones
            ))
        
        # Riesgos Operacionales (20 tipos)
        riesgos_operacionales = [
            ("OPER_001", "Falla Mecánica Camión", {"tba": {"tipo": "exponential", "parametros": {"scale": 240.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.0, "sigma": 0.8}}}),
            ("OPER_002", "Falla Sistema Carga", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.0, "scale": 6.0}}}),
            ("OPER_003", "Derrame Producto", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.5, "sigma": 0.6}}}),
            ("OPER_004", "Falla Bomba Transferencia", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 3.0, "scale": 4.0}}}),
            ("OPER_005", "Error Operador", {"tba": {"tipo": "exponential", "parametros": {"scale": 168.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 2.0, "desviacion": 1.0}}}),
            ("OPER_006", "Mantenimiento No Programado", {"tba": {"tipo": "exponential", "parametros": {"scale": 336.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.8, "sigma": 0.7}}}),
            ("OPER_007", "Falla Instrumentación", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.5, "scale": 3.0}}}),
            ("OPER_008", "Contaminación Producto", {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.2, "sigma": 1.0}}}),
            ("OPER_009", "Sobrecarga Operacional", {"tba": {"tipo": "exponential", "parametros": {"scale": 480.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 4.0, "desviacion": 1.5}}}),
            ("OPER_010", "Falla Sistema Control", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.3, "sigma": 0.9}}}),
            ("OPER_011", "Accidente Laboral", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 4.0, "scale": 8.0}}}),
            ("OPER_012", "Fuga Gas", {"tba": {"tipo": "exponential", "parametros": {"scale": 8760.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.8, "sigma": 1.2}}}),
            ("OPER_013", "Corrosion Equipos", {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 4.5, "sigma": 1.5}}}),
            ("OPER_014", "Falla Válvulas Seguridad", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 3.0, "scale": 12.0}}}),
            ("OPER_015", "Error Procedimiento", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 6.0, "desviacion": 2.0}}}),
            ("OPER_016", "Fatiga Operador", {"tba": {"tipo": "exponential", "parametros": {"scale": 168.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 1.5, "scale": 8.0}}}),
            ("OPER_017", "Falla Comunicaciones", {"tba": {"tipo": "exponential", "parametros": {"scale": 480.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 1.8, "sigma": 0.6}}}),
            ("OPER_018", "Sobrepresión Sistema", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.8, "scale": 4.0}}}),
            ("OPER_019", "Pérdida Calibración", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 12.0, "desviacion": 4.0}}}),
            ("OPER_020", "Falla Backup Sistemas", {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.0, "sigma": 1.0}}})
        ]
        
        for codigo, nombre, distribuciones in riesgos_operacionales:
            self._registrar_riesgo(PerfilRiesgo(
                codigo=codigo,
                nombre=nombre,
                categoria=CategoriaRiesgo.OPERACIONAL,
                severidad_base=SeveridadDisrupcion.ALTA,
                descripcion=f"Riesgo operacional: {nombre}",
                targets_permitidos={"Camion", "PlantaAlmacenamiento"},
                parametros_distribucion=distribuciones
            ))
        
        # Riesgos Sociales (12 tipos)
        riesgos_sociales = [
            ("SOC_001", "Paro Transportistas", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.5, "sigma": 1.2}}}),
            ("SOC_002", "Bloqueo Ruta", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.0, "scale": 12.0}}}),
            ("SOC_003", "Manifestación Civil", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.0, "sigma": 0.8}}}),
            ("SOC_004", "Conflicto Laboral", {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 4.0, "sigma": 1.5}}}),
            ("SOC_005", "Problema Comunitario", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 3.0, "scale": 24.0}}}),
            ("SOC_006", "Vandalismo", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 8.0, "desviacion": 4.0}}}),
            ("SOC_007", "Robo Combustible", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 1.5, "sigma": 0.5}}}),
            ("SOC_008", "Protesta Ambiental", {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.8, "sigma": 1.3}}}),
            ("SOC_009", "Huelga Operadores", {"tba": {"tipo": "exponential", "parametros": {"scale": 8760.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 4.2, "sigma": 1.8}}}),
            ("SOC_010", "Conflicto Sindical", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 4.0, "scale": 18.0}}}),
            ("SOC_011", "Tension Social Regional", {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 5.0, "sigma": 2.0}}}),
            ("SOC_012", "Inseguridad Ciudadana", {"tba": {"tipo": "exponential", "parametros": {"scale": 168.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 1.5, "scale": 4.0}}})
        ]
        
        for codigo, nombre, distribuciones in riesgos_sociales:
            self._registrar_riesgo(PerfilRiesgo(
                codigo=codigo,
                nombre=nombre,
                categoria=CategoriaRiesgo.SOCIAL,
                severidad_base=SeveridadDisrupcion.ALTA,
                descripcion=f"Riesgo social: {nombre}",
                targets_permitidos={"Camion", "Ruta", "PlantaAlmacenamiento"},
                parametros_distribucion=distribuciones
            ))
        
        # Continuar con el resto de categorías...
        self._cargar_riesgos_restantes()
    
    def _cargar_riesgos_restantes(self) -> None:
        """Carga las categorías restantes de riesgos."""
        
        # Riesgos Técnicos (10 tipos)
        riesgos_tecnicos = [
            ("TEC_001", "Falla Eléctrica", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.2, "sigma": 0.7}}}),
            ("TEC_002", "Corte Suministro Eléctrico", {"tba": {"tipo": "exponential", "parametros": {"scale": 480.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.0, "scale": 6.0}}}),
            ("TEC_003", "Falla Sistema IT", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 1.8, "sigma": 0.6}}}),
            ("TEC_004", "Cyber Ataque", {"tba": {"tipo": "exponential", "parametros": {"scale": 8760.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.0, "sigma": 1.5}}}),
            ("TEC_005", "Falla Telecomunicaciones", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.5, "scale": 8.0}}}),
            ("TEC_006", "Obsolescencia Tecnológica", {"tba": {"tipo": "exponential", "parametros": {"scale": 17520.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 5.0, "sigma": 2.0}}}),
            ("TEC_007", "Incompatibilidad Sistemas", {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 3.0, "scale": 24.0}}}),
            ("TEC_008", "Pérdida Datos", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.8, "sigma": 1.0}}}),
            ("TEC_009", "Falla Red Comunicaciones", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 4.0, "desviacion": 2.0}}}),
            ("TEC_010", "Error Software", {"tba": {"tipo": "exponential", "parametros": {"scale": 480.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 1.8, "scale": 2.0}}})
        ]
        
        for codigo, nombre, distribuciones in riesgos_tecnicos:
            self._registrar_riesgo(PerfilRiesgo(
                codigo=codigo,
                nombre=nombre,
                categoria=CategoriaRiesgo.TECNICO,
                severidad_base=SeveridadDisrupcion.MEDIA,
                descripcion=f"Riesgo técnico: {nombre}",
                targets_permitidos={"PlantaAlmacenamiento", "Camion"},
                parametros_distribucion=distribuciones
            ))
        
        # Riesgos Logísticos (10 tipos)
        riesgos_logisticos = [
            ("LOG_001", "Congestión Tráfico", {"tba": {"tipo": "exponential", "parametros": {"scale": 24.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 2.0, "desviacion": 1.0}}}),
            ("LOG_002", "Cierre Temporal Ruta", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.0, "scale": 12.0}}}),
            ("LOG_003", "Retraso Proveedor", {"tba": {"tipo": "exponential", "parametros": {"scale": 168.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.0, "sigma": 0.8}}}),
            ("LOG_004", "Problema Coordinación", {"tba": {"tipo": "exponential", "parametros": {"scale": 480.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 4.0, "desviacion": 2.0}}}),
            ("LOG_005", "Escasez Conductores", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.0, "sigma": 1.2}}}),
            ("LOG_006", "Falta Repuestos", {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 3.0, "scale": 16.0}}}),
            ("LOG_007", "Problema Almacenamiento", {"tba": {"tipo": "exponential", "parametros": {"scale": 1440.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 2.5, "sigma": 0.9}}}),
            ("LOG_008", "Deficiencia Planificación", {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.0, "scale": 8.0}}}),
            ("LOG_009", "Capacidad Insuficiente", {"tba": {"tipo": "exponential", "parametros": {"scale": 336.0}}, "duracion": {"tipo": "normal", "parametros": {"media": 12.0, "desviacion": 6.0}}}),
            ("LOG_010", "Error Programación", {"tba": {"tipo": "exponential", "parametros": {"scale": 240.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 1.5, "sigma": 0.5}}})
        ]
        
        for codigo, nombre, distribuciones in riesgos_logisticos:
            self._registrar_riesgo(PerfilRiesgo(
                codigo=codigo,
                nombre=nombre,
                categoria=CategoriaRiesgo.LOGISTICO,
                severidad_base=SeveridadDisrupcion.MEDIA,
                descripcion=f"Riesgo logístico: {nombre}",
                targets_permitidos={"Camion", "PlantaAlmacenamiento"},
                parametros_distribucion=distribuciones
            ))
        
        # Riesgos Regulatorios (5 tipos) y Económicos (5 tipos)
        otros_riesgos = [
            ("REG_001", "Cambio Normativa", CategoriaRiesgo.REGULATORIO, {"tba": {"tipo": "exponential", "parametros": {"scale": 8760.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 4.5, "sigma": 1.8}}}),
            ("REG_002", "Inspección Regulatoria", CategoriaRiesgo.REGULATORIO, {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.0, "scale": 24.0}}}),
            ("REG_003", "Sanción Operativa", CategoriaRiesgo.REGULATORIO, {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 4.0, "sigma": 2.0}}}),
            ("REG_004", "Restricción Ambiental", CategoriaRiesgo.REGULATORIO, {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 3.0, "scale": 48.0}}}),
            ("REG_005", "Licencia Suspendida", CategoriaRiesgo.REGULATORIO, {"tba": {"tipo": "exponential", "parametros": {"scale": 17520.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 5.5, "sigma": 2.5}}}),
            ("ECO_001", "Crisis Financiera", CategoriaRiesgo.ECONOMICO, {"tba": {"tipo": "exponential", "parametros": {"scale": 17520.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 6.0, "sigma": 2.0}}}),
            ("ECO_002", "Volatilidad Precios", CategoriaRiesgo.ECONOMICO, {"tba": {"tipo": "exponential", "parametros": {"scale": 720.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 2.0, "scale": 168.0}}}),
            ("ECO_003", "Problema Liquidez", CategoriaRiesgo.ECONOMICO, {"tba": {"tipo": "exponential", "parametros": {"scale": 2160.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 3.5, "sigma": 1.5}}}),
            ("ECO_004", "Inflación Costos", CategoriaRiesgo.ECONOMICO, {"tba": {"tipo": "exponential", "parametros": {"scale": 4320.0}}, "duracion": {"tipo": "lognormal", "parametros": {"mu": 4.8, "sigma": 2.2}}}),
            ("ECO_005", "Devaluación Moneda", CategoriaRiesgo.ECONOMICO, {"tba": {"tipo": "exponential", "parametros": {"scale": 8760.0}}, "duracion": {"tipo": "gamma", "parametros": {"shape": 4.0, "scale": 720.0}}})
        ]
        
        for codigo, nombre, categoria, distribuciones in otros_riesgos:
            self._registrar_riesgo(PerfilRiesgo(
                codigo=codigo,
                nombre=nombre,
                categoria=categoria,
                severidad_base=SeveridadDisrupcion.ALTA,
                descripcion=f"Riesgo {categoria.value}: {nombre}",
                targets_permitidos={"Camion", "PlantaAlmacenamiento", "Sistema"},
                parametros_distribucion=distribuciones
            ))
        
        logger.info(f"Catálogo de riesgos cargado: {len(self._riesgos)} tipos de riesgos")
    
    def _registrar_riesgo(self, perfil: PerfilRiesgo) -> None:
        """Registra un perfil de riesgo en el catálogo."""
        self._riesgos[perfil.codigo] = perfil
        
        # Indexar por categoría
        if perfil.categoria not in self._riesgos_por_categoria:
            self._riesgos_por_categoria[perfil.categoria] = []
        self._riesgos_por_categoria[perfil.categoria].append(perfil.codigo)
        
        # Procesar dependencias
        if perfil.dependencies:
            self._dependencias[perfil.codigo] = perfil.dependencies
    
    def get_riesgo(self, codigo: str) -> Optional[PerfilRiesgo]:
        """Obtiene un perfil de riesgo por código."""
        return self._riesgos.get(codigo)
    
    def get_riesgos_categoria(self, categoria: CategoriaRiesgo) -> List[PerfilRiesgo]:
        """Obtiene todos los riesgos de una categoría."""
        codigos = self._riesgos_por_categoria.get(categoria, [])
        return [self._riesgos[codigo] for codigo in codigos]
    
    def get_todos_codigos(self) -> List[str]:
        """Obtiene todos los códigos de riesgos."""
        return list(self._riesgos.keys())
    
    def validar_dependencias(self, codigo: str, activos: Set[str]) -> bool:
        """Valida si las dependencias de un riesgo están satisfechas."""
        dependencias = self._dependencias.get(codigo, [])
        return all(dep in activos for dep in dependencias)


class Disrupcion(ABC):
    """
    Clase base abstracta para todas las disrupciones del sistema.
    Implementa el patrón Template Method y State Machine.
    """
    
    def __init__(self,
                 env: simpy.Environment,
                 perfil: PerfilRiesgo,
                 target: EntidadBase,
                 rng: NPGenerator,
                 config: Dict[str, Any]):
        self.env = env
        self.perfil = perfil
        self.target = target
        self.rng = rng
        self.config = config
        
        # Estado de la disrupción
        self.estado = EstadoDisrupcion.INACTIVA
        self.activa = True
        self.timestamp_inicio: Optional[float] = None
        self.timestamp_fin: Optional[float] = None
        
        # Distribuciones estocásticas
        self._init_distributions()
        
        # Métricas de la disrupción
        self.metricas = {
            'activaciones_total': 0,
            'tiempo_total_activa': 0.0,
            'impacto_acumulado': 0.0,
            'recuperaciones_exitosas': 0,
            'fallas_recuperacion': 0
        }
        
        # Proceso principal
        self.proceso = env.process(self.run())
    
    def _init_distributions(self) -> None:
        """Inicializa las distribuciones estocásticas de la disrupción."""
        params = self.perfil.parametros_distribucion
        
        self.dist_tba = DistribucionEstocastica(
            self.rng,
            params['tba']['tipo'],
            params['tba']['parametros']
        )
        
        self.dist_duracion = DistribucionEstocastica(
            self.rng,
            params['duracion']['tipo'],
            params['duracion']['parametros']
        )
    
    def run(self) -> Generator:
        """Proceso principal de la disrupción (Template Method)."""
        while self.activa:
            try:
                # Esperar tiempo hasta próxima activación
                tiempo_espera = self.dist_tba.sample()
                yield self.env.timeout(tiempo_espera)
                
                # Verificar si se debe activar
                if self._debe_activarse():
                    yield from self._ciclo_disrupcion()
                
            except simpy.Interrupt as interrupt:
                logger.info(f"Disrupción {self.perfil.codigo} interrumpida: {interrupt.cause}")
                yield from self._manejar_interrupcion(interrupt)
            except Exception as e:
                logger.error(f"Error en disrupción {self.perfil.codigo}: {e}")
                yield self.env.timeout(1.0)
    
    def _ciclo_disrupcion(self) -> Generator:
        """Ciclo completo de una disrupción."""
        # Fase 1: Preparación
        self.estado = EstadoDisrupcion.PREPARANDO
        yield from self._preparar_activacion()
        
        # Fase 2: Activación
        self.estado = EstadoDisrupcion.ACTIVA
        self.timestamp_inicio = self.env.now
        duracion = self.dist_duracion.sample()
        
        yield from self._activar_disrupcion()
        
        # Fase 3: Mantener activa
        yield self.env.timeout(duracion)
        
        # Fase 4: Recuperación
        self.estado = EstadoDisrupcion.RECUPERANDO
        yield from self._iniciar_recuperacion()
        
        # Fase 5: Finalización
        self.estado = EstadoDisrupcion.FINALIZADA
        self.timestamp_fin = self.env.now
        self._actualizar_metricas(duracion)
        
        yield from self._finalizar_disrupcion()
        
        self.estado = EstadoDisrupcion.INACTIVA
    
    @abstractmethod
    def _debe_activarse(self) -> bool:
        """Determina si la disrupción debe activarse."""
        pass
    
    @abstractmethod
    def _preparar_activacion(self) -> Generator:
        """Prepara la activación de la disrupción."""
        pass
    
    @abstractmethod
    def _activar_disrupcion(self) -> Generator:
        """Aplica el efecto de la disrupción."""
        pass
    
    @abstractmethod
    def _iniciar_recuperacion(self) -> Generator:
        """Inicia el proceso de recuperación."""
        pass
    
    @abstractmethod
    def _finalizar_disrupcion(self) -> Generator:
        """Finaliza la disrupción y limpia efectos."""
        pass
    
    def _manejar_interrupcion(self, interrupt: simpy.Interrupt) -> Generator:
        """Maneja interrupciones externas."""
        logger.info(f"Manejando interrupción en {self.perfil.codigo}")
        yield self.env.timeout(0.1)
    
    def _actualizar_metricas(self, duracion: float) -> None:
        """Actualiza métricas de la disrupción."""
        self.metricas['activaciones_total'] += 1
        self.metricas['tiempo_total_activa'] += duracion
        
        if self.estado == EstadoDisrupcion.FINALIZADA:
            self.metricas['recuperaciones_exitosas'] += 1
        else:
            self.metricas['fallas_recuperacion'] += 1


class DisrupcionClimatica(Disrupcion):
    """Disrupción climática que afecta principalmente el transporte."""
    
    def _debe_activarse(self) -> bool:
        """Los eventos climáticos se activan probabilísticamente."""
        # Probabilidad base ajustada por estacionalidad (simplificada)
        prob_base = 0.8
        factor_estacional = 1.0 + 0.3 * np.sin(2 * np.pi * self.env.now / (24 * 365))
        return self.rng.random() < (prob_base * factor_estacional)
    
    def _preparar_activacion(self) -> Generator:
        """Preparación para evento climático."""
        self._emit_event(TipoEvento.INICIO_DISRUPCION, {
            'tipo_disrupcion': self.perfil.codigo,
            'severidad': self.perfil.severidad_base.value,
            'target': self.target.entity_id
        })
        yield self.env.timeout(0.1)  # Tiempo de detección
    
    def _activar_disrupcion(self) -> Generator:
        """Aplica efectos climáticos."""
        if hasattr(self.target, 'factor_disrupcion_climatica'):
            # Aumentar tiempo de viaje por condiciones climáticas
            factor_impacto = 1.5 + self.rng.exponential(0.5)
            self.target.factor_disrupcion_climatica = factor_impacto
            
        self.metricas['impacto_acumulado'] += factor_impacto - 1.0
        yield self.env.timeout(0.0)
    
    def _iniciar_recuperacion(self) -> Generator:
        """Inicia recuperación gradual."""
        if hasattr(self.target, 'factor_disrupcion_climatica'):
            # Recuperación gradual
            tiempo_recuperacion = self.rng.exponential(2.0)
            yield self.env.timeout(tiempo_recuperacion)
    
    def _finalizar_disrupcion(self) -> Generator:
        """Finaliza efectos climáticos."""
        if hasattr(self.target, 'factor_disrupcion_climatica'):
            self.target.factor_disrupcion_climatica = 1.0
            
        self._emit_event(TipoEvento.FIN_DISRUPCION, {
            'tipo_disrupcion': self.perfil.codigo,
            'duracion_total': self.timestamp_fin - self.timestamp_inicio,
            'impacto_total': self.metricas['impacto_acumulado']
        })
        yield self.env.timeout(0.0)
    
    def _emit_event(self, tipo: TipoEvento, detalles: Dict[str, Any]) -> None:
        """Emite evento al sistema de monitoreo."""
        evento = EventoSistema(
            timestamp=self.env.now,
            tipo=tipo,
            entidad_id=f"disrupcion_{self.perfil.codigo}",
            detalles=detalles
        )
        # Propagar a observadores del target
        self.target.notify_observers(evento)


class DisrupcionOperacional(Disrupcion):
    """Disrupción operacional que afecta capacidades del sistema."""
    
    def _debe_activarse(self) -> bool:
        """Activación basada en carga operacional."""
        # Mayor probabilidad con mayor utilización
        utilizacion = getattr(self.target, 'utilizacion_actual', 0.5)
        prob_base = 0.3 * (1 + utilizacion)
        return self.rng.random() < prob_base
    
    def _preparar_activacion(self) -> Generator:
        """Preparación para falla operacional."""
        self._emit_event(TipoEvento.INICIO_DISRUPCION, {
            'tipo_disrupcion': self.perfil.codigo,
            'severidad': self.perfil.severidad_base.value,
            'target': self.target.entity_id,
            'modo_falla': self._determinar_modo_falla()
        })
        yield self.env.timeout(0.0)
    
    def _determinar_modo_falla(self) -> str:
        """Determina el modo específico de falla."""
        modos = ['degradacion', 'parada_total', 'funcionamiento_errático']
        return self.rng.choice(modos)
    
    def _activar_disrupcion(self) -> Generator:
        """Aplica falla operacional."""
        if hasattr(self.target, 'disponible'):
            # Simular indisponibilidad temporal
            with self.target.disponible.request() as req:
                yield req
                # Bloquear recurso durante la disrupción
                yield self.env.timeout(0.1)
    
    def _iniciar_recuperacion(self) -> Generator:
        """Proceso de reparación/recuperación."""
        tiempo_reparacion = self.rng.lognormal(1.5, 0.8)
        yield self.env.timeout(tiempo_reparacion)
    
    def _finalizar_disrupcion(self) -> Generator:
        """Restaura operación normal."""
        self._emit_event(TipoEvento.FIN_DISRUPCION, {
            'tipo_disrupcion': self.perfil.codigo,
            'duracion_total': self.timestamp_fin - self.timestamp_inicio,
            'modo_recuperacion': 'reparacion_completa'
        })
        yield self.env.timeout(0.0)


class DisrupcionSocial(Disrupcion):
    """Disrupción social que afecta acceso y operaciones."""
    
    def _debe_activarse(self) -> bool:
        """Activación basada en factores sociales."""
        # Probabilidad constante baja
        return self.rng.random() < 0.1
    
    def _preparar_activacion(self) -> Generator:
        """Preparación para evento social."""
        self._emit_event(TipoEvento.INICIO_DISRUPCION, {
            'tipo_disrupcion': self.perfil.codigo,
            'severidad': self.perfil.severidad_base.value,
            'target': self.target.entity_id,
            'tipo_evento_social': self.perfil.nombre
        })
        yield self.env.timeout(0.5)  # Tiempo de escalamiento
    
    def _activar_disrupcion(self) -> Generator:
        """Aplica bloqueo social."""
        if hasattr(self.target, 'acceso_bloqueado'):
            self.target.acceso_bloqueado = True
        yield self.env.timeout(0.0)
    
    def _iniciar_recuperacion(self) -> Generator:
        """Proceso de negociación/resolución."""
        tiempo_negociacion = self.rng.gamma(2.0, 12.0)
        yield self.env.timeout(tiempo_negociacion)
    
    def _finalizar_disrupcion(self) -> Generator:
        """Levanta bloqueo social."""
        if hasattr(self.target, 'acceso_bloqueado'):
            self.target.acceso_bloqueado = False
            
        self._emit_event(TipoEvento.FIN_DISRUPCION, {
            'tipo_disrupcion': self.perfil.codigo,
            'duracion_total': self.timestamp_fin - self.timestamp_inicio,
            'resolucion': 'negociacion_exitosa'
        })
        yield self.env.timeout(0.0)


class FactoriaDisrupciones:
    """Factory para creación de disrupciones según tipo."""
    
    _mapping: Dict[CategoriaRiesgo, Type[Disrupcion]] = {
        CategoriaRiesgo.CLIMATICO: DisrupcionClimatica,
        CategoriaRiesgo.OPERACIONAL: DisrupcionOperacional,  
        CategoriaRiesgo.SOCIAL: DisrupcionSocial,
        # Otros tipos utilizan DisrupcionOperacional como base
        CategoriaRiesgo.TECNICO: DisrupcionOperacional,
        CategoriaRiesgo.LOGISTICO: DisrupcionOperacional,
        CategoriaRiesgo.REGULATORIO: DisrupcionSocial,
        CategoriaRiesgo.ECONOMICO: DisrupcionOperacional
    }
    
    @classmethod
    def crear_disrupcion(cls,
                        env: simpy.Environment,
                        perfil: PerfilRiesgo,
                        target: EntidadBase,
                        rng: NPGenerator,
                        config: Dict[str, Any]) -> Disrupcion:
        """Crea una disrupción del tipo apropiado."""
        
        clase_disrupcion = cls._mapping.get(perfil.categoria, DisrupcionOperacional)
        
        return clase_disrupcion(
            env=env,
            perfil=perfil,
            target=target,
            rng=rng,
            config=config
        )


class GestorDisrupciones:
    """
    Gestor centralizado de disrupciones que orquesta el sistema completo.
    Implementa patrones Mediator y Chain of Responsibility.
    """
    
    def __init__(self, env: simpy.Environment, rng: NPGenerator):
        self.env = env
        self.rng = rng
        self.registro = RegistroRiesgos()
        
        # Estado del gestor
        self.disrupciones_activas: Dict[str, Disrupcion] = {}
        self.entidades_registradas: Dict[str, EntidadBase] = {}
        self.configuracion_riesgos: Dict[str, Dict[str, Any]] = {}
        
        # Métricas del gestor
        self.metricas = {
            'disrupciones_totales_creadas': 0,
            'disrupciones_activas_pico': 0,
            'tiempo_sistema_degradado': 0.0
        }
    
    def registrar_entidad(self, entidad: EntidadBase) -> None:
        """Registra una entidad para ser afectada por disrupciones."""
        self.entidades_registradas[entidad.entity_id] = entidad
    
    def configurar_riesgos(self, config_riesgos: Dict[str, Any]) -> None:
        """Configura qué riesgos están activos y sus parámetros."""
        self.configuracion_riesgos = config_riesgos
        
        # Crear disrupciones según configuración
        for codigo_riesgo, config_riesgo in config_riesgos.items():
            if config_riesgo.get('activo', False):
                self._crear_disrupciones_para_riesgo(codigo_riesgo, config_riesgo)
    
    def _crear_disrupciones_para_riesgo(self, codigo: str, config: Dict[str, Any]) -> None:
        """Crea instancias de disrupción para un riesgo específico."""
        perfil = self.registro.get_riesgo(codigo)
        if not perfil:
            logger.warning(f"Perfil de riesgo no encontrado: {codigo}")
            return
        
        # Determinar targets según configuración
        targets_config = config.get('targets', list(perfil.targets_permitidos))
        
        for entidad_id, entidad in self.entidades_registradas.items():
            tipo_entidad = entidad.__class__.__name__
            
            if tipo_entidad in targets_config or 'all' in targets_config:
                disrupcion = FactoriaDisrupciones.crear_disrupcion(
                    env=self.env,
                    perfil=perfil,
                    target=entidad,
                    rng=self.rng,
                    config=config
                )
                
                clave_disrupcion = f"{codigo}_{entidad_id}"
                self.disrupciones_activas[clave_disrupcion] = disrupcion
                self.metricas['disrupciones_totales_creadas'] += 1
        
        logger.info(f"Disrupciones creadas para riesgo {codigo}: {len(targets_config)} tipos de target")
    
    def get_estado_sistema(self) -> Dict[str, Any]:
        """Obtiene el estado actual del sistema de disrupciones."""
        disrupciones_activas = [
            {
                'codigo': d.perfil.codigo,
                'target': d.target.entity_id,
                'estado': d.estado.name,
                'tiempo_activa': self.env.now - d.timestamp_inicio if d.timestamp_inicio else 0
            }
            for d in self.disrupciones_activas.values()
            if d.estado != EstadoDisrupcion.INACTIVA
        ]
        
        return {
            'disrupciones_totales': len(self.disrupciones_activas),
            'disrupciones_activas': len(disrupciones_activas),
            'detalle_disrupciones_activas': disrupciones_activas,
            'metricas_gestor': self.metricas.copy()
        }
    
    def finalizar(self) -> Dict[str, Any]:
        """Finaliza todas las disrupciones y retorna métricas finales."""
        # Interrumpir todas las disrupciones activas
        for disrupcion in self.disrupciones_activas.values():
            if disrupcion.proceso.is_alive:
                disrupcion.proceso.interrupt("Simulación finalizada")
        
        # Recopilar métricas finales
        metricas_disrupciones = {}
        for clave, disrupcion in self.disrupciones_activas.items():
            metricas_disrupciones[clave] = disrupcion.metricas.copy()
        
        return {
            'metricas_gestor': self.metricas.copy(),
            'metricas_disrupciones': metricas_disrupciones,
            'estado_final': self.get_estado_sistema()
        }