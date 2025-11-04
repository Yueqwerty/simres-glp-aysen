"""
Experimento Monte Carlo - Diseno Factorial 2x3
Factor endogeno: Capacidad (2 niveles)
Factor exogeno: Duracion Disrupciones (3 niveles)
Total: 6 configuraciones x 1000 replicas = 6,000 simulaciones
"""
import sys
import json
from pathlib import Path
from typing import List, Dict, Any
import logging
from datetime import datetime
import time

import numpy as np
import pandas as pd
from tqdm import tqdm

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modelo import ConfiguracionSimulacion, ejecutarSimulacion

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger(__name__)

NUM_REPLICAS = 1000
SEMILLA_BASE = 42

def generarConfiguracionesFactorial() -> List[Dict[str, Any]]:
    """Genera las 6 configuraciones del diseno factorial 2x3."""
    configuraciones = []

    capacidades = {
        'status_quo': 431.0,
        'propuesta': 681.0
    }

    duracionesMax = {
        'corta': 7.0,
        'media': 14.0,
        'larga': 21.0
    }

    configId = 1

    for capNombre, capacidadTm in capacidades.items():
        for durNombre, duracionMaxDias in duracionesMax.items():
            puntoReorden = capacidadTm * 0.50
            cantidadPedido = capacidadTm * 0.50
            inventarioInicial = capacidadTm * 0.60

            configuraciones.append({
                'configId': configId,
                'nombre': f"{capNombre}_{durNombre}",
                'factorCapacidad': capNombre,
                'factorDuracion': durNombre,
                'parametros': {
                    'capacidadHubTm': capacidadTm,
                    'puntoReordenTm': puntoReorden,
                    'cantidadPedidoTm': cantidadPedido,
                    'inventarioInicialTm': inventarioInicial,
                    'duracionDisrupcionMaxDias': duracionMaxDias,
                    'duracionDisrupcionModeDias': duracionMaxDias * 0.50,
                    'usarEstacionalidad': True,
                }
            })

            configId += 1

    return configuraciones


def ejecutarExperimentoMontecarlo(numReplicas: int = NUM_REPLICAS,
                                  semillaBase: int = SEMILLA_BASE) -> tuple:
    """
    Ejecuta el diseno de experimentos completo con Monte Carlo.

    Args:
        numReplicas: Numero de replicas por configuracion.
        semillaBase: Semilla base para generacion de numeros aleatorios.

    Returns:
        Tupla (DataFrame con resultados, tiempo total en segundos).
    """
    configuraciones = generarConfiguracionesFactorial()

    resultados = []

    print("="*80)
    print(f"EXPERIMENTO MONTE CARLO - DISENO FACTORIAL 2x3")
    print("="*80)
    print(f"Configuraciones:         {len(configuraciones)}")
    print(f"Replicas por config:     {numReplicas:,}")
    print(f"Total de simulaciones:   {len(configuraciones) * numReplicas:,}")
    print(f"Fecha/Hora inicio:       {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    tiempoInicio = time.time()

    for configMeta in configuraciones:
        configId = configMeta['configId']
        nombre = configMeta['nombre']
        parametros = configMeta['parametros']

        for replica in tqdm(range(1, numReplicas + 1),
                           desc=f"Config {configId}/6: {nombre}",
                           unit="sim",
                           ncols=100):
            # Crear configuracion con semilla unica
            config = ConfiguracionSimulacion(
                **parametros,
                semillaAleatoria=semillaBase + (configId - 1) * 10000 + replica
            )

            try:
                # Ejecutar simulacion
                kpis = ejecutarSimulacion(config)

                # Almacenar resultado
                resultado = {
                    'config_id': configId,
                    'nombre': nombre,
                    'replica': replica,
                    'factor_capacidad': configMeta['factorCapacidad'],
                    'factor_duracion': configMeta['factorDuracion'],
                    'capacidad_tm': parametros['capacidadHubTm'],
                    'duracion_max_dias': parametros['duracionDisrupcionMaxDias'],
                    **kpis  # Agregar todos los KPIs
                }

                resultados.append(resultado)

            except Exception as e:
                logger.error(f"Error en config {configId}, replica {replica}: {e}")
                continue

    tiempoTotal = time.time() - tiempoInicio
    df = pd.DataFrame(resultados)

    logger.info(f"Experimento completado: {len(resultados):,} simulaciones en {tiempoTotal/60:.1f} minutos")
    return df, tiempoTotal


def analisisDescriptivo(df: pd.DataFrame) -> None:
    """Realiza analisis descriptivo detallado de los resultados."""
    print("\n" + "="*80)
    print("ANALISIS DESCRIPTIVO")
    print("="*80)

    # Estadisticas por configuracion
    print("\n1. NIVEL DE SERVICIO POR CONFIGURACION:")
    print("-"*80)

    resumen = df.groupby(['factor_capacidad', 'factor_duracion']).agg({
        'nivel_servicio_pct': ['count', 'mean', 'std', 'min', 'median', 'max'],
        'probabilidad_quiebre_stock_pct': 'mean',
        'dias_con_quiebre': 'mean'
    }).round(4)

    print(resumen)

    # Efecto del factor endogeno
    print("\n2. EFECTO DEL FACTOR ENDOGENO (Capacidad):")
    print("-"*80)

    efectoCapacidad = df.groupby('factor_capacidad')['nivel_servicio_pct'].agg([
        'mean', 'std', ('sem', lambda x: x.std() / np.sqrt(len(x)))
    ])
    print(efectoCapacidad)

    deltaCapacidad = (
        efectoCapacidad.loc['propuesta', 'mean'] -
        efectoCapacidad.loc['status_quo', 'mean']
    )
    print(f"\nDelta Nivel Servicio (Propuesta - Status Quo): {deltaCapacidad:+.4f}%")

    # Efecto del factor exogeno
    print("\n3. EFECTO DEL FACTOR EXOGENO (Duracion Disrupciones):")
    print("-"*80)

    efectoDuracion = df.groupby('factor_duracion')['nivel_servicio_pct'].agg([
        'mean', 'std', ('sem', lambda x: x.std() / np.sqrt(len(x)))
    ])
    print(efectoDuracion)

    deltaDuracion = (
        efectoDuracion.loc['larga', 'mean'] -
        efectoDuracion.loc['corta', 'mean']
    )
    print(f"\nDelta Nivel Servicio (Larga - Corta): {deltaDuracion:+.4f}%")

    # Prueba de hipotesis
    print("\n4. PRUEBA DE HIPOTESIS - SENSIBILIDAD:")
    print("-"*80)

    sensibilidadEndogena = abs(deltaCapacidad)
    sensibilidadExogena = abs(deltaDuracion)

    print(f"Sensibilidad a factor endogeno (capacidad):  {sensibilidadEndogena:.4f}%")
    print(f"Sensibilidad a factor exogeno (duracion):    {sensibilidadExogena:.4f}%")

    ratio = sensibilidadExogena / sensibilidadEndogena if sensibilidadEndogena > 0 else float('inf')
    print(f"\nRatio (Exogena/Endogena): {ratio:.3f}x")

    if ratio > 1.5:
        print("\nHipotesis confirmada: La resiliencia es significativamente mas sensible")
        print("a factores exogenos (duracion de disrupciones) que a factores endogenos (capacidad).")
    else:
        print("\nHipotesis refutada: La resiliencia no muestra mayor sensibilidad a factores exogenos.")


def anovaCompleto(df: pd.DataFrame) -> Dict[str, Any]:
    """
    ANOVA de dos vias con interaccion y analisis post-hoc.

    Returns:
        Diccionario con resultados del analisis.
    """
    try:
        from statsmodels.formula.api import ols
        from statsmodels.stats.anova import anova_lm
        from statsmodels.stats.multicomp import pairwise_tukeyhsd
    except ImportError:
        print("\nstatsmodels no instalado. Instalando...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "statsmodels"])
        from statsmodels.formula.api import ols
        from statsmodels.stats.anova import anova_lm
        from statsmodels.stats.multicomp import pairwise_tukeyhsd

    print("\n" + "="*80)
    print("ANOVA DE DOS VIAS (Significancia Estadistica)")
    print("="*80)

    # Modelo ANOVA con interaccion
    modelo = ols(
        'nivel_servicio_pct ~ C(factor_capacidad) + C(factor_duracion) + C(factor_capacidad):C(factor_duracion)',
        data=df
    ).fit()

    tablaAnova = anova_lm(modelo, typ=2)

    print("\nTabla ANOVA (Tipo II):")
    print(tablaAnova)

    # Interpretacion de valores p
    print("\nInterpretacion (alfa = 0.05):")
    print("-"*80)

    pCapacidad = tablaAnova.loc['C(factor_capacidad)', 'PR(>F)']
    pDuracion = tablaAnova.loc['C(factor_duracion)', 'PR(>F)']
    pInteraccion = tablaAnova.loc['C(factor_capacidad):C(factor_duracion)', 'PR(>F)']

    print(f"Efecto CAPACIDAD:     p = {pCapacidad:.6f}", end="")
    print(f"  {'Significativo' if pCapacidad < 0.05 else 'No significativo'}")

    print(f"Efecto DURACION:      p = {pDuracion:.6f}", end="")
    print(f"  {'Significativo' if pDuracion < 0.05 else 'No significativo'}")

    print(f"INTERACCION CapxDur:  p = {pInteraccion:.6f}", end="")
    print(f"  {'Significativo' if pInteraccion < 0.05 else 'No significativo'}")

    # Tamano del efecto (eta cuadrado)
    print("\nTamano del Efecto (eta cuadrado):")
    print("-"*80)

    ssTotal = tablaAnova['sum_sq'].sum()
    eta2Capacidad = tablaAnova.loc['C(factor_capacidad)', 'sum_sq'] / ssTotal
    eta2Duracion = tablaAnova.loc['C(factor_duracion)', 'sum_sq'] / ssTotal
    eta2Interaccion = tablaAnova.loc['C(factor_capacidad):C(factor_duracion)', 'sum_sq'] / ssTotal

    print(f"eta2 Capacidad:    {eta2Capacidad:.6f} ({eta2Capacidad*100:.3f}% de varianza explicada)")
    print(f"eta2 Duracion:     {eta2Duracion:.6f} ({eta2Duracion*100:.3f}% de varianza explicada)")
    print(f"eta2 Interaccion:  {eta2Interaccion:.6f} ({eta2Interaccion*100:.3f}% de varianza explicada)")

    # Interpretacion del tamano del efecto
    print("\nInterpretacion de eta cuadrado (Cohen 1988):")
    print("  Pequeno:  eta2 ~ 0.01")
    print("  Mediano:  eta2 ~ 0.06")
    print("  Grande:   eta2 >= 0.14")

    if eta2Duracion > 2 * eta2Capacidad:
        print(f"\nConfirmacion formal: Duracion explica {eta2Duracion/eta2Capacidad:.1f}x mas varianza que Capacidad")

    # Tests Post-Hoc (Tukey HSD)
    print("\n" + "="*80)
    print("TESTS POST-HOC (Tukey HSD)")
    print("="*80)

    print("\nComparaciones multiples - Factor DURACION:")
    print("-"*80)
    tukeyDuracion = pairwise_tukeyhsd(
        endog=df['nivel_servicio_pct'],
        groups=df['factor_duracion'],
        alpha=0.05
    )
    print(tukeyDuracion)

    print("\nComparaciones multiples - Factor CAPACIDAD:")
    print("-"*80)
    tukeyCapacidad = pairwise_tukeyhsd(
        endog=df['nivel_servicio_pct'],
        groups=df['factor_capacidad'],
        alpha=0.05
    )
    print(tukeyCapacidad)

    # Retornar resultados para exportacion
    resultados = {
        'pCapacidad': float(pCapacidad),
        'pDuracion': float(pDuracion),
        'pInteraccion': float(pInteraccion),
        'eta2Capacidad': float(eta2Capacidad),
        'eta2Duracion': float(eta2Duracion),
        'eta2Interaccion': float(eta2Interaccion),
        'r2Ajustado': float(modelo.rsquared_adj),
    }

    return resultados


def calcularIntervalosConfianza(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula intervalos de confianza al 95% para cada configuracion."""
    from scipy import stats

    print("\n" + "="*80)
    print("INTERVALOS DE CONFIANZA (95%)")
    print("="*80)

    resultadosIc = []

    for (cap, dur), grupo in df.groupby(['factor_capacidad', 'factor_duracion']):
        nivelServicio = grupo['nivel_servicio_pct'].values

        n = len(nivelServicio)
        media = np.mean(nivelServicio)
        std = np.std(nivelServicio, ddof=1)
        sem = std / np.sqrt(n)

        # Intervalo de confianza al 95% (t-student)
        ic95 = stats.t.interval(0.95, n-1, loc=media, scale=sem)

        resultadosIc.append({
            'factor_capacidad': cap,
            'factor_duracion': dur,
            'n': n,
            'media': media,
            'std': std,
            'sem': sem,
            'ic95Inferior': ic95[0],
            'ic95Superior': ic95[1],
            'amplitudIc': ic95[1] - ic95[0]
        })

    dfIc = pd.DataFrame(resultadosIc)
    print(dfIc.to_string(index=False))

    return dfIc


def validarModelo(df: pd.DataFrame) -> None:
    """Valida el modelo comparando con datos reales del informe CNE."""
    print("\n" + "="*80)
    print("VALIDACION DEL MODELO")
    print("="*80)

    # Autonomia promedio del sistema status quo
    autonomiaSimulada = df[df['factor_capacidad'] == 'status_quo']['autonomia_promedio_dias'].mean()
    autonomiaEsperada = 8.2  # Del informe CNE

    print(f"\nAutonomia promedio (Status Quo):")
    print(f"  Simulada:   {autonomiaSimulada:.2f} dias")
    print(f"  Esperada:   {autonomiaEsperada:.2f} dias")
    print(f"  Error:      {abs(autonomiaSimulada - autonomiaEsperada):.2f} dias ({abs(autonomiaSimulada - autonomiaEsperada)/autonomiaEsperada*100:.1f}%)")

    if abs(autonomiaSimulada - autonomiaEsperada) / autonomiaEsperada < 0.15:
        print("\nModelo validado (error < 15%)")
    else:
        print("\nModelo requiere calibracion (error >= 15%)")


def exportarResultados(df: pd.DataFrame,
                       resultadosAnova: Dict[str, Any],
                       dfIc: pd.DataFrame,
                       rutaSalida: Path) -> None:
    """Exporta todos los resultados a CSV y JSON."""
    rutaSalida.mkdir(parents=True, exist_ok=True)

    # DataFrame completo
    df.to_csv(rutaSalida / "resultados_montecarlo.csv", index=False)
    print(f"\nResultados completos: {rutaSalida / 'resultados_montecarlo.csv'}")

    # Estadisticas descriptivas
    resumenStats = df.groupby(['factor_capacidad', 'factor_duracion']).agg({
        'nivel_servicio_pct': ['mean', 'std', 'min', 'max'],
        'probabilidad_quiebre_stock_pct': ['mean', 'std'],
        'dias_con_quiebre': ['mean', 'std'],
        'autonomia_promedio_dias': ['mean', 'std'],
        'disrupciones_totales': ['mean', 'std']
    }).round(4)

    resumenStats.to_csv(rutaSalida / "resumen_estadisticas.csv")
    print(f"Estadisticas descriptivas: {rutaSalida / 'resumen_estadisticas.csv'}")

    # Intervalos de confianza
    dfIc.to_csv(rutaSalida / "intervalos_confianza.csv", index=False)
    print(f"Intervalos de confianza: {rutaSalida / 'intervalos_confianza.csv'}")

    # Resultados ANOVA en JSON
    metadata = {
        'fechaExperimento': datetime.now().isoformat(),
        'numConfiguraciones': df['config_id'].nunique(),
        'numReplicas': df['replica'].max(),
        'totalSimulaciones': len(df),
        'nivelServicioGlobal': {
            'media': float(df['nivel_servicio_pct'].mean()),
            'std': float(df['nivel_servicio_pct'].std()),
            'min': float(df['nivel_servicio_pct'].min()),
            'max': float(df['nivel_servicio_pct'].max()),
        },
        'anova': resultadosAnova,
        'configuraciones': {}
    }

    for (cap, dur), grupo in df.groupby(['factor_capacidad', 'factor_duracion']):
        key = f"{cap}_{dur}"
        metadata['configuraciones'][key] = {
            'nivelServicioPct': {
                'media': float(grupo['nivel_servicio_pct'].mean()),
                'std': float(grupo['nivel_servicio_pct'].std()),
            },
            'probQuebrePct': float(grupo['probabilidad_quiebre_stock_pct'].mean()),
            'diasQuiebre': float(grupo['dias_con_quiebre'].mean()),
        }

    with open(rutaSalida / "metadata_experimento.json", 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    print(f"Metadata: {rutaSalida / 'metadata_experimento.json'}")


if __name__ == "__main__":
    print("\n")
    print("="*80)
    print(" "*18 + "EXPERIMENTO MONTE CARLO - TESIS GLP AYSEN")
    print("="*80)

    # Ejecutar experimento
    dfResultados, tiempoTotal = ejecutarExperimentoMontecarlo(numReplicas=NUM_REPLICAS)

    # Analisis descriptivo
    analisisDescriptivo(dfResultados)

    # ANOVA completo
    resultadosAnova = anovaCompleto(dfResultados)

    # Intervalos de confianza
    dfIc = calcularIntervalosConfianza(dfResultados)

    # Validacion del modelo
    validarModelo(dfResultados)

    # Exportar resultados
    rutaSalida = Path(__file__).parent.parent / "results" / "montecarlo"
    exportarResultados(dfResultados, resultadosAnova, dfIc, rutaSalida)

    print("\n" + "="*80)
    print("EXPERIMENTO COMPLETADO EXITOSAMENTE")
    print("="*80)
    print(f"\nResultados guardados en: {rutaSalida}")
    print("\nProximos pasos:")
    print("  1. Ejecutar: python scripts/generar_figuras_tesis.py")
    print("  2. Revisar figuras en: mitesis/figuras/")
    print("="*80)
