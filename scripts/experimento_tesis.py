"""
Diseño de Experimentos para Prueba de Hipótesis de Tesis.

Diseño Factorial 2×3:
- Factor ENDÓGENO: Capacidad de Almacenamiento (2 niveles)
- Factor EXÓGENO: Duración de Disrupciones (3 niveles)

Total: 6 configuraciones × N réplicas
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

import numpy as np
import pandas as pd

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modelo_simple import ConfiguracionSimulacion, ejecutar_simulacion_simple

logging.basicConfig(level=logging.WARNING)  # Solo warnings/errors
logger = logging.getLogger(__name__)


def generar_configuraciones_factorial() -> List[Dict[str, Any]]:
    """
    Genera las 6 configuraciones del diseño factorial 2×3.

    Returns:
        Lista de diccionarios con parámetros y metadata.
    """
    configuraciones = []

    # Factor 1: Capacidad de Almacenamiento (ENDÓGENO)
    capacidades = {
        'status_quo': 431.0,      # Nivel 1: Capacidad actual Aysén
        'propuesta': 681.0         # Nivel 2: Propuesta 10.4 (+250 TM)
    }

    # Factor 2: Duración Máxima de Disrupciones (EXÓGENO)
    duraciones_max = {
        'corta': 7.0,              # Nivel 1: Disrupciones leves
        'media': 14.0,             # Nivel 2: Disrupciones moderadas
        'larga': 21.0              # Nivel 3: Caso extremo (Argentina)
    }

    config_id = 1

    for cap_nombre, capacidad_tm in capacidades.items():
        for dur_nombre, duracion_max_dias in duraciones_max.items():
            # Calcular punto de reorden (50% de capacidad)
            punto_reorden = capacidad_tm * 0.5

            # Calcular cantidad de pedido (50% de capacidad)
            cantidad_pedido = capacidad_tm * 0.5

            # Inventario inicial (60% de capacidad)
            inventario_inicial = capacidad_tm * 0.6

            configuraciones.append({
                'config_id': config_id,
                'nombre': f"{cap_nombre}_{dur_nombre}",
                'factor_capacidad': cap_nombre,
                'factor_duracion': dur_nombre,
                'parametros': {
                    'capacidad_hub_tm': capacidad_tm,
                    'punto_reorden_tm': punto_reorden,
                    'cantidad_pedido_tm': cantidad_pedido,
                    'inventario_inicial_tm': inventario_inicial,
                    'duracion_disrupcion_max_dias': duracion_max_dias,
                    # Mantener mode proporcional al max
                    'duracion_disrupcion_mode_dias': duracion_max_dias * 0.5,
                }
            })

            config_id += 1

    return configuraciones


def ejecutar_experimento_completo(num_replicas: int = 30, semilla_base: int = 42) -> pd.DataFrame:
    """
    Ejecuta el diseño de experimentos completo con réplicas.

    Args:
        num_replicas: Número de réplicas por configuración.
        semilla_base: Semilla base para generación de números aleatorios.

    Returns:
        DataFrame con todos los resultados.
    """
    configuraciones = generar_configuraciones_factorial()

    resultados = []

    print("="*70)
    print(f"DISEÑO DE EXPERIMENTOS FACTORIAL 2×3")
    print(f"Configuraciones: {len(configuraciones)}")
    print(f"Réplicas por configuración: {num_replicas}")
    print(f"Total de simulaciones: {len(configuraciones) * num_replicas}")
    print("="*70)

    for config_meta in configuraciones:
        config_id = config_meta['config_id']
        nombre = config_meta['nombre']
        parametros = config_meta['parametros']

        print(f"\n[{config_id}/6] Ejecutando: {nombre}")
        print(f"  Capacidad: {parametros['capacidad_hub_tm']:.0f} TM")
        print(f"  Duración máx: {parametros['duracion_disrupcion_max_dias']:.0f} días")

        for replica in range(1, num_replicas + 1):
            # Crear configuración con semilla única
            config = ConfiguracionSimulacion(
                **parametros,
                semilla_aleatoria=semilla_base + (config_id - 1) * 1000 + replica
            )

            # Ejecutar simulación
            kpis = ejecutar_simulacion_simple(config)

            # Almacenar resultado
            resultado = {
                'config_id': config_id,
                'nombre': nombre,
                'replica': replica,
                'factor_capacidad': config_meta['factor_capacidad'],
                'factor_duracion': config_meta['factor_duracion'],
                'capacidad_tm': parametros['capacidad_hub_tm'],
                'duracion_max_dias': parametros['duracion_disrupcion_max_dias'],
                **kpis  # Agregar todos los KPIs
            }

            resultados.append(resultado)

            # Progreso
            if replica % 10 == 0:
                print(f"    Réplica {replica}/{num_replicas} completada")

    print("\n" + "="*70)
    print("EXPERIMENTO COMPLETO")
    print("="*70)

    # Convertir a DataFrame
    df = pd.DataFrame(resultados)

    return df


def analizar_resultados(df: pd.DataFrame) -> None:
    """
    Realiza análisis descriptivo de los resultados del experimento.

    Args:
        df: DataFrame con resultados del experimento.
    """
    print("\n" + "="*70)
    print("ANÁLISIS DE RESULTADOS")
    print("="*70)

    # 1. Estadísticas descriptivas por configuración
    print("\n1. NIVEL DE SERVICIO PROMEDIO POR CONFIGURACIÓN:")
    print("-"*70)

    resumen = df.groupby(['factor_capacidad', 'factor_duracion']).agg({
        'nivel_servicio_pct': ['mean', 'std', 'min', 'max'],
        'probabilidad_quiebre_stock_pct': 'mean',
        'dias_con_quiebre': 'mean'
    }).round(2)

    print(resumen)

    # 2. Efecto del factor ENDÓGENO (capacidad)
    print("\n2. EFECTO DEL FACTOR ENDÓGENO (Capacidad):")
    print("-"*70)

    efecto_capacidad = df.groupby('factor_capacidad')['nivel_servicio_pct'].agg(['mean', 'std'])
    print(efecto_capacidad)

    delta_capacidad = (
        efecto_capacidad.loc['propuesta', 'mean'] -
        efecto_capacidad.loc['status_quo', 'mean']
    )
    print(f"\nDelta Nivel Servicio (Propuesta vs Status Quo): {delta_capacidad:+.2f}%")

    # 3. Efecto del factor EXÓGENO (duración disrupciones)
    print("\n3. EFECTO DEL FACTOR EXÓGENO (Duración Disrupciones):")
    print("-"*70)

    efecto_duracion = df.groupby('factor_duracion')['nivel_servicio_pct'].agg(['mean', 'std'])
    print(efecto_duracion)

    delta_duracion_corta_larga = (
        efecto_duracion.loc['larga', 'mean'] -
        efecto_duracion.loc['corta', 'mean']
    )
    print(f"\nDelta Nivel Servicio (Larga vs Corta): {delta_duracion_corta_larga:+.2f}%")

    # 4. Comparación de sensibilidad
    print("\n4. COMPARACIÓN DE SENSIBILIDAD (Prueba de Hipótesis):")
    print("-"*70)

    # Sensibilidad = cambio absoluto en nivel de servicio
    sensibilidad_endogena = abs(delta_capacidad)
    sensibilidad_exogena = abs(delta_duracion_corta_larga)

    print(f"Sensibilidad a factor ENDÓGENO (capacidad):  {sensibilidad_endogena:.2f}%")
    print(f"Sensibilidad a factor EXÓGENO (duración):    {sensibilidad_exogena:.2f}%")

    ratio = sensibilidad_exogena / sensibilidad_endogena if sensibilidad_endogena > 0 else float('inf')
    print(f"\nRatio (Exógena/Endógena): {ratio:.2f}x")

    if ratio > 1.5:
        print("\n[OK] HIPOTESIS CONFIRMADA:")
        print("   La resiliencia es significativamente MAS SENSIBLE a factores exogenos")
        print("   (duracion de disrupciones) que a factores endogenos (capacidad).")
    else:
        print("\n[X] HIPOTESIS REFUTADA:")
        print("   La resiliencia NO muestra mayor sensibilidad a factores exogenos.")

    # 5. Validación de autonomía
    print("\n5. VALIDACIÓN DE MODELO (Autonomía del Sistema):")
    print("-"*70)

    autonomia_status_quo = df[df['factor_capacidad'] == 'status_quo']['autonomia_promedio_dias'].mean()
    print(f"Autonomía promedio (Status Quo): {autonomia_status_quo:.2f} días")
    print(f"Autonomía esperada (dato real):  8.20 días")

    if 7.5 <= autonomia_status_quo <= 9.0:
        print("[OK] Modelo VALIDADO (autonomia dentro del rango esperado)")
    else:
        print("[!] Modelo necesita calibracion (autonomia fuera de rango)")


def exportar_resultados(df: pd.DataFrame, ruta_salida: Path) -> None:
    """Exporta resultados a CSV y JSON."""
    ruta_salida.mkdir(parents=True, exist_ok=True)

    # CSV completo
    df.to_csv(ruta_salida / "resultados_experimento.csv", index=False)
    print(f"\n[OK] Resultados exportados a: {ruta_salida / 'resultados_experimento.csv'}")

    # Resumen JSON
    resumen = {
        'num_configuraciones': df['config_id'].nunique(),
        'num_replicas': df['replica'].nunique(),
        'total_simulaciones': len(df),
        'nivel_servicio_promedio_pct': float(df['nivel_servicio_pct'].mean()),
        'configuraciones': {
            f"{cap}_{dur}": float(nivel_servicio)
            for (cap, dur), nivel_servicio in
            df.groupby(['factor_capacidad', 'factor_duracion'])['nivel_servicio_pct'].mean().items()
        }
    }

    with open(ruta_salida / "resumen_experimento.json", 'w') as f:
        json.dump(resumen, f, indent=2)

    print(f"[OK] Resumen exportado a: {ruta_salida / 'resumen_experimento.json'}")


if __name__ == "__main__":
    # Ejecutar experimento
    df_resultados = ejecutar_experimento_completo(num_replicas=30)

    # Analizar
    analizar_resultados(df_resultados)

    # Exportar
    ruta_salida = Path(__file__).parent.parent / "results" / "experimento_tesis"
    exportar_resultados(df_resultados, ruta_salida)

    print("\n" + "="*70)
    print("EXPERIMENTO COMPLETADO EXITOSAMENTE")
    print("="*70)
