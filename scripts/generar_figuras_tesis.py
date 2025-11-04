"""
Generacion de Figuras para Tesis - Formato SVG con Paleta Profesional
Estilo publication-ready con colores inspirados en Wes Anderson
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')  # Backend sin GUI
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

# Paleta de colores profesional basada en peliculas de Wes Anderson
WES_PALETTE = {
    'rosaPastel': '#F7A1B7',
    'coral': '#E8927C',
    'amarilloPastel': '#F4D58D',
    'verdeMenta': '#8FC1A9',
    'azulCielo': '#7FA8C9',
    'terracota': '#C86A53',
    'lavanda': '#B4A7D6',
    'crema': '#F2E8CF',
    'borgona': '#9B4F5A',
    'turquesa': '#6FB3B8',
}

# Asignacion a factores experimentales
COLOR_STATUS_QUO = WES_PALETTE['terracota']
COLOR_PROPUESTA = WES_PALETTE['azulCielo']

COLOR_CORTA = WES_PALETTE['verdeMenta']
COLOR_MEDIA = WES_PALETTE['amarilloPastel']
COLOR_LARGA = WES_PALETTE['rosaPastel']

# Configuracion global minimalista
plt.rcParams.update({
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'Helvetica', 'DejaVu Sans'],
    'font.size': 10,
    'axes.labelsize': 12,
    'axes.titlesize': 13,
    'axes.titleweight': 'normal',
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'figure.titlesize': 14,
    'text.usetex': False,
    'axes.linewidth': 1,
    'axes.edgecolor': '#CCCCCC',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'grid.linewidth': 0.5,
    'grid.alpha': 0.3,
    'lines.linewidth': 2,
    'patch.linewidth': 1,
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'savefig.bbox': 'tight',
    'savefig.format': 'pdf',
    'savefig.facecolor': 'white',
})

COLOR_GRID = '#E0E0E0'
COLOR_BACKGROUND = '#FFFFFF'


def cargarDatos():
    """Carga todos los archivos de resultados"""
    basePath = Path(__file__).parent.parent / 'results' / 'montecarlo'

    dfResultados = pd.read_csv(basePath / 'resultados_montecarlo.csv')
    dfStats = pd.read_csv(basePath / 'resumen_estadisticas.csv')
    dfIc = pd.read_csv(basePath / 'intervalos_confianza.csv')

    print(f"Datos cargados: {len(dfResultados):,} simulaciones")
    print(f"Configuraciones: {len(dfStats)}")

    return dfResultados, dfStats, dfIc


def figuraDistribuciones(df: pd.DataFrame, salida: Path):
    """Violin plots con paleta Wes Anderson"""
    fig, ax = plt.subplots(figsize=(18, 10))

    # Preparar datos
    df['config'] = df.apply(
        lambda x: f"{x['factor_capacidad'].replace('status_quo', 'SQ').replace('propuesta', 'Prop')}\n{x['factor_duracion'].capitalize()}",
        axis=1
    )

    orden = ['SQ\nCorta', 'SQ\nMedia', 'SQ\nLarga',
             'Prop\nCorta', 'Prop\nMedia', 'Prop\nLarga']

    datosPorConfig = [df[df['config'] == c]['nivel_servicio_pct'].values for c in orden]

    # Violin plot
    parts = ax.violinplot(
        datosPorConfig,
        positions=range(len(orden)),
        widths=0.75,
        showmeans=True,
        showextrema=True,
        showmedians=True
    )

    # Aplicar colores segun duracion
    colores = [COLOR_CORTA, COLOR_MEDIA, COLOR_LARGA] * 2
    for i, pc in enumerate(parts['bodies']):
        pc.set_facecolor(colores[i])
        pc.set_alpha(0.75)
        pc.set_edgecolor('black')
        pc.set_linewidth(1.3)

    # Lineas de mediana y media
    parts['cmedians'].set_edgecolor('black')
    parts['cmedians'].set_linewidth(2.5)
    parts['cmeans'].set_edgecolor(WES_PALETTE['borgona'])
    parts['cmeans'].set_linewidth(2.5)

    # Linea separadora entre Status Quo y Propuesta
    ax.axvline(x=2.5, color='gray', linestyle='--', linewidth=2, alpha=0.5)

    # Etiquetas y formato
    ax.set_xticks(range(len(orden)))
    ax.set_xticklabels(orden, fontsize=12)
    ax.set_ylabel('Nivel de Servicio (%)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Configuracion', fontsize=14, fontweight='bold')
    ax.set_title('Distribucion del Nivel de Servicio por Configuracion\n(1,000 replicas Monte Carlo)',
                 fontsize=15, fontweight='bold', pad=15)

    ax.grid(True, alpha=0.3, linestyle=':', color=COLOR_GRID)
    ax.set_axisbelow(True)
    ax.set_ylim(70, 105)

    # Leyenda
    from matplotlib.patches import Patch
    leyenda = [
        Patch(facecolor=COLOR_CORTA, edgecolor='black', label='Duracion Corta (7 dias)'),
        Patch(facecolor=COLOR_MEDIA, edgecolor='black', label='Duracion Media (14 dias)'),
        Patch(facecolor=COLOR_LARGA, edgecolor='black', label='Duracion Larga (21 dias)'),
    ]
    ax.legend(handles=leyenda, loc='lower left', frameon=True, shadow=True)

    # Guardar en ambos formatos
    plt.savefig(salida.with_suffix('.svg'), format='svg', bbox_inches='tight')
    plt.savefig(salida.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Figura guardada: {salida.name}")


def figuraDistribucionesKde(df: pd.DataFrame, salida: Path):
    """KDE plots en grid 2x3"""
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    axes = axes.flatten()

    configs = [
        ('status_quo', 'corta', 'Status Quo - Corta (7d)', COLOR_CORTA),
        ('status_quo', 'media', 'Status Quo - Media (14d)', COLOR_MEDIA),
        ('status_quo', 'larga', 'Status Quo - Larga (21d)', COLOR_LARGA),
        ('propuesta', 'corta', 'Propuesta - Corta (7d)', COLOR_CORTA),
        ('propuesta', 'media', 'Propuesta - Media (14d)', COLOR_MEDIA),
        ('propuesta', 'larga', 'Propuesta - Larga (21d)', COLOR_LARGA),
    ]

    for i, (cap, dur, titulo, color) in enumerate(configs):
        ax = axes[i]
        datos = df[(df['factor_capacidad'] == cap) & (df['factor_duracion'] == dur)]['nivel_servicio_pct']

        # Histograma normalizado
        ax.hist(datos, bins=30, density=True, alpha=0.6, color=color,
                edgecolor='black', linewidth=1.2)

        # KDE
        from scipy.stats import gaussian_kde
        kde = gaussian_kde(datos)
        xRange = np.linspace(datos.min(), datos.max(), 200)
        ax.plot(xRange, kde(xRange), color='black', linewidth=2.5, label='KDE')

        # Estadisticas
        media = datos.mean()
        mediana = datos.median()
        std = datos.std()

        ax.axvline(media, color=WES_PALETTE['borgona'], linestyle='--', linewidth=2, label=f'Media: {media:.1f}%')
        ax.axvline(mediana, color=WES_PALETTE['turquesa'], linestyle=':', linewidth=2, label=f'Mediana: {mediana:.1f}%')

        ax.set_title(titulo, fontsize=13, fontweight='bold')
        ax.set_xlabel('Nivel de Servicio (%)', fontsize=11)
        ax.set_ylabel('Densidad', fontsize=11)
        ax.legend(fontsize=9, loc='upper left')
        ax.grid(True, alpha=0.3, linestyle=':', color=COLOR_GRID)
        ax.set_axisbelow(True)

        # Anotar desviacion estandar
        ax.text(0.98, 0.98, f'sigma = {std:.2f}%', transform=ax.transAxes,
                ha='right', va='top', fontsize=10,
                bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    plt.suptitle('Distribuciones de Probabilidad (KDE) por Configuracion\n(1,000 replicas Monte Carlo)',
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()

    plt.savefig(salida.with_suffix('.svg'), format='svg', bbox_inches='tight')
    plt.savefig(salida.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Figura guardada: {salida.name}")


def figuraQqPlots(df: pd.DataFrame, salida: Path):
    """Q-Q plots para validar normalidad"""
    fig, axes = plt.subplots(2, 3, figsize=(20, 12))
    axes = axes.flatten()

    configs = [
        ('status_quo', 'corta', 'Status Quo - Corta'),
        ('status_quo', 'media', 'Status Quo - Media'),
        ('status_quo', 'larga', 'Status Quo - Larga'),
        ('propuesta', 'corta', 'Propuesta - Corta'),
        ('propuesta', 'media', 'Propuesta - Media'),
        ('propuesta', 'larga', 'Propuesta - Larga'),
    ]

    for i, (cap, dur, titulo) in enumerate(configs):
        ax = axes[i]
        datos = df[(df['factor_capacidad'] == cap) & (df['factor_duracion'] == dur)]['nivel_servicio_pct']

        # Q-Q plot
        stats.probplot(datos, dist="norm", plot=ax)

        # Test de Shapiro-Wilk
        stat, pValor = stats.shapiro(datos)

        ax.set_title(f'{titulo}\n(Shapiro-Wilk: p = {pValor:.4f})',
                     fontsize=12, fontweight='bold')
        ax.get_lines()[0].set_color(WES_PALETTE['turquesa'])
        ax.get_lines()[0].set_markersize(4)
        ax.get_lines()[0].set_alpha(0.6)
        ax.get_lines()[1].set_color(WES_PALETTE['borgona'])
        ax.get_lines()[1].set_linewidth(2.5)

        ax.grid(True, alpha=0.3, linestyle=':', color=COLOR_GRID)
        ax.set_axisbelow(True)

    plt.suptitle('Q-Q Plots: Validacion de Normalidad\n(Comparacion contra distribucion normal teorica)',
                 fontsize=16, fontweight='bold', y=0.995)
    plt.tight_layout()

    plt.savefig(salida.with_suffix('.svg'), format='svg', bbox_inches='tight')
    plt.savefig(salida.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Figura guardada: {salida.name}")


def figuraEfectosPrincipales(df: pd.DataFrame, salida: Path):
    """Efectos principales con intervalos de confianza"""
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 8))

    # Panel A: Factor Capacidad
    capacidades = df.groupby('factor_capacidad')['nivel_servicio_pct'].agg(['mean', 'sem'])
    capacidades = capacidades.reindex(['status_quo', 'propuesta'])

    xPos = [0, 1]
    coloresCap = [COLOR_STATUS_QUO, COLOR_PROPUESTA]

    bars1 = ax1.bar(xPos, capacidades['mean'],
                    color=coloresCap,
                    edgecolor='black',
                    linewidth=1.5,
                    alpha=0.85,
                    width=0.6)

    # Intervalo de confianza 95% (1.96 * SEM)
    ax1.errorbar(xPos, capacidades['mean'],
                 yerr=1.96 * capacidades['sem'],
                 fmt='none', ecolor='black', elinewidth=2.5, capsize=8, capthick=2.5)

    # Valores sobre las barras
    for i, (pos, val) in enumerate(zip(xPos, capacidades['mean'])):
        ax1.text(pos, val + 2, f'{val:.1f}%', ha='center', va='bottom',
                fontsize=12, fontweight='bold')

    ax1.set_xticks(xPos)
    ax1.set_xticklabels(['Status Quo\n(431 TM)', 'Propuesta\n(681 TM)'], fontsize=12)
    ax1.set_ylabel('Nivel de Servicio Promedio (%)', fontsize=13, fontweight='bold')
    ax1.set_title('(A) Efecto de la Capacidad de Almacenamiento', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y', linestyle=':', color=COLOR_GRID)
    ax1.set_axisbelow(True)
    ax1.set_ylim(75, 102)

    # Panel B: Factor Duracion
    duraciones = df.groupby('factor_duracion')['nivel_servicio_pct'].agg(['mean', 'sem'])
    duraciones = duraciones.reindex(['corta', 'media', 'larga'])

    xPos2 = [0, 1, 2]
    coloresDur = [COLOR_CORTA, COLOR_MEDIA, COLOR_LARGA]

    bars2 = ax2.bar(xPos2, duraciones['mean'],
                    color=coloresDur,
                    edgecolor='black',
                    linewidth=1.5,
                    alpha=0.85,
                    width=0.6)

    ax2.errorbar(xPos2, duraciones['mean'],
                 yerr=1.96 * duraciones['sem'],
                 fmt='none', ecolor='black', elinewidth=2.5, capsize=8, capthick=2.5)

    for i, (pos, val) in enumerate(zip(xPos2, duraciones['mean'])):
        ax2.text(pos, val + 1, f'{val:.1f}%', ha='center', va='bottom',
                fontsize=12, fontweight='bold')

    ax2.set_xticks(xPos2)
    ax2.set_xticklabels(['Corta\n(7 dias)', 'Media\n(14 dias)', 'Larga\n(21 dias)'], fontsize=12)
    ax2.set_ylabel('Nivel de Servicio Promedio (%)', fontsize=13, fontweight='bold')
    ax2.set_title('(B) Efecto de la Duracion de Disrupciones', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, axis='y', linestyle=':', color=COLOR_GRID)
    ax2.set_axisbelow(True)
    ax2.set_ylim(75, 102)

    plt.suptitle('Efectos Principales de los Factores Experimentales\n(Barras de error: IC 95%)',
                 fontsize=16, fontweight='bold', y=1.02)
    plt.tight_layout()

    plt.savefig(salida.with_suffix('.svg'), format='svg', bbox_inches='tight')
    plt.savefig(salida.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Figura guardada: {salida.name}")


def figuraHeatmap(df: pd.DataFrame, salida: Path):
    """Heatmap de nivel de servicio por configuracion"""
    fig, ax = plt.subplots(figsize=(14, 10))

    # Crear matriz de datos
    matriz = df.groupby(['factor_capacidad', 'factor_duracion'])['nivel_servicio_pct'].mean().unstack()
    matriz = matriz.reindex(index=['status_quo', 'propuesta'],
                           columns=['corta', 'media', 'larga'])

    # Heatmap con paleta divergente
    im = ax.imshow(matriz.values, cmap='RdYlGn', aspect='auto',
                   vmin=75, vmax=100, interpolation='nearest')

    # Etiquetas
    ax.set_xticks([0, 1, 2])
    ax.set_xticklabels(['Corta (7d)', 'Media (14d)', 'Larga (21d)'], fontsize=12)
    ax.set_yticks([0, 1])
    ax.set_yticklabels(['Status Quo (431 TM)', 'Propuesta (681 TM)'], fontsize=12)

    ax.set_xlabel('Duracion Maxima de Disrupciones', fontsize=14, fontweight='bold')
    ax.set_ylabel('Capacidad de Almacenamiento', fontsize=14, fontweight='bold')
    ax.set_title('Nivel de Servicio Promedio por Configuracion (%)\n(Interaccion Capacidad x Duracion)',
                 fontsize=15, fontweight='bold', pad=15)

    # Valores en celdas
    for i in range(2):
        for j in range(3):
            text = ax.text(j, i, f'{matriz.values[i, j]:.1f}%',
                          ha="center", va="center", color="black",
                          fontsize=14, fontweight='bold',
                          bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))

    # Barra de color
    cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label('Nivel de Servicio (%)', fontsize=13, fontweight='bold')
    cbar.ax.tick_params(labelsize=11)

    plt.tight_layout()
    plt.savefig(salida.with_suffix('.svg'), format='svg', bbox_inches='tight')
    plt.savefig(salida.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Figura guardada: {salida.name}")


def figuraTornado(df: pd.DataFrame, salida: Path):
    """Tornado diagram de sensibilidad"""
    fig, ax = plt.subplots(figsize=(16, 9))

    # Calcular sensibilidades
    capBajo = df[df['factor_capacidad'] == 'status_quo']['nivel_servicio_pct'].mean()
    capAlto = df[df['factor_capacidad'] == 'propuesta']['nivel_servicio_pct'].mean()
    sensCapacidad = capAlto - capBajo

    durCorta = df[df['factor_duracion'] == 'corta']['nivel_servicio_pct'].mean()
    durLarga = df[df['factor_duracion'] == 'larga']['nivel_servicio_pct'].mean()
    sensDuracion = durCorta - durLarga

    # Datos para tornado
    factores = ['Capacidad\n(431 -> 681 TM)', 'Duracion\n(21 -> 7 dias)']
    valores = [sensCapacidad, sensDuracion]
    colores = [COLOR_PROPUESTA, COLOR_LARGA]

    # Ordenar por magnitud
    orden = np.argsort(valores)[::-1]
    factoresOrd = [factores[i] for i in orden]
    valoresOrd = [valores[i] for i in orden]
    coloresOrd = [colores[i] for i in orden]

    yPos = np.arange(len(factoresOrd))

    bars = ax.barh(yPos, valoresOrd, color=coloresOrd,
                   edgecolor='black', linewidth=1.5, alpha=0.85, height=0.6)

    # Valores al final de las barras
    for i, (val, y) in enumerate(zip(valoresOrd, yPos)):
        ax.text(val + 0.3, y, f'+{val:.2f}%', va='center', ha='left',
                fontsize=13, fontweight='bold')

    ax.set_yticks(yPos)
    ax.set_yticklabels(factoresOrd, fontsize=12)
    ax.set_xlabel('Cambio en Nivel de Servicio (puntos porcentuales)', fontsize=13, fontweight='bold')
    ax.set_title('Analisis de Sensibilidad: Impacto de Factores en Resiliencia\n(Tornado Diagram)',
                 fontsize=15, fontweight='bold', pad=15)

    ax.grid(True, alpha=0.3, axis='x', linestyle=':', color=COLOR_GRID)
    ax.set_axisbelow(True)
    ax.set_xlim(0, max(valoresOrd) * 1.15)

    # Linea vertical en 0
    ax.axvline(x=0, color='black', linewidth=2)

    plt.tight_layout()
    plt.savefig(salida.with_suffix('.svg'), format='svg', bbox_inches='tight')
    plt.savefig(salida.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Figura guardada: {salida.name}")


def figuraBoxplot(df: pd.DataFrame, salida: Path):
    """Boxplot comparativo de configuraciones"""
    fig, ax = plt.subplots(figsize=(18, 10))

    df['config'] = df.apply(
        lambda x: f"{x['factor_capacidad'].replace('status_quo', 'SQ').replace('propuesta', 'Prop')} - {x['factor_duracion'].capitalize()}",
        axis=1
    )

    orden = ['SQ - Corta', 'SQ - Media', 'SQ - Larga',
             'Prop - Corta', 'Prop - Media', 'Prop - Larga']

    datosBox = [df[df['config'] == c]['nivel_servicio_pct'].values for c in orden]

    bp = ax.boxplot(datosBox,
                    positions=range(len(orden)),
                    widths=0.6,
                    patch_artist=True,
                    showmeans=True,
                    meanprops=dict(marker='D', markerfacecolor=WES_PALETTE['borgona'],
                                 markeredgecolor='black', markersize=8),
                    medianprops=dict(color='black', linewidth=2.5),
                    boxprops=dict(linewidth=1.5),
                    whiskerprops=dict(linewidth=1.5),
                    capprops=dict(linewidth=1.5))

    # Colores por duracion
    colores = [COLOR_CORTA, COLOR_MEDIA, COLOR_LARGA] * 2
    for patch, color in zip(bp['boxes'], colores):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    ax.set_xticks(range(len(orden)))
    ax.set_xticklabels(orden, rotation=15, ha='right', fontsize=11)
    ax.set_ylabel('Nivel de Servicio (%)', fontsize=14, fontweight='bold')
    ax.set_xlabel('Configuracion', fontsize=14, fontweight='bold')
    ax.set_title('Comparacion de Configuraciones mediante Boxplots\n(Diamante: media | Linea: mediana)',
                 fontsize=15, fontweight='bold', pad=15)

    ax.grid(True, alpha=0.3, linestyle=':', color=COLOR_GRID, axis='y')
    ax.set_axisbelow(True)
    ax.set_ylim(65, 105)

    # Linea separadora
    ax.axvline(x=2.5, color='gray', linestyle='--', linewidth=2, alpha=0.5)

    plt.tight_layout()
    plt.savefig(salida.with_suffix('.svg'), format='svg', bbox_inches='tight')
    plt.savefig(salida.with_suffix('.pdf'), format='pdf', bbox_inches='tight')
    plt.close()
    print(f"Figura guardada: {salida.name}")


def main():
    """Funcion principal para generar todas las figuras"""
    print("="*70)
    print("GENERACION DE FIGURAS PARA TESIS")
    print("="*70)

    # Cargar datos
    dfResultados, dfStats, dfIc = cargarDatos()

    # Crear directorio de salida
    salidaDir = Path(__file__).parent.parent / 'mitesis' / 'figuras'
    salidaDir.mkdir(parents=True, exist_ok=True)

    print(f"\nDirectorio de salida: {salidaDir}")
    print("\nGenerando figuras...\n")

    # Generar todas las figuras
    figuraDistribuciones(dfResultados, salidaDir / 'distribuciones')
    figuraDistribucionesKde(dfResultados, salidaDir / 'distribuciones_kde')
    figuraQqPlots(dfResultados, salidaDir / 'qq_plots')
    figuraEfectosPrincipales(dfResultados, salidaDir / 'efectos_principales')
    figuraHeatmap(dfResultados, salidaDir / 'heatmap_interacciones')
    figuraTornado(dfResultados, salidaDir / 'analisis_sensibilidad')
    figuraBoxplot(dfResultados, salidaDir / 'boxplot_comparativo')

    print("\n" + "="*70)
    print("TODAS LAS FIGURAS GENERADAS EXITOSAMENTE")
    print("="*70)
    print(f"\nFormatos generados: SVG (vectorial) + PDF (backup)")
    print(f"Paleta: Inspirada en peliculas de Wes Anderson")
    print(f"DPI: 300 (publication-ready)")
    print(f"Ubicacion: {salidaDir}/")


if __name__ == "__main__":
    main()
