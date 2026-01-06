"""Servicio de análisis estadístico ANOVA para experimentos Monte Carlo.

Este módulo implementa:
- ANOVA de dos vías (capacidad × duración)
- Cálculo de efectos principales e interacciones
- Tests post-hoc (Tukey HSD)
- Tamaño del efecto (eta cuadrado)
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.formula.api import ols
from statsmodels.stats.anova import anova_lm
from statsmodels.stats.multicomp import pairwise_tukeyhsd


@dataclass
class ANOVAResult:
    """Resultado completo del análisis ANOVA."""

    # Tabla ANOVA principal
    tabla_anova: pd.DataFrame

    # Efectos principales
    efecto_capacidad: float
    efecto_duracion: float
    efecto_interaccion: float

    # Tamaños del efecto (eta cuadrado)
    eta_cuadrado_capacidad: float
    eta_cuadrado_duracion: float
    eta_cuadrado_interaccion: float

    # Tests post-hoc
    tukey_capacidad: Optional[pd.DataFrame]
    tukey_duracion: Optional[pd.DataFrame]

    # R² ajustado del modelo
    r_cuadrado_ajustado: float

    # Medias por grupo
    medias_por_configuracion: pd.DataFrame


def calcular_anova_dos_vias(
    data: pd.DataFrame,
    variable_respuesta: str = "nivel_servicio",
    factor_1: str = "capacidad",
    factor_2: str = "duracion"
) -> ANOVAResult:
    """Calcula ANOVA de dos vías con interacción.

    Args:
        data: DataFrame con las columnas del experimento
        variable_respuesta: Nombre de la variable dependiente
        factor_1: Nombre del primer factor (ej. 'capacidad')
        factor_2: Nombre del segundo factor (ej. 'duracion')

    Returns:
        Resultado completo del análisis ANOVA

    Example:
        >>> df = pd.DataFrame({
        ...     'nivel_servicio': [84.3, 81.1, 78.1, 98.8, 97.2, 94.7],
        ...     'capacidad': ['SQ', 'SQ', 'SQ', 'PR', 'PR', 'PR'],
        ...     'duracion': ['C', 'M', 'L', 'C', 'M', 'L']
        ... })
        >>> resultado = calcular_anova_dos_vias(df)
        >>> print(resultado.tabla_anova)
    """
    # Validar datos
    required_cols = [variable_respuesta, factor_1, factor_2]
    missing = set(required_cols) - set(data.columns)
    if missing:
        raise ValueError(f"Columnas faltantes: {missing}")

    # Asegurar que los factores son categóricos
    data = data.copy()
    data[factor_1] = data[factor_1].astype('category')
    data[factor_2] = data[factor_2].astype('category')

    # Modelo ANOVA de dos vías con interacción (Tipo II)
    formula = f"{variable_respuesta} ~ C({factor_1}) + C({factor_2}) + C({factor_1}):C({factor_2})"
    modelo = ols(formula, data=data).fit()

    # Tabla ANOVA Tipo II (suma de cuadrados parcial)
    tabla_anova = anova_lm(modelo, typ=2)

    # Calcular tamaños del efecto (eta cuadrado parcial)
    ss_total = tabla_anova['sum_sq'].sum()

    eta_cuadrado_capacidad = tabla_anova.loc[f'C({factor_1})', 'sum_sq'] / ss_total
    eta_cuadrado_duracion = tabla_anova.loc[f'C({factor_2})', 'sum_sq'] / ss_total

    # Verificar si existe la interacción
    interaccion_key = f'C({factor_1}):C({factor_2})'
    if interaccion_key in tabla_anova.index:
        eta_cuadrado_interaccion = tabla_anova.loc[interaccion_key, 'sum_sq'] / ss_total
    else:
        eta_cuadrado_interaccion = 0.0

    # Calcular efectos principales (diferencia entre niveles extremos)
    medias_factor1 = data.groupby(factor_1)[variable_respuesta].mean()
    medias_factor2 = data.groupby(factor_2)[variable_respuesta].mean()

    efecto_capacidad = medias_factor1.max() - medias_factor1.min()
    efecto_duracion = medias_factor2.max() - medias_factor2.min()

    # Efecto de interacción (diferencia de diferencias)
    medias_interaccion = data.groupby([factor_1, factor_2])[variable_respuesta].mean()
    if len(medias_interaccion) >= 4:  # Mínimo 2x2 para calcular interacción
        efecto_interaccion = medias_interaccion.std()
    else:
        efecto_interaccion = 0.0

    # Tests post-hoc Tukey HSD
    tukey_capacidad = None
    tukey_duracion = None

    if len(data[factor_1].unique()) > 1:
        tukey_cap = pairwise_tukeyhsd(
            endog=data[variable_respuesta],
            groups=data[factor_1],
            alpha=0.05
        )
        tukey_capacidad = pd.DataFrame(
            data=tukey_cap.summary().data[1:],
            columns=tukey_cap.summary().data[0]
        )

    if len(data[factor_2].unique()) > 1:
        tukey_dur = pairwise_tukeyhsd(
            endog=data[variable_respuesta],
            groups=data[factor_2],
            alpha=0.05
        )
        tukey_duracion = pd.DataFrame(
            data=tukey_dur.summary().data[1:],
            columns=tukey_dur.summary().data[0]
        )

    # Medias por configuración
    medias_por_configuracion = data.groupby([factor_1, factor_2])[variable_respuesta].agg([
        'mean', 'std', 'count',
        ('ci_lower', lambda x: x.mean() - 1.96 * x.std() / np.sqrt(len(x))),
        ('ci_upper', lambda x: x.mean() + 1.96 * x.std() / np.sqrt(len(x)))
    ]).reset_index()

    # Renombrar columnas para mejor legibilidad
    tabla_anova_clean = tabla_anova.copy()
    tabla_anova_clean.index = [
        'Capacidad' if f'C({factor_1})' in idx else
        'Duración' if f'C({factor_2})' in idx else
        'Capacidad × Duración' if ':' in idx else
        'Residual'
        for idx in tabla_anova_clean.index
    ]
    tabla_anova_clean.columns = ['SC', 'gl', 'MC', 'F', 'p-valor']

    return ANOVAResult(
        tabla_anova=tabla_anova_clean,
        efecto_capacidad=efecto_capacidad,
        efecto_duracion=efecto_duracion,
        efecto_interaccion=efecto_interaccion,
        eta_cuadrado_capacidad=eta_cuadrado_capacidad,
        eta_cuadrado_duracion=eta_cuadrado_duracion,
        eta_cuadrado_interaccion=eta_cuadrado_interaccion,
        tukey_capacidad=tukey_capacidad,
        tukey_duracion=tukey_duracion,
        r_cuadrado_ajustado=modelo.rsquared_adj,
        medias_por_configuracion=medias_por_configuracion
    )


def formatear_resultados_anova(resultado: ANOVAResult) -> Dict:
    """Convierte los resultados ANOVA a formato JSON serializable.

    Args:
        resultado: Resultado del análisis ANOVA

    Returns:
        Diccionario con todos los resultados en formato JSON-friendly
    """
    return {
        "tabla_anova": resultado.tabla_anova.to_dict(orient='records'),
        "efectos_principales": {
            "capacidad": round(resultado.efecto_capacidad, 4),
            "duracion": round(resultado.efecto_duracion, 4),
            "interaccion": round(resultado.efecto_interaccion, 4)
        },
        "tamanos_efecto": {
            "eta_cuadrado_capacidad": round(resultado.eta_cuadrado_capacidad, 4),
            "eta_cuadrado_duracion": round(resultado.eta_cuadrado_duracion, 4),
            "eta_cuadrado_interaccion": round(resultado.eta_cuadrado_interaccion, 4)
        },
        "r_cuadrado_ajustado": round(resultado.r_cuadrado_ajustado, 4),
        "medias_por_configuracion": resultado.medias_por_configuracion.to_dict(orient='records'),
        "tukey_capacidad": resultado.tukey_capacidad.to_dict(orient='records') if resultado.tukey_capacidad is not None else None,
        "tukey_duracion": resultado.tukey_duracion.to_dict(orient='records') if resultado.tukey_duracion is not None else None,
    }
