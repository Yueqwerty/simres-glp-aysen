"""
Generacion de Figuras Profesionales para Tesis

Este script genera visualizaciones de alta calidad con paletas de colores
inspiradas en las peliculas de Wes Anderson, optimizadas para publicacion academica.

Formatos de salida:
- SVG (vectorial, escalable)
- PDF (publication-ready)
- PNG (alta resolucion, 300 DPI)

Autor: Carlos Subiabre
Institucion: Universidad de Chile / Universidad Austral de Chile
"""
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import seaborn as sns
from scipy import stats
import warnings

warnings.filterwarnings('ignore')

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

# Configuracion global de matplotlib para calidad profesional
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.family'] = 'serif'
plt.rcParams['font.serif'] = ['Times New Roman', 'DejaVu Serif']
plt.rcParams['font.size'] = 10
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['figure.titlesize'] = 13
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.alpha'] = 0.3
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['axes.axisbelow'] = True

# Paletas de colores Wes Anderson profesionales
PALETA_WES_ANDERSON = {
    'grand_budapest': ['#F1BB7B', '#FD6467', '#5B1A18', '#D67236'],
    'moonrise': ['#F4DF4E', '#949398', '#ED6A5A', '#9A8822'],
    'royal_tenenbaums': ['#899DA4', '#C93312', '#FAEFD1', '#DC863B'],
    'darjeeling': ['#FF0000', '#F1BB7B', '#00A08A', '#F98400'],
    'rushmore': ['#E1BD6D', '#EABE94', '#0B775E', '#35274A'],
    'fantastic_fox': ['#DD8D29', '#E2D200', '#46ACC8', '#E58601'],
    'academic_mix': ['#00A08A', '#F98400', '#5B1A18', '#046C9A', '#C93312', '#899DA4']
}

# Paleta principal para la tesis (mezcla academica)
COLORES_PRINCIPALES = PALETA_WES_ANDERSON['academic_mix']


class GeneradorFigurasTesis:
    """Generador de figuras profesionales para tesis."""

    def __init__(self, directorioResultados: Path, directorioSalida: Path):
        self.dirResultados = directorioResultados
        self.dirSalida = directorioSalida
        self.dirSalida.mkdir(parents=True, exist_ok=True)

        # Cargar datos
        self.df = pd.read_csv(self.dirResultados / 'resultados_montecarlo.csv')
        self.resumen = pd.read_csv(self.dirResultados / 'resumen_estadisticas.csv')
        self.intervalos = pd.read_csv(self.dirResultados / 'intervalos_confianza.csv')

        print(f"Datos cargados: {len(self.df)} observaciones")
        print(f"Configuraciones: {self.df['config_id'].nunique()}")

    def generarTodasLasFiguras(self):
        """Genera todas las figuras para la tesis."""
        print("\n" + "="*70)
        print("GENERACION DE FIGURAS PROFESIONALES PARA TESIS")
        print("="*70 + "\n")

        self.figura01_distribucionesViolin()
        self.figura02_efectosPrincipales()
        self.figura03_heatmapInteracciones()
        self.figura04_comparacionConfiguraciones()
        self.figura05_analisisSensibilidad()
        self.figura06_evolucionTemporal()

        print("\n" + "="*70)
        print("GENERACION COMPLETADA")
        print(f"Figuras guardadas en: {self.dirSalida}")
        print("="*70 + "\n")

    def figura01_distribucionesViolin(self):
        """Figura 1: Distribuciones de nivel de servicio por configuracion."""
        print("Generando Figura 1: Distribuciones (Violin Plots)...")

        fig, ax = plt.subplots(figsize=(12, 6))

        # Preparar datos
        self.df['capacidad_label'] = self.df['capacidad_tm'].map({
            431: 'Status Quo\n(431 TM)',
            681: 'Propuesta\n(681 TM)'
        })
        self.df['disrupcion_label'] = self.df['duracion_max_dias'].map({
            7: 'Corta\n(7 dias)',
            14: 'Media\n(14 dias)',
            21: 'Larga\n(21 dias)'
        })

        # Violin plot con colores Wes Anderson
        partes = ax.violinplot(
            [self.df[self.df['config_id'] == i]['nivel_servicio_pct'].values
             for i in range(1, 7)],
            positions=range(1, 7),
            widths=0.7,
            showmeans=True,
            showmedians=True
        )

        # Colorear violines
        for i, pc in enumerate(partes['bodies']):
            color = COLORES_PRINCIPALES[i % len(COLORES_PRINCIPALES)]
            pc.set_facecolor(color)
            pc.set_alpha(0.7)

        partes['cmeans'].set_color('black')
        partes['cmeans'].set_linewidth(2)
        partes['cmedians'].set_color('darkred')
        partes['cmedians'].set_linewidth(1.5)

        # Etiquetas de configuraciones
        etiquetas = [
            'SQ + Corta', 'SQ + Media', 'SQ + Larga',
            'Prop + Corta', 'Prop + Media', 'Prop + Larga'
        ]

        ax.set_xticks(range(1, 7))
        ax.set_xticklabels(etiquetas, rotation=45, ha='right')
        ax.set_ylabel('Nivel de Servicio (%)', fontweight='bold')
        ax.set_xlabel('Configuracion', fontweight='bold')
        ax.set_title('Distribucion del Nivel de Servicio por Configuracion\n' +
                     'Experimento Monte Carlo (n=1,000 replicas por configuracion)',
                     fontweight='bold', pad=20)

        # Linea de referencia 95%
        ax.axhline(y=95, color='red', linestyle='--', linewidth=1, alpha=0.6,
                   label='Umbral 95%')

        ax.legend(loc='lower left')
        ax.set_ylim([80, 102])
        ax.grid(True, alpha=0.3)

        plt.tight_layout()
        self.guardarFigura(fig, 'fig01_distribuciones_violin')
        plt.close()

    def figura02_efectosPrincipales(self):
        """Figura 2: Efectos principales con intervalos de confianza."""
        print("Generando Figura 2: Efectos Principales...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Efecto de Capacidad
        efecto_cap = self.df.groupby('capacidad_tm')['nivel_servicio_pct'].agg(['mean', 'std', 'count'])
        efecto_cap['se'] = efecto_cap['std'] / np.sqrt(efecto_cap['count'])
        efecto_cap['ci'] = 1.96 * efecto_cap['se']

        capacidades = efecto_cap.index.tolist()
        medias_cap = efecto_cap['mean'].values
        errores_cap = efecto_cap['ci'].values

        ax1.errorbar(capacidades, medias_cap, yerr=errores_cap,
                     fmt='o-', linewidth=2.5, markersize=10,
                     color=COLORES_PRINCIPALES[0], markerfacecolor=COLORES_PRINCIPALES[1],
                     markeredgewidth=2, markeredgecolor=COLORES_PRINCIPALES[0],
                     capsize=8, capthick=2, elinewidth=2,
                     label='Media ± IC 95%')

        for i, (cap, media) in enumerate(zip(capacidades, medias_cap)):
            ax1.text(cap, media + 1.5, f'{media:.1f}%',
                     ha='center', va='bottom', fontweight='bold', fontsize=10)

        ax1.set_xlabel('Capacidad de Almacenamiento (TM)', fontweight='bold')
        ax1.set_ylabel('Nivel de Servicio Promedio (%)', fontweight='bold')
        ax1.set_title('Efecto Principal: Capacidad', fontweight='bold', pad=15)
        ax1.set_xticks(capacidades)
        ax1.set_xticklabels(['Status Quo\n(431 TM)', 'Propuesta\n(681 TM)'])
        ax1.grid(True, alpha=0.3)
        ax1.legend()
        ax1.set_ylim([85, 100])

        # Efecto de Duracion de Disrupciones
        efecto_dur = self.df.groupby('duracion_max_dias')['nivel_servicio_pct'].agg(['mean', 'std', 'count'])
        efecto_dur['se'] = efecto_dur['std'] / np.sqrt(efecto_dur['count'])
        efecto_dur['ci'] = 1.96 * efecto_dur['se']

        duraciones = efecto_dur.index.tolist()
        medias_dur = efecto_dur['mean'].values
        errores_dur = efecto_dur['ci'].values

        ax2.errorbar(duraciones, medias_dur, yerr=errores_dur,
                     fmt='s-', linewidth=2.5, markersize=10,
                     color=COLORES_PRINCIPALES[2], markerfacecolor=COLORES_PRINCIPALES[3],
                     markeredgewidth=2, markeredgecolor=COLORES_PRINCIPALES[2],
                     capsize=8, capthick=2, elinewidth=2,
                     label='Media ± IC 95%')

        for i, (dur, media) in enumerate(zip(duraciones, medias_dur)):
            ax2.text(dur, media - 1.5, f'{media:.1f}%',
                     ha='center', va='top', fontweight='bold', fontsize=10)

        ax2.set_xlabel('Duracion Maxima de Disrupciones (dias)', fontweight='bold')
        ax2.set_ylabel('Nivel de Servicio Promedio (%)', fontweight='bold')
        ax2.set_title('Efecto Principal: Disrupciones', fontweight='bold', pad=15)
        ax2.set_xticks(duraciones)
        ax2.set_xticklabels(['Corta\n(7 dias)', 'Media\n(14 dias)', 'Larga\n(21 dias)'])
        ax2.grid(True, alpha=0.3)
        ax2.legend()
        ax2.set_ylim([85, 100])

        plt.tight_layout()
        self.guardarFigura(fig, 'fig02_efectos_principales')
        plt.close()

    def figura03_heatmapInteracciones(self):
        """Figura 3: Heatmap de interacciones Capacidad x Duracion."""
        print("Generando Figura 3: Heatmap de Interacciones...")

        # Crear matriz de medias
        pivot = self.df.pivot_table(
            values='nivel_servicio_pct',
            index='duracion_max_dias',
            columns='capacidad_tm',
            aggfunc='mean'
        )

        fig, ax = plt.subplots(figsize=(10, 7))

        # Heatmap con paleta Wes Anderson
        cmap = sns.diverging_palette(10, 220, sep=80, as_cmap=True)
        im = ax.imshow(pivot.values, cmap=cmap, aspect='auto',
                       vmin=85, vmax=100, interpolation='nearest')

        # Configurar ejes
        ax.set_xticks(range(len(pivot.columns)))
        ax.set_xticklabels(['Status Quo (431 TM)', 'Propuesta (681 TM)'])
        ax.set_yticks(range(len(pivot.index)))
        ax.set_yticklabels(['Corta (7 dias)', 'Media (14 dias)', 'Larga (21 dias)'])

        ax.set_xlabel('Capacidad de Almacenamiento', fontweight='bold', fontsize=12)
        ax.set_ylabel('Duracion Maxima de Disrupciones', fontweight='bold', fontsize=12)
        ax.set_title('Nivel de Servicio: Interaccion Capacidad × Duracion de Disrupciones\n' +
                     '(valores promedio de 1,000 replicas por celda)',
                     fontweight='bold', pad=20, fontsize=13)

        # Anotar valores
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                valor = pivot.values[i, j]
                ax.text(j, i, f'{valor:.1f}%',
                        ha='center', va='center',
                        color='white' if valor < 92 else 'black',
                        fontweight='bold', fontsize=11)

        # Colorbar
        cbar = plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label('Nivel de Servicio (%)', rotation=270, labelpad=20, fontweight='bold')

        plt.tight_layout()
        self.guardarFigura(fig, 'fig03_heatmap_interacciones')
        plt.close()

    def figura04_comparacionConfiguraciones(self):
        """Figura 4: Comparacion directa de configuraciones con boxplots."""
        print("Generando Figura 4: Comparacion de Configuraciones...")

        fig, ax = plt.subplots(figsize=(14, 7))

        # Preparar datos
        datos_plot = [self.df[self.df['config_id'] == i]['nivel_servicio_pct'].values
                      for i in range(1, 7)]

        # Boxplot con colores Wes Anderson
        bp = ax.boxplot(datos_plot, positions=range(1, 7),
                        widths=0.6, patch_artist=True,
                        showmeans=True,
                        meanprops=dict(marker='D', markerfacecolor='red', markersize=8),
                        medianprops=dict(linewidth=2, color='darkred'),
                        boxprops=dict(linewidth=1.5),
                        whiskerprops=dict(linewidth=1.5),
                        capprops=dict(linewidth=1.5))

        # Colorear cajas
        for i, box in enumerate(bp['boxes']):
            color = COLORES_PRINCIPALES[i % len(COLORES_PRINCIPALES)]
            box.set_facecolor(color)
            box.set_alpha(0.7)

        # Etiquetas
        etiquetas = [
            'Status Quo\n+ Corta',
            'Status Quo\n+ Media',
            'Status Quo\n+ Larga',
            'Propuesta\n+ Corta',
            'Propuesta\n+ Media',
            'Propuesta\n+ Larga'
        ]

        ax.set_xticks(range(1, 7))
        ax.set_xticklabels(etiquetas, fontsize=10)
        ax.set_ylabel('Nivel de Servicio (%)', fontweight='bold', fontsize=12)
        ax.set_xlabel('Configuracion', fontweight='bold', fontsize=12)
        ax.set_title('Comparacion de Configuraciones del Diseno Factorial 2×3\n' +
                     'Box plots con mediana (linea roja) y media (rombo rojo)',
                     fontweight='bold', pad=20, fontsize=13)

        # Lineas de referencia
        ax.axhline(y=95, color='red', linestyle='--', linewidth=1.5, alpha=0.5,
                   label='Umbral 95%')
        ax.axhline(y=90, color='orange', linestyle=':', linewidth=1.5, alpha=0.5,
                   label='Umbral 90%')

        ax.legend(loc='lower left', fontsize=10)
        ax.set_ylim([80, 102])
        ax.grid(True, alpha=0.3, axis='y')

        plt.tight_layout()
        self.guardarFigura(fig, 'fig04_comparacion_configuraciones')
        plt.close()

    def figura05_analisisSensibilidad(self):
        """Figura 5: Analisis de sensibilidad (tornado diagram)."""
        print("Generando Figura 5: Analisis de Sensibilidad...")

        # Calcular rangos de variacion
        base = self.df['nivel_servicio_pct'].mean()

        # Efecto capacidad
        ns_cap_bajo = self.df[self.df['capacidad_tm'] == 431]['nivel_servicio_pct'].mean()
        ns_cap_alto = self.df[self.df['capacidad_tm'] == 681]['nivel_servicio_pct'].mean()

        # Efecto disrupciones
        ns_dur_bajo = self.df[self.df['duracion_max_dias'] == 7]['nivel_servicio_pct'].mean()
        ns_dur_alto = self.df[self.df['duracion_max_dias'] == 21]['nivel_servicio_pct'].mean()

        # Calcular variaciones
        var_cap = abs(ns_cap_alto - ns_cap_bajo)
        var_dur = abs(ns_dur_alto - ns_dur_bajo)

        parametros = ['Duracion Disrupciones\n(7 → 21 dias)',
                      'Capacidad Almacenamiento\n(431 → 681 TM)']
        variaciones = [var_dur, var_cap]

        # Ordenar por magnitud
        orden = np.argsort(variaciones)[::-1]
        parametros = [parametros[i] for i in orden]
        variaciones = [variaciones[i] for i in orden]

        fig, ax = plt.subplots(figsize=(10, 6))

        # Barras horizontales
        y_pos = np.arange(len(parametros))
        colores_tornado = [COLORES_PRINCIPALES[2], COLORES_PRINCIPALES[0]]

        bars = ax.barh(y_pos, variaciones, color=colores_tornado, alpha=0.8,
                       edgecolor='black', linewidth=1.5)

        # Anotar valores
        for i, (bar, val) in enumerate(zip(bars, variaciones)):
            ax.text(val + 0.3, i, f'{val:.2f}%',
                    va='center', fontweight='bold', fontsize=11)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(parametros, fontsize=11)
        ax.set_xlabel('Variacion en Nivel de Servicio (puntos porcentuales)',
                      fontweight='bold', fontsize=12)
        ax.set_title('Analisis de Sensibilidad: Impacto de Parametros en Nivel de Servicio\n' +
                     '(tornado diagram ordenado por magnitud de efecto)',
                     fontweight='bold', pad=20, fontsize=13)
        ax.grid(True, alpha=0.3, axis='x')
        ax.set_xlim([0, max(variaciones) * 1.2])

        plt.tight_layout()
        self.guardarFigura(fig, 'fig05_analisis_sensibilidad')
        plt.close()

    def figura06_evolucionTemporal(self):
        """Figura 6: Evolucion temporal de una simulacion representativa."""
        print("Generando Figura 6: Evolucion Temporal (ejemplo)...")

        # Ejecutar una simulacion para obtener serie temporal
        from modelo import ConfiguracionSimulacion, SimulacionGlpAysen

        config_ejemplo = ConfiguracionSimulacion(
            capacidadHubTm=431.0,
            puntoReordenTm=431.0 * 0.50,
            cantidadPedidoTm=431.0 * 0.50,
            inventarioInicialTm=431.0 * 0.60,
            duracionDisrupcionMaxDias=14.0,
            duracionDisrupcionModeDias=7.0,
            semillaAleatoria=42
        )

        import logging
        logging.basicConfig(level=logging.WARNING)

        sim = SimulacionGlpAysen(config_ejemplo)
        sim.run()

        # Extraer metricas diarias
        dias = [m.dia for m in sim.metricasDiarias]
        inventario = [m.inventarioTm for m in sim.metricasDiarias]
        demanda = [m.demandaTm for m in sim.metricasDiarias]
        rutaBloqueada = [m.rutaBloqueada for m in sim.metricasDiarias]

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

        # Panel superior: Inventario
        ax1.plot(dias, inventario, linewidth=2, color=COLORES_PRINCIPALES[0],
                 label='Nivel de Inventario')
        ax1.axhline(y=config_ejemplo.puntoReordenTm, color='red', linestyle='--',
                    linewidth=1.5, label=f'Punto de Reorden ({config_ejemplo.puntoReordenTm:.0f} TM)')
        ax1.fill_between(dias, 0, inventario, alpha=0.3, color=COLORES_PRINCIPALES[0])

        # Marcar periodos bloqueados
        periodos_bloqueados = []
        inicio_bloqueo = None
        for i, bloqueada in enumerate(rutaBloqueada):
            if bloqueada and inicio_bloqueo is None:
                inicio_bloqueo = i
            elif not bloqueada and inicio_bloqueo is not None:
                periodos_bloqueados.append((inicio_bloqueo, i))
                inicio_bloqueo = None

        for inicio, fin in periodos_bloqueados:
            ax1.axvspan(inicio, fin, color='red', alpha=0.15)

        ax1.set_ylabel('Inventario (TM)', fontweight='bold', fontsize=11)
        ax1.set_title('Evolucion Temporal del Sistema: Ejemplo Ilustrativo\n' +
                      'Configuracion: Status Quo + Disrupciones Medias (14 dias)',
                      fontweight='bold', pad=20, fontsize=13)
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3)
        ax1.set_ylim([0, config_ejemplo.capacidadHubTm * 1.05])

        # Panel inferior: Demanda
        ax2.bar(dias, demanda, width=1.0, color=COLORES_PRINCIPALES[1], alpha=0.6,
                label='Demanda Diaria')
        ax2.axhline(y=config_ejemplo.demandaBaseDiariaTm, color='black', linestyle=':',
                    linewidth=1.5, label=f'Demanda Base ({config_ejemplo.demandaBaseDiariaTm:.0f} TM/dia)')

        # Marcar periodos bloqueados
        for inicio, fin in periodos_bloqueados:
            ax2.axvspan(inicio, fin, color='red', alpha=0.15, label='Ruta Bloqueada' if inicio == periodos_bloqueados[0][0] else '')

        ax2.set_xlabel('Dia de Simulacion', fontweight='bold', fontsize=11)
        ax2.set_ylabel('Demanda (TM/dia)', fontweight='bold', fontsize=11)
        ax2.legend(loc='upper right', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim([0, 365])

        plt.tight_layout()
        self.guardarFigura(fig, 'fig06_evolucion_temporal')
        plt.close()

    def guardarFigura(self, fig, nombre: str):
        """Guarda figura en multiples formatos de alta calidad."""
        formatos = ['svg', 'pdf', 'png']

        for formato in formatos:
            ruta = self.dirSalida / f'{nombre}.{formato}'
            if formato == 'png':
                fig.savefig(ruta, format=formato, dpi=300, bbox_inches='tight',
                           facecolor='white', edgecolor='none')
            else:
                fig.savefig(ruta, format=formato, bbox_inches='tight')

        print(f"  [OK] {nombre} guardado ({', '.join(formatos)})")


def main():
    """Punto de entrada principal."""
    basePath = Path(__file__).parent.parent

    dirResultados = basePath / 'results' / 'montecarlo'
    dirSalida = basePath / 'mitesis' / 'figuras'

    if not dirResultados.exists():
        print(f"ERROR: Directorio de resultados no encontrado: {dirResultados}")
        print("Ejecuta primero: python scripts/experimento_montecarlo.py")
        return

    generador = GeneradorFigurasTesis(dirResultados, dirSalida)
    generador.generarTodasLasFiguras()

    print(f"\nFiguras disponibles en formato SVG, PDF y PNG (300 DPI)")
    print(f"Listas para incluir en tu tesis LaTeX o Word")


if __name__ == "__main__":
    main()
