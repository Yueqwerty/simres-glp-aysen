"""
Script para ejecutar la simulación base de la cadena de suministro de GLP en Aysén.
Sin riesgos - Solo funcionamiento nominal del sistema.
"""
import json
import logging
import sys
from pathlib import Path

import numpy as np
import yaml

# Agregar el directorio raíz al path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.modelo_aysen import SimulacionAysen

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('simulacion_aysen_base.log')
    ]
)

logger = logging.getLogger(__name__)


def cargar_configuracion(ruta_config: str) -> dict:
    """Carga configuración desde archivo YAML."""
    with open(ruta_config, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    return config


def main():
    """Función principal."""
    logger.info("=" * 80)
    logger.info("SIMULACIÓN BASE - CADENA DE SUMINISTRO GLP AYSÉN")
    logger.info("=" * 80)

    # Cargar configuración
    ruta_config = Path(__file__).parent.parent / "configs" / "escenario_aysen_base.yml"
    logger.info(f"Cargando configuración desde: {ruta_config}")

    config = cargar_configuracion(str(ruta_config))

    # Extraer parámetros de simulación
    duracion_dias = config['simulacion']['duracion_dias']
    semilla = config['simulacion']['semilla_aleatoria']

    logger.info(f"Duración: {duracion_dias} días ({duracion_dias/365:.2f} años)")
    logger.info(f"Semilla aleatoria: {semilla}")

    # Crear generador de números aleatorios
    rng = np.random.default_rng(semilla)

    # Crear y ejecutar simulación
    logger.info("Creando simulación...")
    simulacion = SimulacionAysen(
        duracion_dias=duracion_dias,
        rng=rng,
        config=config
    )

    logger.info("Ejecutando simulación...")
    simulacion.ejecutar()

    logger.info("Simulación completada. Generando resultados...")

    # Obtener resultados
    resultados = simulacion.get_resultados()
    resumen = simulacion.get_resumen()

    # Mostrar resumen en consola
    logger.info("")
    logger.info("=" * 80)
    logger.info("RESUMEN DE RESULTADOS")
    logger.info("=" * 80)

    logger.info(f"Duración simulada: {resumen['duracion_simulada_dias']:.0f} días")
    logger.info(f"Tasa satisfacción demanda: {resumen['tasa_satisfaccion_demanda_pct']:.2f}%")
    logger.info(f"Días con desabastecimiento: {resumen['dias_con_desabastecimiento']}")
    logger.info(f"% Días con desabastecimiento: {resumen['porcentaje_dias_desabastecimiento']:.2f}%")

    logger.info("")
    logger.info("Transporte Primario:")
    logger.info(f"  Viajes completados: {resumen['viajes_transporte_primario']}")
    logger.info(f"  Volumen transportado: {resumen['volumen_transportado_tm']:.2f} TM")

    logger.info("")
    logger.info("Quiebres de Stock:")
    logger.info(f"  Hub granel: {resumen['quiebres_stock_hub_granel']}")
    logger.info(f"  Hub envasado: {resumen['quiebres_stock_hub_envasado']}")
    logger.info(f"  Red CDEs: {resumen['quiebres_stock_cdes']}")

    logger.info("")
    logger.info("Niveles Mínimos Alcanzados:")
    logger.info(f"  Hub granel: {resumen['nivel_minimo_hub_granel_tm']:.2f} TM")
    logger.info(f"  Hub envasado: {resumen['nivel_minimo_hub_envasado_tm']:.2f} TM")

    # Guardar resultados completos
    dir_resultados = Path(__file__).parent.parent / "results"
    dir_resultados.mkdir(exist_ok=True)

    # Guardar JSON con resumen y métricas
    ruta_json = dir_resultados / "simulacion_base_resultados.json"
    with open(ruta_json, 'w', encoding='utf-8') as f:
        json.dump({
            'resumen': resumen,
            'resultados_completos': resultados
        }, f, indent=2, ensure_ascii=False)

    logger.info("")
    logger.info(f"Resultados JSON guardados en: {ruta_json}")

    # Guardar series temporales en Parquet
    ruta_parquet = dir_resultados / "simulacion_base_series_temporales.parquet"
    simulacion.monitor.guardar_parquet(ruta_parquet)

    logger.info("=" * 80)


if __name__ == "__main__":
    main()
