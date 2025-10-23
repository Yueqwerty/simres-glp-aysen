"""
Visualización profesional de resultados para tesis.
Paletas de colores inspiradas en Wes Anderson.
"""
import sys
from pathlib import Path
from typing import Dict, List

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns

# Configuración de estilo profesional
plt.rcParams.update({
    'font.family': 'serif',
    'font.serif': ['Palatino', 'Times New Roman'],
    'font.size': 10,
    'axes.labelsize': 11,
    'axes.titlesize': 12,
    'xtick.labelsize': 9,
    'ytick.labelsize': 9,
    'legend.fontsize': 9,
    'figure.titlesize': 13,
    'text.usetex': False,  # Cambiar a True si tienes LaTeX instalado
    'axes.linewidth': 1.2,
    'grid.linewidth': 0.8,
    'lines.linewidth': 2,
    'patch.linewidth': 1,
})

# ============================================================================
# PALETAS WES ANDERSON
# ============================================================================

PALETAS_WES_ANDERSON = {
    'grand_budapest': {
        'primary': '#F1BB7B',      # Dorado pastel
        'secondary': '#FD6467',    # Rosa salmón
        'tertiary': '#5B1A18',     # Marrón oscuro
        'accent1': '#D67236',      # Naranja quemado
        'accent2': '#E6A0C4',      # Rosa suave
        'neutral': '#C6CDF7',      # Azul lavanda
        'background': '#F7F5E6',   # Crema
    },
    'royal_tenenbaums': {
        'primary': '#899DA4',      # Azul grisáceo
        'secondary': '#C93312',    # Rojo ladrillo
        'tertiary': '#FAEFD1',     # Crema
        'accent1': '#DC863B',      # Naranja tierra
        'accent2': '#9A8822',      # Mostaza
        'neutral': '#F5CDB4',      # Durazno
        'background': '#FAF0E6',   # Lino
    },
    'moonrise_kingdom': {
        'primary': '#F4E8D0',      # Beige arena
        'secondary': '#D8B70A',    # Amarillo mostaza
        'tertiary': '#02401B',     # Verde oscuro
        'accent1': '#A2A475',      # Verde oliva
        'accent2': '#81A88D',      # Verde salvia
        'neutral': '#F2F2F2',      # Gris muy claro
        'background': '#FEFEFE',   # Casi blanco
    },
    'darjeeling': {
        'primary': '#FF0000',      # Rojo intenso
        'secondary': '#00A08A',    # Verde turquesa
        'tertiary': '#F2AD00',     # Amarillo dorado
        'accent1': '#F98400',      # Naranja brillante
        'accent2': '#5BBCD6',      # Azul cielo
        'neutral': '#046C9A',      # Azul profundo
        'background': '#FFF8DC',   # Maíz
    }
}

# Usar Grand Budapest como paleta principal
PALETA_PRINCIPAL = PALETAS_WES_ANDERSON['grand_budapest']

# Colores para factores específicos
COLOR_STATUS_QUO = PALETA_PRINCIPAL['secondary']      # Rosa salmón
COLOR_PROPUESTA = PALETA_PRINCIPAL['primary']          # Dorado
COLOR_CORTA = PALETA_PRINCIPAL['accent2']              # Rosa suave
COLOR_MEDIA = PALETA_PRINCIPAL['accent1']              # Naranja
COLOR_LARGA = PALETA_PRINCIPAL['tertiary']             # Marrón oscuro

# Colores para KPIs
COLOR_NIVEL_SERVICIO = PALETAS_WES_ANDERSON['royal_tenenbaums']['primary']
COLOR_QUIEBRE = PALETAS_WES_ANDERSON['royal_tenenbaums']['secondary']
COLOR_INVENTARIO = PALETAS_WES_ANDERSON['moonrise_kingdom']['secondary']


# ============================================================================
# FUNCIONES DE VISUALIZACIÓN
# ============================================================================

def cargar_resultados(ruta_csv: Path) -> pd.DataFrame:
    """Carga resultados del experimento."""
    df = pd.read_csv(ruta_csv)
    print(f"Datos cargados: {len(df)} filas, {len(df.columns)} columnas")
    return df


def grafico_nivel_servicio_configuracion(df: pd.DataFrame, ruta_salida: Path) -> None:
    """
    Figura 1: Nivel de Servicio por Configuración (boxplot).
    """
    fig, ax = plt.subplots(figsize=(10, 5))

    # Preparar datos
    df['config_label'] = df.apply(
        lambda x: f"{x['factor_capacidad'].replace('status_quo', 'Status Quo').replace('propuesta', 'Propuesta')}\n{x['factor_duracion'].capitalize()}",
        axis=1
    )

    # Ordenar configuraciones
    orden = [
        'Status Quo\nCorta', 'Status Quo\nMedia', 'Status Quo\nLarga',
        'Propuesta\nCorta', 'Propuesta\nMedia', 'Propuesta\nLarga'
    ]

    # Colores por duración
    colores_duracion = {
        'corta': COLOR_CORTA,
        'media': COLOR_MEDIA,
        'larga': COLOR_LARGA
    }

    # Crear boxplot
    positions = []
    box_parts_list = []

    for i, config in enumerate(orden):
        datos = df[df['config_label'] == config]['nivel_servicio_pct']
        duracion = config.split('\n')[1].lower()

        bp = ax.boxplot(
            [datos],
            positions=[i],
            widths=0.6,
            patch_artist=True,
            boxprops=dict(facecolor=colores_duracion[duracion], alpha=0.7, linewidth=1.5),
            medianprops=dict(color='black', linewidth=2),
            whiskerprops=dict(linewidth=1.5),
            capprops=dict(linewidth=1.5),
            flierprops=dict(marker='o', markersize=4, alpha=0.5)
        )

        positions.append(i)
        box_parts_list.append(bp)

    # Configuración de ejes
    ax.set_xticks(positions)
    ax.set_xticklabels(orden, rotation=0, ha='center')
    ax.set_ylabel('Nivel de Servicio (%)', fontweight='bold')
    ax.set_xlabel('Configuración', fontweight='bold')
    ax.set_title('Nivel de Servicio por Configuración Experimental',
                 fontweight='bold', pad=15)

    # Límites del eje Y
    ax.set_ylim(96, 100.5)

    # Grid sutil
    ax.yaxis.grid(True, linestyle='--', alpha=0.3, linewidth=0.8)
    ax.set_axisbelow(True)

    # Línea de referencia en 99%
    ax.axhline(y=99, color='gray', linestyle=':', linewidth=1.5, alpha=0.6, label='Objetivo: 99%')

    # Leyenda
    legend_elements = [
        mpatches.Patch(facecolor=COLOR_CORTA, alpha=0.7, label='Disrupciones Cortas (7 días)'),
        mpatches.Patch(facecolor=COLOR_MEDIA, alpha=0.7, label='Disrupciones Medias (14 días)'),
        mpatches.Patch(facecolor=COLOR_LARGA, alpha=0.7, label='Disrupciones Largas (21 días)'),
    ]
    ax.legend(handles=legend_elements, loc='lower left', framealpha=0.95)

    # Fondo
    ax.set_facecolor(PALETA_PRINCIPAL['background'])
    fig.patch.set_facecolor('white')

    plt.tight_layout()
    plt.savefig(ruta_salida / 'fig1_nivel_servicio_configuracion.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(ruta_salida / 'fig1_nivel_servicio_configuracion.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Figura 1 guardada: {ruta_salida / 'fig1_nivel_servicio_configuracion.pdf'}")


def grafico_efecto_factores(df: pd.DataFrame, ruta_salida: Path) -> None:
    """
    Figura 2: Comparación del Efecto de Factores (barplot).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel A: Efecto del Factor ENDÓGENO (Capacidad)
    capacidad_stats = df.groupby('factor_capacidad')['nivel_servicio_pct'].agg(['mean', 'std']).reset_index()
    capacidad_stats['factor_capacidad'] = capacidad_stats['factor_capacidad'].replace({
        'status_quo': 'Status Quo\n(431 TM)',
        'propuesta': 'Propuesta\n(681 TM)'
    })

    bars1 = ax1.bar(
        capacidad_stats['factor_capacidad'],
        capacidad_stats['mean'],
        yerr=capacidad_stats['std'],
        color=[COLOR_STATUS_QUO, COLOR_PROPUESTA],
        alpha=0.8,
        capsize=8,
        error_kw={'linewidth': 2, 'elinewidth': 2}
    )

    ax1.set_ylabel('Nivel de Servicio Promedio (%)', fontweight='bold')
    ax1.set_xlabel('Capacidad de Almacenamiento', fontweight='bold')
    ax1.set_title('(A) Efecto del Factor ENDÓGENO', fontweight='bold', pad=10)
    ax1.set_ylim(98, 100)
    ax1.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax1.set_axisbelow(True)
    ax1.set_facecolor(PALETA_PRINCIPAL['background'])

    # Añadir valores sobre las barras
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height + 0.15,
                f'{height:.2f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=10)

    # Panel B: Efecto del Factor EXÓGENO (Duración)
    duracion_stats = df.groupby('factor_duracion')['nivel_servicio_pct'].agg(['mean', 'std']).reset_index()
    duracion_orden = ['corta', 'media', 'larga']
    duracion_stats = duracion_stats.set_index('factor_duracion').loc[duracion_orden].reset_index()
    duracion_stats['factor_duracion'] = duracion_stats['factor_duracion'].replace({
        'corta': 'Corta\n(7 días)',
        'media': 'Media\n(14 días)',
        'larga': 'Larga\n(21 días)'
    })

    bars2 = ax2.bar(
        duracion_stats['factor_duracion'],
        duracion_stats['mean'],
        yerr=duracion_stats['std'],
        color=[COLOR_CORTA, COLOR_MEDIA, COLOR_LARGA],
        alpha=0.8,
        capsize=8,
        error_kw={'linewidth': 2, 'elinewidth': 2}
    )

    ax2.set_ylabel('Nivel de Servicio Promedio (%)', fontweight='bold')
    ax2.set_xlabel('Duración Máxima de Disrupciones', fontweight='bold')
    ax2.set_title('(B) Efecto del Factor EXÓGENO', fontweight='bold', pad=10)
    ax2.set_ylim(98, 100)
    ax2.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax2.set_axisbelow(True)
    ax2.set_facecolor(PALETA_PRINCIPAL['background'])

    # Añadir valores sobre las barras
    for bar in bars2:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + 0.15,
                f'{height:.2f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=10)

    fig.patch.set_facecolor('white')
    plt.tight_layout()
    plt.savefig(ruta_salida / 'fig2_efecto_factores.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(ruta_salida / 'fig2_efecto_factores.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Figura 2 guardada: {ruta_salida / 'fig2_efecto_factores.pdf'}")


def grafico_sensibilidad_hipotesis(df: pd.DataFrame, ruta_salida: Path) -> None:
    """
    Figura 3: Prueba de Hipótesis - Ratio de Sensibilidad.
    """
    fig, ax = plt.subplots(figsize=(8, 6))

    # Calcular sensibilidades
    # Endógena: diferencia entre propuesta y status quo (agregado sobre duraciones)
    ns_propuesta = df[df['factor_capacidad'] == 'propuesta']['nivel_servicio_pct'].mean()
    ns_status_quo = df[df['factor_capacidad'] == 'status_quo']['nivel_servicio_pct'].mean()
    sensibilidad_endogena = abs(ns_propuesta - ns_status_quo)

    # Exógena: diferencia entre larga y corta (agregado sobre capacidades)
    ns_larga = df[df['factor_duracion'] == 'larga']['nivel_servicio_pct'].mean()
    ns_corta = df[df['factor_duracion'] == 'corta']['nivel_servicio_pct'].mean()
    sensibilidad_exogena = abs(ns_larga - ns_corta)

    # Ratio
    ratio = sensibilidad_exogena / sensibilidad_endogena if sensibilidad_endogena > 0 else 0

    # Crear barras
    categorias = ['Factor\nENDÓGENO\n(Capacidad)', 'Factor\nEXÓGENO\n(Duración)']
    sensibilidades = [sensibilidad_endogena, sensibilidad_exogena]
    colores = [COLOR_PROPUESTA, COLOR_LARGA]

    bars = ax.bar(categorias, sensibilidades, color=colores, alpha=0.8, width=0.5)

    # Etiquetas
    ax.set_ylabel('Sensibilidad del Nivel de Servicio\n(Cambio absoluto en puntos porcentuales)',
                  fontweight='bold')
    ax.set_title('Prueba de Hipótesis: Sensibilidad de la Resiliencia',
                 fontweight='bold', pad=15, fontsize=13)

    # Valores sobre barras
    for bar, val in zip(bars, sensibilidades):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.05,
                f'{val:.2f}%',
                ha='center', va='bottom', fontweight='bold', fontsize=12)

    # Anotación del ratio
    ax.text(0.5, max(sensibilidades) * 0.85,
            f'Ratio de Sensibilidad:\n{ratio:.2f}×',
            ha='center', va='center',
            bbox=dict(boxstyle='round,pad=0.8', facecolor=PALETA_PRINCIPAL['neutral'],
                      edgecolor='black', linewidth=2, alpha=0.9),
            fontsize=12, fontweight='bold')

    # Flecha indicando mayor sensibilidad
    ax.annotate('', xy=(1, sensibilidad_exogena - 0.1), xytext=(1, sensibilidad_endogena + 0.1),
                arrowprops=dict(arrowstyle='->', lw=2.5, color='black'))

    ax.text(1.35, (sensibilidad_exogena + sensibilidad_endogena) / 2,
            f'+{sensibilidad_exogena - sensibilidad_endogena:.2f}%',
            ha='left', va='center', fontsize=10, style='italic')

    # Grid y estilo
    ax.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax.set_axisbelow(True)
    ax.set_ylim(0, max(sensibilidades) * 1.3)
    ax.set_facecolor(PALETA_PRINCIPAL['background'])
    fig.patch.set_facecolor('white')

    plt.tight_layout()
    plt.savefig(ruta_salida / 'fig3_sensibilidad_hipotesis.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(ruta_salida / 'fig3_sensibilidad_hipotesis.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Figura 3 guardada: {ruta_salida / 'fig3_sensibilidad_hipotesis.pdf'}")
    print(f"  Ratio de sensibilidad: {ratio:.2f}x")


def grafico_heatmap_configuraciones(df: pd.DataFrame, ruta_salida: Path) -> None:
    """
    Figura 4: Heatmap de Nivel de Servicio (2D).
    """
    fig, ax = plt.subplots(figsize=(8, 5))

    # Crear matriz pivote
    matriz = df.groupby(['factor_duracion', 'factor_capacidad'])['nivel_servicio_pct'].mean().unstack()

    # Reordenar
    matriz = matriz.reindex(index=['corta', 'media', 'larga'],
                           columns=['status_quo', 'propuesta'])

    # Renombrar
    matriz.index = ['Corta\n(7 días)', 'Media\n(14 días)', 'Larga\n(21 días)']
    matriz.columns = ['Status Quo\n(431 TM)', 'Propuesta\n(681 TM)']

    # Crear heatmap
    im = ax.imshow(matriz.values, cmap='RdYlGn', aspect='auto', vmin=97, vmax=100)

    # Ticks
    ax.set_xticks(np.arange(len(matriz.columns)))
    ax.set_yticks(np.arange(len(matriz.index)))
    ax.set_xticklabels(matriz.columns)
    ax.set_yticklabels(matriz.index)

    # Labels
    ax.set_xlabel('Capacidad de Almacenamiento', fontweight='bold', fontsize=11)
    ax.set_ylabel('Duración Máxima de Disrupciones', fontweight='bold', fontsize=11)
    ax.set_title('Nivel de Servicio por Combinación de Factores', fontweight='bold', pad=15)

    # Anotaciones con valores
    for i in range(len(matriz.index)):
        for j in range(len(matriz.columns)):
            valor = matriz.iloc[i, j]
            color_texto = 'white' if valor < 98.5 else 'black'
            ax.text(j, i, f'{valor:.2f}%',
                   ha='center', va='center', color=color_texto,
                   fontweight='bold', fontsize=11)

    # Colorbar
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Nivel de Servicio (%)', fontweight='bold', rotation=270, labelpad=20)

    fig.patch.set_facecolor('white')
    plt.tight_layout()
    plt.savefig(ruta_salida / 'fig4_heatmap_configuraciones.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(ruta_salida / 'fig4_heatmap_configuraciones.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Figura 4 guardada: {ruta_salida / 'fig4_heatmap_configuraciones.pdf'}")


def grafico_disrupciones_impacto(df: pd.DataFrame, ruta_salida: Path) -> None:
    """
    Figura 5: Impacto de Disrupciones en el Sistema.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))

    # Panel A: Días con quiebre por configuración
    quiebre_stats = df.groupby(['factor_capacidad', 'factor_duracion']).agg({
        'dias_con_quiebre': ['mean', 'std']
    }).reset_index()

    quiebre_stats.columns = ['capacidad', 'duracion', 'media', 'std']

    # Crear gráfico agrupado
    duraciones = ['corta', 'media', 'larga']
    x = np.arange(2)  # Status Quo y Propuesta
    width = 0.25

    for i, dur in enumerate(duraciones):
        datos_dur = quiebre_stats[quiebre_stats['duracion'] == dur]
        valores = [
            datos_dur[datos_dur['capacidad'] == 'status_quo']['media'].values[0],
            datos_dur[datos_dur['capacidad'] == 'propuesta']['media'].values[0]
        ]
        errores = [
            datos_dur[datos_dur['capacidad'] == 'status_quo']['std'].values[0],
            datos_dur[datos_dur['capacidad'] == 'propuesta']['std'].values[0]
        ]

        colores_map = {'corta': COLOR_CORTA, 'media': COLOR_MEDIA, 'larga': COLOR_LARGA}

        ax1.bar(x + i*width, valores, width, yerr=errores,
               label=f'{dur.capitalize()} ({["7", "14", "21"][i]} días)',
               color=colores_map[dur], alpha=0.8, capsize=5)

    ax1.set_ylabel('Días con Quiebre de Stock (promedio)', fontweight='bold')
    ax1.set_xlabel('Configuración de Capacidad', fontweight='bold')
    ax1.set_title('(A) Frecuencia de Quiebres de Stock', fontweight='bold', pad=10)
    ax1.set_xticks(x + width)
    ax1.set_xticklabels(['Status Quo\n(431 TM)', 'Propuesta\n(681 TM)'])
    ax1.legend(framealpha=0.95)
    ax1.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax1.set_axisbelow(True)
    ax1.set_facecolor(PALETA_PRINCIPAL['background'])

    # Panel B: Tiempo bloqueado vs Tiempo con quiebre
    disrupciones_stats = df.groupby('factor_duracion').agg({
        'pct_tiempo_bloqueado': 'mean',
        'probabilidad_quiebre_stock_pct': 'mean'
    }).reset_index()

    disrupciones_stats = disrupciones_stats.set_index('factor_duracion').loc[duraciones].reset_index()

    x2 = np.arange(len(duraciones))
    width2 = 0.35

    bars1 = ax2.bar(x2 - width2/2, disrupciones_stats['pct_tiempo_bloqueado'],
                   width2, label='% Tiempo Ruta Bloqueada',
                   color=PALETAS_WES_ANDERSON['darjeeling']['accent1'], alpha=0.8)
    bars2 = ax2.bar(x2 + width2/2, disrupciones_stats['probabilidad_quiebre_stock_pct'],
                   width2, label='% Tiempo con Quiebre',
                   color=PALETAS_WES_ANDERSON['darjeeling']['secondary'], alpha=0.8)

    ax2.set_ylabel('Porcentaje del Tiempo (%)', fontweight='bold')
    ax2.set_xlabel('Duración Máxima de Disrupciones', fontweight='bold')
    ax2.set_title('(B) Tiempo Bloqueado vs Tiempo con Quiebre', fontweight='bold', pad=10)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(['Corta\n(7 días)', 'Media\n(14 días)', 'Larga\n(21 días)'])
    ax2.legend(framealpha=0.95)
    ax2.yaxis.grid(True, linestyle='--', alpha=0.3)
    ax2.set_axisbelow(True)
    ax2.set_facecolor(PALETA_PRINCIPAL['background'])

    # Añadir valores sobre barras en panel B
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.2,
                    f'{height:.1f}%',
                    ha='center', va='bottom', fontsize=8)

    fig.patch.set_facecolor('white')
    plt.tight_layout()
    plt.savefig(ruta_salida / 'fig5_disrupciones_impacto.pdf', dpi=300, bbox_inches='tight')
    plt.savefig(ruta_salida / 'fig5_disrupciones_impacto.png', dpi=300, bbox_inches='tight')
    plt.close()

    print(f"[OK] Figura 5 guardada: {ruta_salida / 'fig5_disrupciones_impacto.pdf'}")


def generar_todas_figuras(ruta_csv: Path, ruta_salida: Path) -> None:
    """Genera todas las figuras para la tesis."""
    # Crear directorio de salida
    ruta_salida.mkdir(parents=True, exist_ok=True)

    # Cargar datos
    print("\n" + "="*70)
    print("GENERACIÓN DE FIGURAS PARA TESIS")
    print("="*70)
    df = cargar_resultados(ruta_csv)

    # Generar figuras
    print("\nGenerando figuras...")
    grafico_nivel_servicio_configuracion(df, ruta_salida)
    grafico_efecto_factores(df, ruta_salida)
    grafico_sensibilidad_hipotesis(df, ruta_salida)
    grafico_heatmap_configuraciones(df, ruta_salida)
    grafico_disrupciones_impacto(df, ruta_salida)

    print("\n" + "="*70)
    print("FIGURAS GENERADAS EXITOSAMENTE")
    print(f"Ubicación: {ruta_salida}")
    print("="*70)


if __name__ == "__main__":
    # Rutas
    ruta_proyecto = Path(__file__).parent.parent
    ruta_csv = ruta_proyecto / "results" / "experimento_tesis" / "resultados_experimento.csv"
    ruta_salida = ruta_proyecto / "results" / "figuras_tesis"

    # Generar figuras
    generar_todas_figuras(ruta_csv, ruta_salida)
