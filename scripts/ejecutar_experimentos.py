"""
Orquestador avanzado de experimentos masivos para análisis de resiliencia.
Implementa paralelización inteligente, gestión de memoria y monitoreo en tiempo real.
"""
from __future__ import annotations

import json
import logging
import multiprocessing as mp
import os
import queue
import signal
import sys
import threading
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple, Union

import pandas as pd
import typer
from tqdm import tqdm

# Importar script de simulación individual
sys.path.append(str(Path(__file__).parent))
from ejecutar_simulacion import ConfiguracionSimulacion, EjecutorSimulacion

# Configuración de logging para multiprocessing
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="ejecutar_experimentos",
    help="Orquestador avanzado de experimentos de simulación masiva",
    add_completion=False
)


@dataclass
class ExperimentoJob:
    """Estructura que define un trabajo de experimento individual."""
    experiment_id: str
    config_path: Path
    output_path: Path
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: int = 0
    retries: int = 0
    max_retries: int = 3


@dataclass
class ResultadoExperimento:
    """Resultado de un experimento ejecutado."""
    experiment_id: str
    success: bool
    execution_time: float
    output_path: Optional[Path] = None
    error_message: Optional[str] = None
    metrics_summary: Dict[str, Any] = field(default_factory=dict)


class GestorRecursos:
    """
    Gestor inteligente de recursos del sistema para optimizar ejecución.
    Implementa algoritmos de balanceamiento de carga y predicción de recursos.
    """
    
    def __init__(self):
        self.cpu_count = mp.cpu_count()
        self.memory_gb = self._get_memory_gb()
        self.load_factor = 0.8  # Factor de seguridad para no saturar el sistema
        
    def _get_memory_gb(self) -> float:
        """Obtiene memoria RAM disponible en GB."""
        try:
            import psutil
            return psutil.virtual_memory().available / (1024**3)
        except ImportError:
            logger.warning("psutil no disponible, usando estimación de memoria")
            return 8.0  # Estimación conservadora
    
    def calcular_paralelismo_optimo(self, 
                                   num_experimentos: int,
                                   memoria_por_simulacion: float = 0.5) -> int:
        """
        Calcula el nivel óptimo de paralelización basado en recursos disponibles.
        
        Args:
            num_experimentos: Número total de experimentos
            memoria_por_simulacion: Memoria estimada en GB por simulación
        
        Returns:
            Número óptimo de procesos paralelos
        """
        # Limitación por CPU
        max_por_cpu = max(1, int(self.cpu_count * self.load_factor))
        
        # Limitación por memoria
        max_por_memoria = max(1, int(self.memory_gb / memoria_por_simulacion))
        
        # Usar el menor de los dos límites
        parallelism = min(max_por_cpu, max_por_memoria, num_experimentos)
        
        logger.info(f"Paralelismo calculado: {parallelism} procesos")
        logger.info(f"  - Límite por CPU ({self.cpu_count} cores): {max_por_cpu}")
        logger.info(f"  - Límite por memoria ({self.memory_gb:.1f} GB): {max_por_memoria}")
        
        return parallelism
    
    def estimar_tiempo_ejecucion(self, 
                                num_experimentos: int,
                                tiempo_promedio_por_exp: float,
                                paralelismo: int) -> float:
        """Estima tiempo total de ejecución en horas."""
        tiempo_secuencial = num_experimentos * tiempo_promedio_por_exp
        tiempo_paralelo = tiempo_secuencial / paralelismo
        overhead = tiempo_paralelo * 0.1  # 10% de overhead por coordinación
        return tiempo_paralelo + overhead


class GeneradorExperimentos:
    """
    Generador inteligente de experimentos con soporte para diseños factoriales,
    Latin Hypercube Sampling y análisis de sensibilidad.
    """
    
    def __init__(self, 
                 base_config_dir: Path,
                 output_base_dir: Path,
                 design_type: str = "full_factorial"):
        self.base_config_dir = base_config_dir
        self.output_base_dir = output_base_dir
        self.design_type = design_type
        
    def generar_experimentos(self) -> Iterator[ExperimentoJob]:
        """Genera secuencia de experimentos según el diseño especificado."""
        
        if self.design_type == "individual_configs":
            yield from self._generar_desde_configs_individuales()
        elif self.design_type == "factorial":
            yield from self._generar_factorial()
        elif self.design_type == "lhs":
            yield from self._generar_latin_hypercube()
        elif self.design_type == "sensitivity":
            yield from self._generar_analisis_sensibilidad()
        else:
            raise ValueError(f"Tipo de diseño no soportado: {self.design_type}")
    
    def _generar_desde_configs_individuales(self) -> Iterator[ExperimentoJob]:
        """Genera experimentos desde archivos de configuración individuales."""
        config_files = list(self.base_config_dir.glob("*.yaml"))
        config_files.extend(self.base_config_dir.glob("*.yml"))
        
        for i, config_file in enumerate(sorted(config_files)):
            experiment_id = f"exp_{i:04d}_{config_file.stem}"
            output_path = self.output_base_dir / f"{experiment_id}_results"
            
            yield ExperimentoJob(
                experiment_id=experiment_id,
                config_path=config_file,
                output_path=output_path,
                metadata={"source_config": config_file.name}
            )
    
    def _generar_factorial(self) -> Iterator[ExperimentoJob]:
        """Genera diseño factorial completo."""
        # Implementación simplificada - en producción sería más complejo
        base_config_file = self.base_config_dir / "base_factorial.yaml"
        if not base_config_file.exists():
            logger.error(f"Configuración base no encontrada: {base_config_file}")
            return
        
        # Factores para el diseño factorial
        factores = {
            'numero_camiones': [1, 2, 3, 4],
            'capacidad_planta': [50000, 100000, 150000],
            'nivel_critico': [0.1, 0.2, 0.3]
        }
        
        # Generar todas las combinaciones
        import itertools
        
        combinaciones = list(itertools.product(*factores.values()))
        nombres_factores = list(factores.keys())
        
        for i, combinacion in enumerate(combinaciones):
            experiment_id = f"factorial_{i:04d}"
            
            # Crear configuración modificada
            config_modificada = self._crear_config_factorial(
                base_config_file, 
                dict(zip(nombres_factores, combinacion))
            )
            
            config_path = self.base_config_dir / f"generated_{experiment_id}.yaml"
            output_path = self.output_base_dir / f"{experiment_id}_results"
            
            # Guardar configuración generada
            self._guardar_config_temporal(config_modificada, config_path)
            
            yield ExperimentoJob(
                experiment_id=experiment_id,
                config_path=config_path,
                output_path=output_path,
                metadata={
                    "design_type": "factorial",
                    "factors": dict(zip(nombres_factores, combinacion))
                }
            )
    
    def _generar_latin_hypercube(self) -> Iterator[ExperimentoJob]:
        """Genera muestreo Latin Hypercube para análisis eficiente del espacio de parámetros."""
        try:
            from scipy.stats import qmc
            import numpy as np
        except ImportError:
            logger.error("scipy requerido para Latin Hypercube Sampling")
            return
        
        # Configuración LHS
        n_samples = 100
        n_dimensions = 5  # Número de parámetros a variar
        
        sampler = qmc.LatinHypercube(d=n_dimensions, seed=42)
        samples = sampler.random(n=n_samples)
        
        # Definir rangos de parámetros
        param_ranges = {
            'duracion_simulacion': (168, 8760),  # 1 semana a 1 año
            'capacidad_camion': (15000, 30000),  # Litros
            'capacidad_planta': (80000, 200000),  # Litros
            'intervalo_demanda': (12, 48),  # Horas
            'tasa_disrupciones': (0.1, 2.0)  # Factor multiplicativo
        }
        
        base_config_file = self.base_config_dir / "base_lhs.yaml"
        if not base_config_file.exists():
            logger.error(f"Configuración base LHS no encontrada: {base_config_file}")
            return
        
        for i, sample in enumerate(samples):
            experiment_id = f"lhs_{i:04d}"
            
            # Escalar muestras a rangos de parámetros
            parametros = {}
            for j, (param_name, (min_val, max_val)) in enumerate(param_ranges.items()):
                parametros[param_name] = min_val + sample[j] * (max_val - min_val)
            
            # Crear configuración
            config_modificada = self._crear_config_lhs(base_config_file, parametros)
            
            config_path = self.base_config_dir / f"generated_lhs_{experiment_id}.yaml"
            output_path = self.output_base_dir / f"{experiment_id}_results"
            
            # Guardar configuración
            self._guardar_config_temporal(config_modificada, config_path)
            
            yield ExperimentoJob(
                experiment_id=experiment_id,
                config_path=config_path,
                output_path=output_path,
                metadata={
                    "design_type": "lhs",
                    "parameters": parametros,
                    "sample_index": i
                }
            )
    
    def _generar_analisis_sensibilidad(self) -> Iterator[ExperimentoJob]:
        """Genera experimentos para análisis de sensibilidad tipo Sobol."""
        try:
            from SALib.sample import sobol
            from SALib.util import read_param_file
        except ImportError:
            logger.error("SALib requerido para análisis de sensibilidad")
            return
        
        # Definir problema para SALib
        problem = {
            'num_vars': 4,
            'names': ['capacidad_planta', 'numero_camiones', 'nivel_critico', 'frecuencia_disrupciones'],
            'bounds': [