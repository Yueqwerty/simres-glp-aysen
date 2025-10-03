"""
Script principal de ejecución de simulaciones con arquitectura modular avanzada.
Implementa patrones Command, Factory y Builder para máxima flexibilidad.
"""
from __future__ import annotations

import json
import logging
import sys
import traceback
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd
import typer
import yaml

# Importaciones del proyecto
sys.path.append(str(Path(__file__).parent.parent))

from src.entidades import Camion, NodoDemanda, PlantaAlmacenamiento
from src.modelo import Simulacion
from src.monitores import AnalizadorRealTime, MonitorSistema

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simulation.log')
    ]
)
logger = logging.getLogger(__name__)

app = typer.Typer(
    name="ejecutar_simulacion",
    help="Ejecutor avanzado de simulaciones de cadena de suministro GLP",
    add_completion=False,
    rich_markup_mode="rich"
)


class ConfiguracionSimulacion:
    """
    Builder pattern para construcción robusta de configuración.
    Implementa validación exhaustiva y valores por defecto inteligentes.
    """
    
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.config: Dict[str, Any] = {}
        self._load_config()
        self._validate_config()
        self._enrich_config()
    
    def _load_config(self) -> None:
        """Carga configuración desde archivo YAML."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            logger.info(f"Configuración cargada desde {self.config_path}")
        except Exception as e:
            logger.error(f"Error cargando configuración: {e}")
            raise typer.Exit(1)
    
    def _validate_config(self) -> None:
        """Validación exhaustiva de configuración."""
        required_sections = ['simulacion', 'entidades', 'planta', 'demanda']
        
        for section in required_sections:
            if section not in self.config:
                raise ValueError(f"Sección requerida faltante: {section}")
        
        # Validaciones específicas
        sim_config = self.config['simulacion']
        if sim_config.get('duracion', 0) <= 0:
            raise ValueError("Duración de simulación debe ser positiva")
        
        if len(self.config.get('entidades', {})) <= 0:
            raise ValueError("Se debe definir al menos un camión en la sección 'entidades'")
        
        # Validar configuración de planta
        planta_config = self.config['planta']
        if planta_config.get('capacidad_maxima', 0) <= 0:
            raise ValueError("Capacidad máxima de planta debe ser positiva")
    
    def _enrich_config(self) -> None:
        """Enriquece configuración con valores calculados y por defecto."""
        # Valores por defecto para simulación
        sim_defaults = {
            'semilla_aleatoria': 42,
            'precision_temporal': 0.01,
            'modo_debug': False
        }
        
        for key, default_value in sim_defaults.items():
            if key not in self.config['simulacion']:
                self.config['simulacion'][key] = default_value
        
        # Enriquecimiento automático de parámetros de distribuciones
        self._auto_tune_distributions()
    
    def _auto_tune_distributions(self) -> None:
        """Auto-tuning de parámetros de distribuciones basado en configuración."""
        # Esta función podría usar ML para optimizar parámetros
        # Por ahora, aplicamos heurísticas simples
        
        entidades_config = self.config['entidades']
        for camion_id, camion_config in entidades_config.items():
            if 'distribuciones' not in camion_config:
                # Generar distribuciones por defecto basadas en capacidad
                capacidad = camion_config.get('capacidad', 20000)
                
                # Tiempo de viaje proporcional a la capacidad (camiones más grandes = más lentos)
                factor_capacidad = capacidad / 20000  # Normalizar a capacidad base
                
                camion_config['distribuciones'] = {
                    'tiempo_viaje': {
                        'tipo': 'lognormal',
                        'parametros': {
                            'mu': 2.0 + 0.1 * factor_capacidad,
                            'sigma': 0.3
                        }
                    },
                    'tiempo_carga': {
                        'tipo': 'gamma',
                        'parametros': {
                            'shape': 2.0,
                            'scale': 1.5 * factor_capacidad
                        }
                    },
                    'tiempo_descarga': {
                        'tipo': 'normal',
                        'parametros': {
                            'media': 1.0 * factor_capacidad,
                            'desviacion': 0.2
                        }
                    }
                }
    
    def get_config(self) -> Dict[str, Any]:
        """Retorna configuración validada y enriquecida."""
        return self.config.copy()


class FactoriaSimulacion:
    """
    Factory pattern para creación de componentes de simulación.
    Abstrae la complejidad de inicialización y permite extensibilidad.
    """
    
    @staticmethod
    def crear_simulacion(config: Dict[str, Any]) -> Simulacion:
        """Crea instancia de simulación completamente configurada."""
        sim_config = config['simulacion']
        
        # Crear generador de números aleatorios
        rng = np.random.default_rng(sim_config['semilla_aleatoria'])
        
        # Crear simulación base
        simulacion = Simulacion(
            duracion=sim_config['duracion'],
            rng=rng,
            config=config
        )
        
        return simulacion
    
    @staticmethod
    def crear_monitor_sistema(config: Dict[str, Any]) -> MonitorSistema:
        """Crea monitor del sistema con configuración optimizada."""
        monitor_config = config.get('monitoreo', {})
        
        return MonitorSistema(
            buffer_size=monitor_config.get('buffer_size', 1000),
            auto_flush=monitor_config.get('auto_flush', True),
            flush_interval=monitor_config.get('flush_interval', 10.0)
        )
    
    @staticmethod
    def crear_analizador_realtime(config: Dict[str, Any]) -> AnalizadorRealTime:
        """Crea analizador en tiempo real."""
        analyzer_config = config.get('analisis_realtime', {})
        
        return AnalizadorRealTime(
            ventana_analisis=analyzer_config.get('ventana_analisis', 100)
        )


class EjecutorSimulacion:
    """
    Command pattern para ejecución de simulaciones.
    Encapsula toda la lógica de ejecución con manejo robusto de errores.
    """
    
    def __init__(self, config: Dict[str, Any], output_path: Path):
        self.config = config
        self.output_path = output_path
        self.simulacion: Optional[Simulacion] = None
        self.monitor: Optional[MonitorSistema] = None
        self.analizador: Optional[AnalizadorRealTime] = None
        self.resultados: Dict[str, Any] = {}
    
    def preparar(self) -> None:
        """Prepara todos los componentes para la ejecución."""
        logger.info("Preparando simulación...")
        
        # Crear componentes usando factory
        self.simulacion = FactoriaSimulacion.crear_simulacion(self.config)
        self.monitor = FactoriaSimulacion.crear_monitor_sistema(self.config)
        self.analizador = FactoriaSimulacion.crear_analizador_realtime(self.config)
        
        # Configurar observadores
        self._configurar_observadores()
        
        logger.info("Simulación preparada exitosamente")
    
    def _configurar_observadores(self) -> None:
        """Configura el sistema de observadores."""
        if not (self.simulacion and self.monitor):
            raise RuntimeError("Componentes no inicializados")
        
        # Registrar monitor como observador de todas las entidades
        for entidad in self.simulacion.get_entidades():
            entidad.add_observer(self.monitor)
    
    def ejecutar(self) -> None:
        """Ejecuta la simulación con manejo completo de errores."""
        if not self.simulacion:
            raise RuntimeError("Simulación no preparada")
        
        logger.info("Iniciando ejecución de simulación...")
        
        try:
            # Ejecutar simulación
            inicio_ejecucion = pd.Timestamp.now()
            self.simulacion.ejecutar()
            fin_ejecucion = pd.Timestamp.now()
            
            # Recopilar resultados
            self._recopilar_resultados(inicio_ejecucion, fin_ejecucion)
            
            logger.info("Simulación ejecutada exitosamente")
            
        except Exception as e:
            logger.error(f"Error durante ejecución: {e}")
            logger.error(traceback.format_exc())
            raise
    
    def _recopilar_resultados(self, inicio: pd.Timestamp, fin: pd.Timestamp) -> None:
        """Recopila todos los resultados de la simulación."""
        # Datos del monitor
        datos_monitor = self.monitor.get_datos_simulacion()
        
        # Métricas de entidades
        metricas_entidades = {}
        for entidad in self.simulacion.get_entidades():
            if hasattr(entidad, 'get_metricas'):
                metricas_entidades[entidad.entity_id] = entidad.get_metricas()
        
        # Metadatos de ejecución
        metadatos = {
            'configuracion': self.config,
            'tiempo_inicio': inicio.isoformat(),
            'tiempo_fin': fin.isoformat(),
            'duracion_real_segundos': (fin - inicio).total_seconds(),
            'version_simulacion': '1.0.0'
        }
        
        self.resultados = {
            'metadatos': metadatos,
            'eventos': datos_monitor['eventos'],
            'metricas_sistema': datos_monitor['metricas'],
            'metricas_entidades': metricas_entidades,
            'agregaciones': {
                'temporal': datos_monitor['agregacion_temporal'],
                'por_tipo': datos_monitor['agregacion_por_tipo']
            },
            'stats_monitoreo': datos_monitor['stats_monitor']
        }
    
    def guardar_resultados(self) -> None:
        """Guarda resultados en múltiples formatos."""
        if not self.resultados:
            raise RuntimeError("No hay resultados para guardar")
        
        logger.info(f"Guardando resultados en {self.output_path}")
        
        try:
            # Crear directorio si no existe
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Guardar DataFrame de eventos como Parquet (principal)
            eventos_df = self.resultados['eventos']
            if not eventos_df.empty:
                parquet_path = self.output_path.with_suffix('.parquet')
                eventos_df.to_parquet(parquet_path, compression='snappy')
                logger.info(f"Eventos guardados en {parquet_path}")
            
            # Guardar metadatos y métricas como JSON
            metadatos_path = self.output_path.with_suffix('.json')
            metadatos_completos = {
                k: v for k, v in self.resultados.items() 
                if k != 'eventos'  # Excluir DataFrame
            }
            
            with open(metadatos_path, 'w', encoding='utf-8') as f:
                json.dump(metadatos_completos, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Metadatos guardados en {metadatos_path}")
            
            # Guardar resumen de resultados como CSV para análisis rápido
            self._guardar_resumen_csv()
            
        except Exception as e:
            logger.error(f"Error guardando resultados: {e}")
            raise
    
    def _guardar_resumen_csv(self) -> None:
        """Guarda resumen ejecutivo en formato CSV."""
        try:
            # Extraer métricas clave
            metricas_sistema = self.resultados['metricas_sistema']
            metricas_entidades = self.resultados['metricas_entidades']
            
            # Crear resumen
            resumen = []
            
            # Métricas del sistema
            total_eventos = sum(metricas_sistema.eventos_por_tipo.values())
            resumen.append({
                'categoria': 'sistema',
                'metrica': 'total_eventos',
                'valor': total_eventos,
                'unidad': 'eventos'
            })
            
            # Métricas de entidades
            for entidad_id, metricas in metricas_entidades.items():
                for metrica, valor in metricas.items():
                    resumen.append({
                        'categoria': entidad_id,
                        'metrica': metrica,
                        'valor': valor,
                        'unidad': 'varios'
                    })
            
            # Guardar como CSV
            resumen_df = pd.DataFrame(resumen)
            csv_path = self.output_path.parent / f"{self.output_path.stem}_resumen.csv"
            resumen_df.to_csv(csv_path, index=False)
            
            logger.info(f"Resumen guardado en {csv_path}")
            
        except Exception as e:
            logger.warning(f"No se pudo guardar resumen CSV: {e}")


@app.command()
def ejecutar(
    config_path: Path = typer.Argument(..., help="Ruta al archivo de configuración YAML"),
    output_path: Path = typer.Argument(..., help="Ruta base para archivos de salida"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Modo verbose"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validar configuración sin ejecutar")
) -> None:
    """
    Ejecuta una simulación individual con configuración especificada.
    
    Examples:
        python ejecutar_simulacion.py configs/escenario_base.yaml results/sim_001
        python ejecutar_simulacion.py configs/test.yaml results/test --verbose
        python ejecutar_simulacion.py configs/scenario.yaml results/output --dry-run
    """
    
    # Configurar nivel de logging
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Validar rutas de entrada
        if not config_path.exists():
            typer.echo(f"Archivo de configuración no encontrado: {config_path}", err=True)
            raise typer.Exit(1)
        
        # Cargar y validar configuración
        typer.echo("Cargando configuración...")
        config_manager = ConfiguracionSimulacion(config_path)
        config = config_manager.get_config()
        
        typer.echo(f"Configuración cargada y validada")
        typer.echo(f"   - Duración: {config['simulacion']['duracion']} horas")
        typer.echo(f"   - Camiones: {len(config['entidades'])} unidades")
        typer.echo(f"   - Semilla: {config['simulacion']['semilla_aleatoria']}")
        
        if dry_run:
            typer.echo("Dry run completado - configuración válida")
            return
        
        # Crear y ejecutar simulación
        typer.echo("Iniciando simulación...")
        
        ejecutor = EjecutorSimulacion(config, output_path)
        ejecutor.preparar()
        ejecutor.ejecutar()
        ejecutor.guardar_resultados()
        
        typer.echo("Simulación completada exitosamente")
        typer.echo(f"   - Resultados guardados en: {output_path}")
        
        # Mostrar estadísticas básicas
        resultados = ejecutor.resultados
        eventos_df = resultados['eventos']
        
        if not eventos_df.empty:
            typer.echo("\nEstadísticas básicas:")
            typer.echo(f"   - Total de eventos: {len(eventos_df)}")
            typer.echo(f"   - Tipos de eventos únicos: {eventos_df['event_type'].nunique()}")
            typer.echo(f"   - Entidades activas: {eventos_df['entity_id'].nunique()}")
            typer.echo(f"   - Rango temporal: {eventos_df['timestamp'].min().strftime('%Y-%m-%d %H:%M')} - {eventos_df['timestamp'].max().strftime('%Y-%m-%d %H:%M')}")
        
    except Exception as e:
        typer.echo(f"Error: {e}", err=True)
        if verbose:
            typer.echo(f"Detalles: {traceback.format_exc()}", err=True)
        raise typer.Exit(1)


@app.command()
def validar_config(
    config_path: Path = typer.Argument(..., help="Ruta al archivo de configuración a validar")
) -> None:
    """
    Valida un archivo de configuración sin ejecutar la simulación.
    """
    try:
        config_manager = ConfiguracionSimulacion(config_path)
        config = config_manager.get_config()
        
        typer.echo("Configuración válida")
        
        # Mostrar resumen
        sim_config = config['simulacion']
        typer.echo(f"\nResumen de configuración:")
        typer.echo(f"   - Duración: {sim_config['duracion']} horas")
        typer.echo(f"   - Semilla aleatoria: {sim_config['semilla_aleatoria']}")
        typer.echo(f"   - Número de camiones: {len(config['entidades'])}")
        typer.echo(f"   - Capacidad planta: {config['planta']['capacidad_maxima']}")
        
    except Exception as e:
        typer.echo(f"Configuración inválida: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()