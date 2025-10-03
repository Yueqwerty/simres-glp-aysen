"""
Script para visualizar resultados de la simulación de GLP Aysén.
Genera 3 gráficos profesionales integrados con paleta Wes Anderson.
"""
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.gridspec import GridSpec

# Paleta Wes Anderson
COLORS_WES = {
    'primary': '#264653',      # Azul oscuro profundo
    'secondary': '#2A9D8F',    # Verde azulado
    'accent1': '#E9C46A',      # Amarillo mostaza
    'accent2': '#F4A261',      # Naranja suave
    'accent3': '#E76F51',      # Coral/rojo suave
    'accent4': '#8AB17D',      # Verde oliva
    'accent5': '#6A4C93',      # Púrpura
}

# Configuración profesional
plt.style.use('seaborn-v0_8-whitegrid')
plt.rcParams.update({
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'font.family': 'sans-serif',
    'font.sans-serif': ['Arial', 'DejaVu Sans'],
    'font.size': 11,
    'axes.labelsize': 11,
    'axes.titlesize': 13,
    'axes.titleweight': 'bold',
    'xtick.labelsize': 10,
    'ytick.labelsize': 10,
    'legend.fontsize': 9,
    'axes.facecolor': '#FAFAFA',
    'grid.alpha': 0.25,
    'grid.linestyle': '--',
    'lines.linewidth': 2,
})


def cargar_datos(ruta_json: Path, ruta_parquet: Path):
    """Carga resultados JSON y series temporales Parquet."""
    with open(ruta_json, 'r', encoding='utf-8') as f:
        resultados = json.load(f)

    df = pd.read_parquet(ruta_parquet) if ruta_parquet.exists() else pd.DataFrame()

    return resultados, df


def grafico_1_sistema_integrado(df: pd.DataFrame, ruta_salida: Path):
    """
    Gráfico 1: Vista Integrada del Sistema Completo
    - Inventarios en todas las etapas
    - Flujos principales
    - Demanda vs suministro con satisfacción
    """
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 1, height_ratios=[1.2, 1, 1], hspace=0.25)

    # ========== PANEL 1: Inventarios en todas las etapas ==========
    ax1 = fig.add_subplot(gs[0])

    ax1.fill_between(df['dia'], 0, df['inv_hub_granel'],
                     color=COLORS_WES['primary'], alpha=0.6, label='Hub Granel')
    ax1.plot(df['dia'], df['inv_hub_granel'],
            color=COLORS_WES['primary'], linewidth=2.5, alpha=0.9)

    ax1.fill_between(df['dia'], 0, df['inv_hub_envasado'],
                     color=COLORS_WES['secondary'], alpha=0.5, label='Hub Envasado')
    ax1.plot(df['dia'], df['inv_hub_envasado'],
            color=COLORS_WES['secondary'], linewidth=2.5, alpha=0.9)

    ax1.fill_between(df['dia'], 0, df['inv_cdes'],
                     color=COLORS_WES['accent2'], alpha=0.4, label='Red CDEs')
    ax1.plot(df['dia'], df['inv_cdes'],
            color=COLORS_WES['accent2'], linewidth=2, alpha=0.9)

    # Marcar zonas estacionales
    ax1.axvspan(0, 90, alpha=0.05, color='orange', label='Verano')
    ax1.axvspan(90, 270, alpha=0.08, color='blue', label='Otoño-Invierno')
    ax1.axvspan(270, 364, alpha=0.05, color='orange')

    ax1.set_ylabel('Inventario (TM)', fontsize=12, fontweight='bold')
    ax1.set_title('Evolución Temporal de Inventarios por Etapa del Sistema',
                  fontsize=14, pad=15)
    ax1.legend(loc='upper right', ncol=5, framealpha=0.95)
    ax1.set_xlim(0, 364)
    ax1.grid(True, alpha=0.25)

    # ========== PANEL 2: Flujos principales ==========
    ax2 = fig.add_subplot(gs[1])

    # Media móvil de 7 días para suavizar
    flujo_recepcion_ma = df['flujo_recepcion_hub'].rolling(7, min_periods=1).mean()
    flujo_procesamiento_ma = df['flujo_envasado_procesado'].rolling(7, min_periods=1).mean()
    flujo_despacho_granel_ma = df['flujo_despacho_granel'].rolling(7, min_periods=1).mean()
    flujo_despacho_envasado_ma = df['flujo_reabastecimiento_cdes'].rolling(7, min_periods=1).mean()

    ax2.plot(df['dia'], flujo_recepcion_ma,
            color=COLORS_WES['primary'], linewidth=2.5, label='Recepción Hub', alpha=0.9)
    ax2.plot(df['dia'], flujo_procesamiento_ma,
            color=COLORS_WES['accent1'], linewidth=2, label='Procesamiento Envasado', alpha=0.8)
    ax2.plot(df['dia'], flujo_despacho_granel_ma,
            color=COLORS_WES['accent3'], linewidth=2, label='Despacho Granel', alpha=0.8)
    ax2.plot(df['dia'], flujo_despacho_envasado_ma,
            color=COLORS_WES['accent5'], linewidth=2, label='Despacho a CDEs', alpha=0.8)

    ax2.set_ylabel('Flujo diario (TM)\nMedia móvil 7 días', fontsize=12, fontweight='bold')
    ax2.set_title('Flujos de Material en la Cadena de Suministro',
                  fontsize=14, pad=15)
    ax2.legend(loc='upper right', ncol=4, framealpha=0.95)
    ax2.set_xlim(0, 364)
    ax2.grid(True, alpha=0.25)

    # ========== PANEL 3: Demanda vs Suministro + Satisfacción ==========
    ax3 = fig.add_subplot(gs[2])
    ax3_twin = ax3.twinx()

    # Demanda total diaria
    demanda_total = df['demanda_granel'] + df['demanda_envasado']
    demanda_total_ma = demanda_total.rolling(7, min_periods=1).mean()

    # Suministro = recepción hub
    suministro_ma = df['flujo_recepcion_hub'].rolling(7, min_periods=1).mean()

    # Gráfico de áreas para demanda y suministro
    ax3.fill_between(df['dia'], 0, demanda_total_ma,
                     color=COLORS_WES['accent3'], alpha=0.4, label='Demanda total')
    ax3.plot(df['dia'], demanda_total_ma,
            color=COLORS_WES['accent3'], linewidth=2.5, alpha=0.9)

    ax3.fill_between(df['dia'], 0, suministro_ma,
                     color=COLORS_WES['secondary'], alpha=0.35, label='Suministro (recepción hub)')
    ax3.plot(df['dia'], suministro_ma,
            color=COLORS_WES['secondary'], linewidth=2.5, alpha=0.9)

    # Satisfacción en eje secundario
    satisfaccion_total = (df['satisfaccion_granel'] + df['satisfaccion_envasado']) / 2 * 100
    satisfaccion_ma = satisfaccion_total.rolling(7, min_periods=1).mean()

    ax3_twin.plot(df['dia'], satisfaccion_ma,
                 color=COLORS_WES['accent5'], linewidth=3,
                 label='Satisfacción (7d)', alpha=0.95, linestyle='-')
    ax3_twin.axhline(y=95, color='#E76F51', linestyle='--',
                    linewidth=2, alpha=0.6, label='Objetivo 95%')

    ax3.set_xlabel('Días de Simulación', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Volumen (TM/día)', fontsize=12, fontweight='bold', color=COLORS_WES['primary'])
    ax3_twin.set_ylabel('Tasa de Satisfacción (%)', fontsize=12, fontweight='bold',
                       color=COLORS_WES['accent5'])
    ax3.set_title('Balance Oferta-Demanda y Nivel de Servicio', fontsize=14, pad=15)

    # Leyendas
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2,
              loc='lower left', ncol=4, framealpha=0.95)

    ax3.set_xlim(0, 364)
    ax3_twin.set_ylim(0, 105)
    ax3.grid(True, alpha=0.25)
    ax3.tick_params(axis='y', labelcolor=COLORS_WES['primary'])
    ax3_twin.tick_params(axis='y', labelcolor=COLORS_WES['accent5'])

    # Título general
    fig.suptitle('SISTEMA INTEGRADO: Cadena de Suministro GLP Región de Aysén',
                fontsize=16, fontweight='bold', y=0.995)

    plt.savefig(ruta_salida / '01_sistema_integrado.png',
               dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Gráfico 1 guardado: 01_sistema_integrado.png")
    plt.close()


def grafico_2_analisis_estacional(df: pd.DataFrame, ruta_salida: Path):
    """
    Gráfico 2: Análisis Estacional de Capacidad
    - Demanda mensual vs capacidad de suministro
    - Déficit/superávit por período
    - Satisfacción por estación
    """
    # Agregar por períodos de 30 días (meses aprox)
    df['mes'] = (df['dia'] // 30).clip(0, 11)

    agregado = df.groupby('mes').agg({
        'demanda_granel': 'sum',
        'demanda_envasado': 'sum',
        'flujo_recepcion_hub': 'sum',
        'satisfaccion_granel': 'mean',
        'satisfaccion_envasado': 'mean',
        'desabastecimiento_granel': 'sum',
        'desabastecimiento_envasado': 'sum'
    }).reset_index()

    agregado['demanda_total'] = agregado['demanda_granel'] + agregado['demanda_envasado']
    agregado['deficit'] = agregado['demanda_total'] - agregado['flujo_recepcion_hub']
    agregado['satisfaccion_promedio'] = (agregado['satisfaccion_granel'] +
                                         agregado['satisfaccion_envasado']) / 2 * 100
    agregado['desabastecimientos_total'] = (agregado['desabastecimiento_granel'] +
                                           agregado['desabastecimiento_envasado'])

    # Nombres de meses
    meses_etiquetas = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                       'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']

    fig = plt.figure(figsize=(16, 9))
    gs = GridSpec(2, 2, height_ratios=[1.5, 1], width_ratios=[1.5, 1],
                  hspace=0.3, wspace=0.3)

    # ========== PANEL 1: Demanda vs Suministro mensual ==========
    ax1 = fig.add_subplot(gs[0, :])

    x = np.arange(len(agregado))
    width = 0.35

    # Barras de demanda y suministro
    bars1 = ax1.bar(x - width/2, agregado['demanda_total'], width,
                    label='Demanda Total', color=COLORS_WES['accent3'], alpha=0.8,
                    edgecolor='black', linewidth=0.8)
    bars2 = ax1.bar(x + width/2, agregado['flujo_recepcion_hub'], width,
                    label='Suministro (recepción)', color=COLORS_WES['secondary'],
                    alpha=0.8, edgecolor='black', linewidth=0.8)

    # Marcar zonas estacionales con colores de fondo
    ax1.axvspan(-0.5, 2.5, alpha=0.08, color='orange', label='Verano')
    ax1.axvspan(2.5, 8.5, alpha=0.12, color='blue', label='Otoño-Invierno')
    ax1.axvspan(8.5, 11.5, alpha=0.08, color='orange', label='Primavera-Verano')

    # Eje secundario para déficit
    ax1_twin = ax1.twinx()
    line_deficit = ax1_twin.plot(x, agregado['deficit'],
                                 color='#E76F51', linewidth=3,
                                 marker='o', markersize=8,
                                 label='Déficit (Demanda - Suministro)',
                                 zorder=10)
    ax1_twin.axhline(y=0, color='black', linestyle='-', linewidth=0.8, alpha=0.4)
    ax1_twin.fill_between(x, 0, agregado['deficit'],
                          where=(agregado['deficit'] > 0),
                          color='#E76F51', alpha=0.2, interpolate=True)

    ax1.set_xlabel('Mes', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Volumen Mensual (TM)', fontsize=12, fontweight='bold')
    ax1_twin.set_ylabel('Déficit (TM)', fontsize=12, fontweight='bold', color='#E76F51')
    ax1.set_title('Análisis Estacional: Demanda vs Capacidad de Suministro',
                  fontsize=14, pad=15)
    ax1.set_xticks(x)
    ax1.set_xticklabels(meses_etiquetas)

    # Combinar leyendas
    lines1, labels1 = ax1.get_legend_handles_labels()
    ax1.legend(lines1 + line_deficit, labels1 + ['Déficit (Demanda - Suministro)'],
              loc='upper left', ncol=3, framealpha=0.95)

    ax1_twin.tick_params(axis='y', labelcolor='#E76F51')
    ax1.grid(True, alpha=0.25, axis='y')

    # ========== PANEL 2: Satisfacción por mes ==========
    ax2 = fig.add_subplot(gs[1, 0])

    bars = ax2.bar(x, agregado['satisfaccion_promedio'],
                   color=[COLORS_WES['secondary'] if s >= 95
                         else COLORS_WES['accent1'] if s >= 85
                         else COLORS_WES['accent3']
                         for s in agregado['satisfaccion_promedio']],
                   alpha=0.85, edgecolor='black', linewidth=0.8)

    ax2.axhline(y=95, color='#E76F51', linestyle='--', linewidth=2,
               alpha=0.7, label='Objetivo 95%')
    ax2.set_ylabel('Satisfacción (%)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Mes', fontsize=11, fontweight='bold')
    ax2.set_title('Tasa de Satisfacción Mensual', fontsize=13, pad=10)
    ax2.set_xticks(x)
    ax2.set_xticklabels(meses_etiquetas, rotation=45)
    ax2.set_ylim(0, 105)
    ax2.legend(framealpha=0.9)
    ax2.grid(True, alpha=0.25, axis='y')

    # Agregar valores sobre barras
    for i, (bar, val) in enumerate(zip(bars, agregado['satisfaccion_promedio'])):
        ax2.text(bar.get_x() + bar.get_width()/2, val + 2,
                f'{val:.1f}%', ha='center', fontsize=8, fontweight='bold')

    # ========== PANEL 3: Eventos de desabastecimiento por mes ==========
    ax3 = fig.add_subplot(gs[1, 1])

    bars_desabasto = ax3.bar(x, agregado['desabastecimientos_total'],
                             color=COLORS_WES['accent3'], alpha=0.8,
                             edgecolor='black', linewidth=0.8)

    ax3.set_ylabel('Días con\ndesabastecimiento', fontsize=11, fontweight='bold')
    ax3.set_xlabel('Mes', fontsize=11, fontweight='bold')
    ax3.set_title('Días con Desabastecimiento', fontsize=13, pad=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(meses_etiquetas, rotation=45)
    ax3.grid(True, alpha=0.25, axis='y')

    # Agregar valores
    for bar, val in zip(bars_desabasto, agregado['desabastecimientos_total']):
        if val > 0:
            ax3.text(bar.get_x() + bar.get_width()/2, val + 0.3,
                    f'{int(val)}', ha='center', fontsize=9, fontweight='bold')

    # Título general
    fig.suptitle('ANÁLISIS ESTACIONAL: Capacidad del Sistema y Nivel de Servicio',
                fontsize=16, fontweight='bold', y=0.995)

    plt.savefig(ruta_salida / '02_analisis_estacional.png',
               dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Gráfico 2 guardado: 02_analisis_estacional.png")
    plt.close()


def grafico_3_mapa_calor_sistema(df: pd.DataFrame, ruta_salida: Path):
    """
    Gráfico 3: Mapa de Calor del Estado del Sistema
    - Heatmap de estado operacional por etapa y tiempo
    - Muestra patrones de quiebres de stock
    - Utilización de inventarios
    """
    fig = plt.figure(figsize=(16, 10))
    gs = GridSpec(3, 1, height_ratios=[1, 1, 1.2], hspace=0.35)

    # Preparar datos para heatmap (cada 7 días para reducir tamaño)
    df_semanal = df.iloc[::7].copy()
    semanas = len(df_semanal)

    # ========== PANEL 1: Heatmap de Quiebres de Stock ==========
    ax1 = fig.add_subplot(gs[0])

    # Matriz de quiebres (1 = quiebre, 0 = OK)
    matriz_quiebres = np.array([
        df_semanal['quiebre_stock_hub_granel'].astype(int),
        df_semanal['quiebre_stock_hub_envasado'].astype(int),
        df_semanal['quiebre_stock_cdes'].astype(int),
        df_semanal['desabastecimiento_granel'].astype(int),
        df_semanal['desabastecimiento_envasado'].astype(int),
    ])

    # Crear heatmap
    im1 = ax1.imshow(matriz_quiebres, aspect='auto', cmap='RdYlGn_r',
                     interpolation='nearest', vmin=0, vmax=1)

    ax1.set_yticks(range(5))
    ax1.set_yticklabels(['Hub Granel', 'Hub Envasado', 'Red CDEs',
                         'Desabasto Granel', 'Desabasto Envasado'],
                        fontsize=10)
    ax1.set_xlabel('Semana del año', fontsize=11, fontweight='bold')
    ax1.set_title('Mapa de Quiebres de Stock y Desabastecimientos',
                  fontsize=13, pad=12)

    # Colorbar
    cbar1 = plt.colorbar(im1, ax=ax1, fraction=0.02, pad=0.02)
    cbar1.set_ticks([0, 1])
    cbar1.set_ticklabels(['OK', 'Quiebre'])

    # Marcar semanas
    xticks_pos = [0, 13, 26, 39, 52]
    xticks_labels = ['Sem 1', 'Sem 14', 'Sem 27', 'Sem 40', 'Sem 52']
    ax1.set_xticks([i for i in range(0, semanas, 4)])
    ax1.set_xticklabels([f'{i//4 + 1}' for i in range(0, semanas, 4)], fontsize=8)

    # ========== PANEL 2: Heatmap de Nivel de Inventarios (% capacidad) ==========
    ax2 = fig.add_subplot(gs[1])

    # Capacidades conocidas
    cap_hub_granel = 431
    cap_hub_envasado = 140
    cap_cdes = 161.3

    # Calcular porcentajes de utilización
    util_hub_granel = (df_semanal['inv_hub_granel'] / cap_hub_granel * 100).values
    util_hub_envasado = (df_semanal['inv_hub_envasado'] / cap_hub_envasado * 100).values
    util_cdes = (df_semanal['inv_cdes'] / cap_cdes * 100).values

    matriz_utilizacion = np.array([
        util_hub_granel,
        util_hub_envasado,
        util_cdes,
    ])

    # Crear heatmap
    im2 = ax2.imshow(matriz_utilizacion, aspect='auto', cmap='RdYlGn',
                     interpolation='bilinear', vmin=0, vmax=100)

    ax2.set_yticks(range(3))
    ax2.set_yticklabels(['Hub Granel', 'Hub Envasado', 'Red CDEs'], fontsize=10)
    ax2.set_xlabel('Semana del año', fontsize=11, fontweight='bold')
    ax2.set_title('Mapa de Utilización de Inventarios (% de capacidad)',
                  fontsize=13, pad=12)

    # Colorbar
    cbar2 = plt.colorbar(im2, ax=ax2, fraction=0.02, pad=0.02)
    cbar2.set_label('% Capacidad', rotation=270, labelpad=20, fontweight='bold')

    ax2.set_xticks([i for i in range(0, semanas, 4)])
    ax2.set_xticklabels([f'{i//4 + 1}' for i in range(0, semanas, 4)], fontsize=8)

    # ========== PANEL 3: Timeline con métricas clave ==========
    ax3 = fig.add_subplot(gs[2])

    # Agregado semanal
    df['semana'] = df['dia'] // 7
    semanal_agg = df.groupby('semana').agg({
        'camiones_en_ruta': 'mean',
        'viajes_completados': 'sum',
        'flujo_recepcion_hub': 'sum',
        'demanda_granel': 'sum',
        'demanda_envasado': 'sum',
    }).reset_index()

    semanal_agg['demanda_total'] = semanal_agg['demanda_granel'] + semanal_agg['demanda_envasado']

    # Gráfico de líneas múltiples
    ax3_twin = ax3.twinx()

    # Demanda vs suministro
    ax3.plot(semanal_agg['semana'], semanal_agg['demanda_total'],
            color=COLORS_WES['accent3'], linewidth=3,
            label='Demanda Total Semanal', alpha=0.9, marker='o', markersize=5)
    ax3.plot(semanal_agg['semana'], semanal_agg['flujo_recepcion_hub'],
            color=COLORS_WES['secondary'], linewidth=3,
            label='Suministro Semanal', alpha=0.9, marker='s', markersize=5)

    # Viajes en eje secundario
    ax3_twin.bar(semanal_agg['semana'], semanal_agg['viajes_completados'],
                alpha=0.3, color=COLORS_WES['accent4'],
                label='Viajes Completados', width=0.8)

    # Zonas estacionales
    ax3.axvspan(0, 13, alpha=0.05, color='orange')
    ax3.axvspan(13, 39, alpha=0.08, color='blue')
    ax3.axvspan(39, 52, alpha=0.05, color='orange')

    ax3.set_xlabel('Semana del año', fontsize=12, fontweight='bold')
    ax3.set_ylabel('Volumen Semanal (TM)', fontsize=11, fontweight='bold',
                  color=COLORS_WES['primary'])
    ax3_twin.set_ylabel('Viajes Completados', fontsize=11, fontweight='bold',
                       color=COLORS_WES['accent4'])
    ax3.set_title('Timeline Operacional: Demanda, Suministro y Actividad de Transporte',
                  fontsize=13, pad=12)

    # Leyendas combinadas
    lines1, labels1 = ax3.get_legend_handles_labels()
    lines2, labels2 = ax3_twin.get_legend_handles_labels()
    ax3.legend(lines1 + lines2, labels1 + labels2,
              loc='upper left', ncol=3, framealpha=0.95)

    ax3.set_xlim(0, 52)
    ax3.grid(True, alpha=0.25, axis='y')
    ax3.tick_params(axis='y', labelcolor=COLORS_WES['primary'])
    ax3_twin.tick_params(axis='y', labelcolor=COLORS_WES['accent4'])

    # Título general
    fig.suptitle('DIAGNÓSTICO DEL SISTEMA: Análisis Temporal de Estado Operacional',
                fontsize=16, fontweight='bold', y=0.995)

    plt.savefig(ruta_salida / '03_diagnostico_sistema.png',
               dpi=300, bbox_inches='tight', facecolor='white')
    print(f"✓ Gráfico 3 guardado: 03_diagnostico_sistema.png")
    plt.close()


def main():
    """Función principal."""
    print("=" * 80)
    print("VISUALIZACIÓN INTEGRADA - SIMULACIÓN GLP AYSÉN")
    print("=" * 80)

    # Rutas
    base_path = Path(__file__).parent.parent
    ruta_json = base_path / "results" / "simulacion_base_resultados.json"
    ruta_parquet = base_path / "results" / "simulacion_base_series_temporales.parquet"
    ruta_graficos = base_path / "results" / "graficos"

    # Validar
    if not ruta_json.exists():
        print(f"ERROR: No se encuentra {ruta_json}")
        return

    if not ruta_parquet.exists():
        print(f"ERROR: No se encuentra {ruta_parquet}")
        return

    # Cargar datos
    print(f"Cargando datos...")
    resultados, df = cargar_datos(ruta_json, ruta_parquet)
    print(f"  ✓ {len(df)} días de datos cargados")

    # Crear directorio
    ruta_graficos.mkdir(exist_ok=True, parents=True)

    print(f"\nGenerando 3 gráficos integrados...")
    print("-" * 80)

    # Generar gráficos
    grafico_1_sistema_integrado(df, ruta_graficos)
    grafico_2_analisis_estacional(df, ruta_graficos)
    grafico_3_mapa_calor_sistema(df, ruta_graficos)

    print("-" * 80)
    print(f"\n✓ Proceso completado exitosamente")
    print(f"✓ Ubicación: {ruta_graficos}")
    print("=" * 80)


if __name__ == "__main__":
    main()
