"""
Generador de diagramas de flujo profesionales para la tesis SimRes-GLP-Aysén.
Estilo: Draw.io profesional, limpio y académico.
"""
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle
import numpy as np

# === PALETA WES ANDERSON ===
# Inspirada en "The Grand Budapest Hotel", "Moonrise Kingdom" y "The Royal Tenenbaums"
COLORES = {
    # Colores principales Wes Anderson
    'rosa_pastel': '#F4C2C2',        # Rosa suave (Grand Budapest)
    'salmon': '#E8998D',              # Salmon vintage
    'amarillo_mostaza': '#F2CC8F',    # Mostaza suave
    'azul_pastel': '#81B29A',         # Verde azulado (Moonrise)
    'verde_menta': '#A8DADC',         # Menta claro
    'coral': '#EF9A9A',               # Coral suave
    'beige': '#F4E8C1',               # Beige cálido
    'lavanda': '#C5CAE9',             # Lavanda suave

    # Tonos más saturados para contraste
    'bordo': '#8B4049',               # Bordo profundo
    'azul_oscuro': '#3D5A80',         # Azul profundo
    'verde_bosque': '#6B8E23',        # Verde oliva
    'terracota': '#C17767',           # Terracota

    # Colores técnicos manteniendo paleta
    'azul_principal': '#5B9BD5',      # Azul más suave
    'verde_proceso': '#7ED321',       # Verde proceso
    'naranja_warning': '#F5A623',     # Naranja advertencia
    'rojo_error': '#E74C3C',          # Rojo error
    'morado_data': '#9575CD',         # Morado suave

    # Tonos pastel
    'azul_claro': '#D6EAF8',
    'verde_claro': '#D5F4E6',
    'amarillo_claro': '#FEF5E7',
    'naranja_claro': '#FAE5D3',
    'rojo_claro': '#FADBD8',
    'gris_claro': '#ECF0F1',

    # Estados
    'success': '#81B29A',
    'warning': '#F2CC8F',
    'danger': '#E8998D',
    'info': '#81B29A',

    # Texto
    'texto_oscuro': '#2C3E50',
    'texto_claro': '#FFFFFF',
    'texto_gris': '#7F8C8D',

    # Bordes
    'borde_oscuro': '#8B4049',
    'borde_claro': '#BDC3C7',
}

class DiagramadorTesis:
    """Genera diagramas de flujo estilo Draw.io para presentaciones académicas."""

    def __init__(self, estilo='profesional'):
        self.fig = None
        self.ax = None
        self.estilo = estilo

    def crear_lienzo(self, titulo, figsize=(18, 12)):
        """Crea lienzo con estilo profesional Draw.io."""
        self.fig, self.ax = plt.subplots(figsize=figsize, facecolor='white')
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 10)
        self.ax.axis('off')

        # Fondo sutil
        fondo = Rectangle((0, 0), 10, 10,
                         facecolor='#FAFBFC',
                         edgecolor='none',
                         zorder=0)
        self.ax.add_patch(fondo)

        # Título profesional estilo Draw.io
        self.ax.text(5, 9.6, titulo,
                    fontsize=22, weight='bold',
                    ha='center', va='top',
                    color=COLORES['borde_oscuro'],
                    family='sans-serif')

    def crear_caja(self, x, y, ancho, alto, texto, color, icono=None, borde_color=None):
        """Crea caja estilo Draw.io profesional."""
        if borde_color is None:
            borde_color = COLORES['borde_oscuro']

        # Sombra sutil estilo Draw.io
        sombra = FancyBboxPatch(
            (x + 0.03, y - 0.03), ancho, alto,
            boxstyle="round,pad=0.05",
            edgecolor='none',
            facecolor='#000000',
            alpha=0.08,
            zorder=1
        )
        self.ax.add_patch(sombra)

        # Caja principal con bordes más definidos
        caja = FancyBboxPatch(
            (x, y), ancho, alto,
            boxstyle="round,pad=0.05",
            edgecolor=borde_color,
            facecolor=color,
            linewidth=2,
            zorder=2
        )
        self.ax.add_patch(caja)

        # Determinar color de texto
        texto_color = COLORES['texto_claro'] if self._es_color_oscuro(color) else COLORES['texto_oscuro']

        # Icono opcional
        if icono:
            self.ax.text(x + ancho/2, y + alto*0.68, icono,
                        fontsize=16, ha='center', va='center',
                        color=texto_color, weight='bold')
            texto_y = y + alto*0.32
            fontsize_texto = 10
        else:
            texto_y = y + alto/2
            fontsize_texto = 11

        # Texto principal con mejor tipografía
        self.ax.text(x + ancho/2, texto_y, texto,
                    fontsize=fontsize_texto, ha='center', va='center',
                    color=texto_color,
                    weight='600',
                    family='sans-serif',
                    linespacing=1.3,
                    wrap=True)

    def crear_flecha(self, x1, y1, x2, y2, texto='', estilo='normal', color=None):
        """Crea flecha estilo Draw.io profesional."""
        if color is None:
            color = COLORES['borde_oscuro']

        # Determinar tipo de flecha
        if estilo == 'normal':
            arrowstyle = '->,head_width=0.4,head_length=0.8'
            linewidth = 2
        elif estilo == 'doble':
            arrowstyle = '<->,head_width=0.4,head_length=0.8'
            linewidth = 2
        elif estilo == 'decision':
            arrowstyle = '->,head_width=0.4,head_length=0.8'
            linewidth = 2.5
            color = COLORES['danger']

        flecha = FancyArrowPatch(
            (x1, y1), (x2, y2),
            arrowstyle=arrowstyle,
            color=color,
            linewidth=linewidth,
            connectionstyle="arc3,rad=0.05",
            zorder=3,
            mutation_scale=20
        )
        self.ax.add_patch(flecha)

        # Etiqueta con fondo
        if texto:
            mid_x = (x1 + x2) / 2
            mid_y = (y1 + y2) / 2

            # Fondo blanco con borde sutil
            bbox_props = dict(boxstyle="round,pad=0.4",
                            facecolor='white',
                            edgecolor=COLORES['borde_claro'],
                            linewidth=1,
                            alpha=0.95)

            self.ax.text(mid_x, mid_y, texto,
                        fontsize=9, ha='center', va='center',
                        color=COLORES['texto_oscuro'],
                        bbox=bbox_props,
                        weight='500',
                        style='italic')

    def crear_diamante(self, x, y, ancho, alto, texto, color, borde_color=None):
        """Crea rombo para decisiones estilo Draw.io."""
        if borde_color is None:
            borde_color = COLORES['warning']

        vertices = np.array([
            [x, y + alto/2],           # Izquierda
            [x + ancho/2, y + alto],   # Arriba
            [x + ancho, y + alto/2],   # Derecha
            [x + ancho/2, y]           # Abajo
        ])

        # Sombra sutil
        sombra_vertices = vertices + np.array([0.03, -0.03])
        sombra = mpatches.Polygon(sombra_vertices,
                                 closed=True,
                                 facecolor='#000000',
                                 alpha=0.08,
                                 zorder=1)
        self.ax.add_patch(sombra)

        # Diamante principal
        diamante = mpatches.Polygon(vertices,
                                   closed=True,
                                   edgecolor=borde_color,
                                   facecolor=color,
                                   linewidth=2,
                                   zorder=2)
        self.ax.add_patch(diamante)

        # Texto
        texto_color = COLORES['texto_claro'] if self._es_color_oscuro(color) else COLORES['texto_oscuro']
        self.ax.text(x + ancho/2, y + alto/2, texto,
                    fontsize=10, ha='center', va='center',
                    color=texto_color,
                    weight='600',
                    linespacing=1.3)

    def crear_cilindro(self, x, y, ancho, alto, texto, color, borde_color=None):
        """Crea cilindro para bases de datos estilo Draw.io."""
        from matplotlib.patches import Ellipse, Arc

        if borde_color is None:
            borde_color = COLORES['morado_data']

        # Elipse superior
        elipse_top = Ellipse((x + ancho/2, y + alto),
                            ancho/2, alto*0.15,
                            facecolor=color,
                            edgecolor=borde_color,
                            linewidth=2,
                            zorder=2)
        self.ax.add_patch(elipse_top)

        # Rectángulo central
        rect = Rectangle((x, y + alto*0.1), ancho, alto*0.8,
                        facecolor=color,
                        edgecolor='none',
                        zorder=1)
        self.ax.add_patch(rect)

        # Bordes laterales
        self.ax.plot([x, x], [y + alto*0.15, y + alto],
                    color=borde_color, linewidth=2, zorder=2)
        self.ax.plot([x + ancho, x + ancho], [y + alto*0.15, y + alto],
                    color=borde_color, linewidth=2, zorder=2)

        # Elipse inferior (parcial)
        arc = Arc((x + ancho/2, y + alto*0.15),
                 ancho, alto*0.3,
                 angle=0, theta1=180, theta2=360,
                 edgecolor=borde_color,
                 linewidth=2,
                 zorder=2)
        self.ax.add_patch(arc)

        # Texto
        texto_color = COLORES['texto_claro'] if self._es_color_oscuro(color) else COLORES['texto_oscuro']
        self.ax.text(x + ancho/2, y + alto/2, texto,
                    fontsize=10, ha='center', va='center',
                    color=texto_color,
                    weight='600',
                    linespacing=1.3)

    def _es_color_oscuro(self, color):
        """Determina si un color es oscuro para elegir color de texto."""
        colores_oscuros = [
            COLORES['azul_principal'],
            COLORES['verde_proceso'],
            COLORES['rojo_error'],
            COLORES['morado_data'],
            COLORES['success'],
            COLORES['warning'],
            COLORES['danger'],
            COLORES['info'],
            COLORES['borde_oscuro']
        ]
        return color in colores_oscuros

    def guardar(self, filename, dpi=300):
        """Guarda diagrama en alta resolución."""
        plt.tight_layout()
        plt.savefig(filename, dpi=dpi, bbox_inches='tight',
                   facecolor='white', edgecolor='none')
        print(f"[OK] Diagrama guardado: {filename}")
        plt.close()


def diagrama_1_flujo_principal():
    """Diagrama 1: Flujo principal de la simulación."""
    d = DiagramadorTesis()
    d.crear_lienzo('Arquitectura de Ejecución: Sistema de Simulación de Disrupciones', figsize=(18, 13))

    # Nivel 1: Inicio
    d.crear_caja(3.5, 8.5, 3, 0.6, 'INICIO\nCargar Configuración YAML',
                COLORES['info'])

    # Nivel 2: Inicialización de Componentes
    d.crear_caja(0.5, 7.2, 2, 0.8, 'Instanciar RNG\nnumpy.random',
                COLORES['verde_claro'], borde_color=COLORES['success'])
    d.crear_caja(3, 7.2, 2, 0.8, 'Inicializar SimPy\nEnvironment',
                COLORES['verde_claro'], borde_color=COLORES['success'])
    d.crear_caja(5.5, 7.2, 2, 0.8, 'Validar Schema\nYAML',
                COLORES['verde_claro'], borde_color=COLORES['success'])
    d.crear_caja(8, 7.2, 2, 0.8, 'Setup Observers\nPattern',
                COLORES['verde_claro'], borde_color=COLORES['success'])

    # Flechas Nivel 1 -> Nivel 2
    d.crear_flecha(4.2, 8.5, 1.5, 8.0, '', 'normal')
    d.crear_flecha(5, 8.5, 4, 8.0, '', 'normal')
    d.crear_flecha(5.8, 8.5, 6.5, 8.0, '', 'normal')
    d.crear_flecha(6.3, 8.5, 9, 8.0, '', 'normal')

    # Nivel 3: Instanciación de Entidades del Modelo
    d.crear_caja(0.3, 5.8, 1.5, 0.7, 'PlantaAlmacenamiento\nSimPy.Resource',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(2.2, 5.8, 1.5, 0.7, 'ProveedorExterno\nSimPy.Process',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(4.1, 5.8, 1.5, 0.7, 'FlotaCamiones[N]\nList[Vehicle]',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(6, 5.8, 1.5, 0.7, 'NodosDemanda\nDict[str, Node]',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(8, 5.8, 1.8, 0.7, 'GestorDisrupciones\n77 Perfiles',
                COLORES['rojo_claro'], borde_color=COLORES['danger'])

    # Flechas convergentes
    d.crear_flecha(1.5, 7.2, 1.05, 6.5, '', 'normal')
    d.crear_flecha(4, 7.2, 2.95, 6.5, '', 'normal')
    d.crear_flecha(6.5, 7.2, 4.85, 6.5, '', 'normal')
    d.crear_flecha(9, 7.2, 6.75, 6.5, '', 'normal')
    d.crear_flecha(9, 7.2, 8.9, 6.5, '', 'normal')

    # Nivel 4: Registro y Configuración
    d.crear_caja(2.5, 4.5, 5, 0.8, 'Registrar Entidades en Sistema de Disrupciones\nCargar Perfiles Estocásticos (TBA, Duración, Impacto)',
                COLORES['naranja_claro'], borde_color=COLORES['naranja_warning'])

    # Flechas convergencia a configuración
    d.crear_flecha(1.05, 5.8, 3.5, 5.3, 'register', 'normal')
    d.crear_flecha(2.95, 5.8, 4.2, 5.3, 'register', 'normal')
    d.crear_flecha(4.85, 5.8, 5, 5.3, 'register', 'normal')
    d.crear_flecha(6.75, 5.8, 5.8, 5.3, 'register', 'normal')
    d.crear_flecha(8.9, 5.8, 6.5, 5.3, 'attach', 'normal')

    # Nivel 5: Motor de Simulación
    d.crear_caja(3, 3.2, 4, 0.8, 'MOTOR DE SIMULACIÓN\nenv.run(until=T)',
                COLORES['azul_principal'])

    d.crear_flecha(5, 4.5, 5, 4.0, '', 'normal')

    # Nivel 6: Event Loop (Procesamiento Paralelo)
    d.crear_caja(0.2, 1.8, 2, 0.6, 'Process Events\nEntity.run()',
                COLORES['azul_claro'], borde_color=COLORES['info'])
    d.crear_caja(2.5, 1.8, 2, 0.6, 'Disruption Events\nState Machine',
                COLORES['rojo_claro'], borde_color=COLORES['danger'])
    d.crear_caja(4.8, 1.8, 2, 0.6, 'Monitor System\nObserver.notify()',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(7.1, 1.8, 2.7, 0.6, 'Metrics Aggregation\nCollector.update()',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])

    # Flechas paralelas
    d.crear_flecha(3.5, 3.2, 1.2, 2.4, 'yield', 'normal')
    d.crear_flecha(4.5, 3.2, 3.5, 2.4, 'timeout', 'normal')
    d.crear_flecha(5.5, 3.2, 5.8, 2.4, 'emit', 'normal')
    d.crear_flecha(6.5, 3.2, 8.45, 2.4, 'collect', 'normal')

    # Nivel 7: Persistencia de Datos
    d.crear_cilindro(2, 0.3, 2.5, 0.9, 'events.parquet\nDataFrame',
                    COLORES['azul_claro'])
    d.crear_cilindro(5, 0.3, 2.5, 0.9, 'metadata.json\nConfig + Stats',
                    COLORES['azul_claro'])
    d.crear_cilindro(7.5, 0.3, 2, 0.9, 'summary.csv\nKPIs',
                    COLORES['azul_claro'])

    # Flechas convergentes a almacenamiento
    d.crear_flecha(1.2, 1.8, 3, 1.2, 'write', 'normal')
    d.crear_flecha(3.5, 1.8, 4.5, 1.2, 'flush', 'normal')
    d.crear_flecha(5.8, 1.8, 6.2, 1.2, 'export', 'normal')
    d.crear_flecha(8.45, 1.8, 8, 1.2, 'save', 'normal')

    # Nota técnica
    d.ax.text(5, 0.05, 'Stack Tecnológico: SimPy (DES) | Observer Pattern | Factory Pattern | State Machine | NumPy | Pandas',
             fontsize=8, ha='center', style='italic',
             color=COLORES['texto_oscuro'], alpha=0.7)

    d.guardar('diagrama_1_flujo_principal.png')


def diagrama_2_ciclo_disrupcion():
    """Diagrama 2: Ciclo de vida de una disrupción."""
    d = DiagramadorTesis()
    d.crear_lienzo('State Machine: Ciclo de Vida de Disrupción Estocástica', figsize=(17, 11))

    # Estados (círculos como cajas redondeadas)
    d.crear_caja(1, 8, 1.8, 0.7, 'INACTIVE\nstate=0', COLORES['verde_claro'], borde_color=COLORES['success'])
    d.crear_caja(4, 8, 1.8, 0.7, 'PREPARING\nstate=1', COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(7, 8, 1.8, 0.7, 'ACTIVE\nstate=2', COLORES['rojo_claro'], borde_color=COLORES['danger'])

    # Flecha ciclo superior
    d.crear_flecha(2.8, 8.35, 4.0, 8.35, 'TBA ~ Exp(λ)', 'normal')
    d.crear_flecha(5.8, 8.35, 7.0, 8.35, 'activate()', 'normal')

    # Estados inferiores
    d.crear_caja(7, 6, 1.8, 0.7, 'RECOVERING\nstate=3', COLORES['azul_claro'], borde_color=COLORES['info'])
    d.crear_caja(4, 6, 1.8, 0.7, 'FINALIZED\nstate=4', COLORES['gris_claro'], borde_color=COLORES['borde_claro'])

    # Flecha ciclo inferior
    d.crear_flecha(7.9, 8.0, 7.9, 6.7, 'Duration\n~ LogNormal(μ,σ)', 'normal')
    d.crear_flecha(7.0, 6.35, 5.8, 6.35, 'recover()', 'normal')
    d.crear_flecha(4.0, 6.35, 2.8, 6.35, 'finalize()', 'normal')

    # Cierre del ciclo
    d.crear_flecha(1.9, 8.0, 1.9, 6.7, '', 'normal')
    d.crear_flecha(1.9, 6.35, 1.9, 6.35, '', 'normal', COLORES['success'])

    # Cuadro de decisión
    d.crear_diamante(3.5, 4.5, 3, 1, 'check_conditions()\nPreconditions?', COLORES['amarillo_claro'])

    d.crear_flecha(5, 8.0, 5, 5.5, 'evaluate', 'decision')
    d.crear_flecha(3.5, 5, 2, 6, 'False', 'decision')
    d.crear_flecha(6.5, 5, 7.5, 6, 'True', 'decision')

    # Detalles de acciones por estado
    # RECUPERANDO
    d.crear_caja(0.3, 2.8, 2.5, 1.2,
                'RECOVERING:\n• recovery_process()\n• gradual_restoration()\n• update_metrics()',
                COLORES['azul_claro'], borde_color=COLORES['info'])

    # PREPARANDO
    d.crear_caja(3.5, 2.8, 2.5, 1.2,
                'PREPARING:\n• emit_event()\n• check_preconditions()\n• notify_observers()',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])

    # ACTIVA
    d.crear_caja(6.5, 2.8, 2.5, 1.2,
                'ACTIVE:\n• modify_parameters()\n• block_resources()\n• apply_impact()',
                COLORES['rojo_claro'], borde_color=COLORES['danger'])

    # Flechas explicativas
    d.crear_flecha(4.75, 8.0, 4.75, 4.0, '', 'normal', COLORES['texto_oscuro'])
    d.crear_flecha(7.9, 8.0, 7.75, 4.0, '', 'normal', COLORES['texto_oscuro'])
    d.crear_flecha(1.9, 6.7, 1.55, 4.0, '', 'normal', COLORES['texto_oscuro'])

    # Panel de métricas
    d.crear_caja(0.5, 0.8, 9, 1.3,
                'MÉTRICAS CAPTURADAS (State Variables):\n'
                'activation_count | total_active_time | cumulative_impact | successful_recoveries | failed_recoveries\n'
                'timestamp_start | timestamp_end | current_state | target_entity_id',
                COLORES['amarillo_claro'], borde_color=COLORES['naranja_warning'])

    # Nota sobre tipos
    d.ax.text(5, 0.4, 'Tipos de Disrupción: Climática (15) | Operacional (5) | Social (5) | Técnica (3) | Logística (3) | Regulatoria (2) | Económica (2)',
             fontsize=8, ha='center', style='italic',
             color=COLORES['texto_oscuro'], alpha=0.7)

    d.guardar('diagrama_2_ciclo_disrupcion.png')


def diagrama_3_arquitectura_sistema():
    """Diagrama 3: Arquitectura del sistema completo."""
    d = DiagramadorTesis()
    d.crear_lienzo('Arquitectura del Sistema: Componentes y Capas', figsize=(18, 12))

    # Capa 1: CLI Layer
    d.crear_caja(0.5, 9, 2.5, 0.8, 'CLI Interface\nTyper Framework',
                COLORES['borde_oscuro'])
    d.crear_caja(3.5, 9, 2.5, 0.8, 'Config Builder\nYAML Validator',
                COLORES['borde_oscuro'])
    d.crear_caja(6.5, 9, 3, 0.8, 'Executor\nCommand Pattern',
                COLORES['borde_oscuro'])

    # Capa 2: Core Simulation Layer
    d.crear_caja(1.5, 7.2, 3, 1, 'Simulation Engine\nmodelo.py\nSimPy.Environment',
                COLORES['azul_principal'])
    d.crear_caja(5, 7.2, 4, 1, 'Disruption Manager\neventos.py\n77 Risk Profiles',
                COLORES['rojo_error'])

    # Flechas Capa 1 -> Capa 2
    d.crear_flecha(1.75, 9, 2.5, 8.2, 'execute()', 'normal')
    d.crear_flecha(4.75, 9, 3.5, 8.2, 'load_config()', 'normal')
    d.crear_flecha(8, 9, 7.5, 8.2, 'orchestrate()', 'normal')

    # Capa 3: Entity Layer (Domain Model)
    d.crear_caja(0.2, 5.5, 1.6, 0.7, 'StoragePlant\nResource',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(2, 5.5, 1.6, 0.7, 'Supplier\nProcess',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(3.8, 5.5, 1.6, 0.7, 'Fleet[N]\nVehicle',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(5.6, 5.5, 1.6, 0.7, 'DemandNode\nConsumer',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(7.5, 5.5, 2.3, 0.7, 'EntityBase\nABC + Observable',
                COLORES['azul_claro'], borde_color=COLORES['info'])

    # Flechas herencia/composición
    d.crear_flecha(3, 7.2, 1.0, 6.2, 'instantiate', 'normal')
    d.crear_flecha(3, 7.2, 2.8, 6.2, 'instantiate', 'normal')
    d.crear_flecha(3, 7.2, 4.6, 6.2, 'instantiate', 'normal')
    d.crear_flecha(3, 7.2, 6.4, 6.2, 'instantiate', 'normal')

    # Relación disrupciones-entidades
    d.crear_flecha(7, 7.2, 8.6, 6.2, 'affects', 'doble', COLORES['danger'])
    d.crear_flecha(7, 7.2, 6.4, 6.2, 'subscribe', 'normal', COLORES['danger'])
    d.crear_flecha(7, 7.2, 4.6, 6.2, 'subscribe', 'normal', COLORES['danger'])

    # Capa 4: Observability Layer
    d.crear_caja(1, 3.8, 2.5, 0.8, 'SystemMonitor\nObserver Pattern',
                COLORES['verde_claro'], borde_color=COLORES['success'])
    d.crear_caja(4, 3.8, 2.5, 0.8, 'RealTimeAnalyzer\nStreaming',
                COLORES['verde_claro'], borde_color=COLORES['success'])
    d.crear_caja(7, 3.8, 2.5, 0.8, 'MetricsCollector\nAggregator',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])

    # Flechas eventos -> monitores
    d.crear_flecha(1.0, 5.5, 2.25, 4.6, 'on_event()', 'normal')
    d.crear_flecha(2.8, 5.5, 2.5, 4.6, 'on_event()', 'normal')
    d.crear_flecha(4.6, 5.5, 5.25, 4.6, 'on_event()', 'normal')
    d.crear_flecha(6.4, 5.5, 5.5, 4.6, 'on_event()', 'normal')

    # Flechas entre monitores
    d.crear_flecha(3.5, 3.8, 4.0, 3.8, 'stream', 'doble')
    d.crear_flecha(6.5, 3.8, 7.0, 3.8, 'aggregate', 'normal')

    # Capa 5: Data Persistence Layer
    d.crear_cilindro(0.5, 1.8, 2, 1, 'Events Store\nevents.parquet\npd.DataFrame',
                    COLORES['azul_claro'])
    d.crear_cilindro(3, 1.8, 2, 1, 'Metadata Store\nmetadata.json\nDict',
                    COLORES['azul_claro'])
    d.crear_cilindro(5.5, 1.8, 2, 1, 'Metrics Store\nsummary.csv\npd.Series',
                    COLORES['azul_claro'])
    d.crear_cilindro(8, 1.8, 1.5, 1, 'Logs\napp.log\nstr',
                    COLORES['amarillo_claro'])

    # Flechas persistencia
    d.crear_flecha(2.25, 3.8, 1.5, 2.8, 'to_parquet()', 'normal')
    d.crear_flecha(5.25, 3.8, 4, 2.8, 'to_json()', 'normal')
    d.crear_flecha(8.25, 3.8, 6.5, 2.8, 'to_csv()', 'normal')

    # Capa 6: Analytics Layer (Post-Processing)
    d.crear_caja(0.5, 0.3, 2.8, 0.9, 'ML Pipeline\nscikit-learn\nClustering',
                COLORES['verde_claro'], borde_color=COLORES['success'])
    d.crear_caja(3.8, 0.3, 2.8, 0.9, 'Graph Analysis\nNetworkX\nTopology',
                COLORES['verde_claro'], borde_color=COLORES['success'])
    d.crear_caja(7, 0.3, 2.5, 0.9, 'HPC Module\nC Extension\nNumPy',
                COLORES['verde_claro'], borde_color=COLORES['success'])

    # Flechas análisis
    d.crear_flecha(1.5, 1.8, 1.9, 1.2, 'read', 'normal')
    d.crear_flecha(4, 1.8, 5.2, 1.2, 'read', 'normal')
    d.crear_flecha(6.5, 1.8, 8.25, 1.2, 'process', 'normal')

    # Leyenda de patrones
    d.crear_caja(0.2, 10.2, 9.6, 0.5,
                'Design Patterns: Observer | Factory | Strategy | State | Command | Builder | Singleton | Template Method',
                COLORES['naranja_claro'], borde_color=COLORES['warning'])

    d.guardar('diagrama_3_arquitectura_sistema.png')


def diagrama_4_flujo_yaml_riesgos():
    """Diagrama 4: Procesamiento de riesgos desde YAML."""
    d = DiagramadorTesis()
    d.crear_lienzo('Risk Configuration Pipeline: YAML to Stochastic Disruption Objects', figsize=(17, 10))

    # Inicio
    d.crear_caja(3, 8.5, 4, 0.7, 'YAML Config\nriesgos: Dict[str, RiskDef]',
                COLORES['borde_oscuro'])

    # Extracción parámetros
    d.crear_caja(0.5, 7, 2.2, 1,
                'Extract Parameters:\n• annual_probability: float\n• duration_hours: float\n• targets: List[str]\n• description: str',
                COLORES['azul_claro'], borde_color=COLORES['info'])

    d.crear_flecha(4.5, 8.5, 1.6, 8.0, 'yaml.safe_load()', 'normal')

    # Decisión de mapeo
    d.crear_diamante(3.5, 6.5, 3, 1.2, 'risk_id in\nCATALOG_77\n?',
                    COLORES['amarillo_claro'])

    d.crear_flecha(1.6, 7.0, 3.8, 7.7, 'validate', 'normal')

    # Rama SÍ - Mapeo exitoso
    d.crear_caja(7.2, 6.8, 2.5, 1.2,
                'HYBRID Mode:\nCatalogProfile\n.override(yaml_params)',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])

    d.crear_flecha(6.5, 7.1, 7.2, 7.4, 'True', 'normal', COLORES['success'])

    # Rama NO - Perfil nuevo
    d.crear_caja(7.2, 4.8, 2.5, 1.2,
                'CUSTOM Mode:\ninfer_category()\ncreate_profile()',
                COLORES['rojo_claro'], borde_color=COLORES['danger'])

    d.crear_flecha(6.5, 6.5, 7.2, 5.4, 'False', 'decision')

    # Conversión a distribuciones
    d.crear_caja(2, 4.5, 3.5, 1.5,
                'Stochastic Conversion:\n'
                'TBA ~ Exponential(λ=8760/p_annual)\n'
                'Duration ~ LogNormal(μ, σ)\n'
                'CV(type): adaptive variance',
                COLORES['verde_claro'], borde_color=COLORES['success'])

    d.crear_flecha(7.2, 6.8, 5.5, 5.25, '', 'normal')
    d.crear_flecha(7.2, 4.8, 5.5, 5.25, '', 'normal')

    # Factory de disrupciones
    d.crear_caja(2.5, 2.5, 5, 1,
                'DisruptionFactory.create()\nInstantiate by inferred category',
                COLORES['azul_principal'])

    d.crear_flecha(3.75, 4.5, 5, 3.5, 'build', 'normal')

    # Tipos de disrupciones
    d.crear_caja(0.2, 0.8, 1.8, 0.9,
                'ClimateDisruption\nclass instance',
                COLORES['azul_claro'], borde_color=COLORES['info'])
    d.crear_caja(2.3, 0.8, 1.8, 0.9,
                'OperationalDisruption\nclass instance',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])
    d.crear_caja(4.4, 0.8, 1.8, 0.9,
                'SocialDisruption\nclass instance',
                COLORES['rojo_claro'], borde_color=COLORES['danger'])
    d.crear_caja(6.5, 0.8, 1.8, 0.9,
                'LogisticDisruption\nclass instance',
                COLORES['amarillo_claro'], borde_color=COLORES['warning'])

    # Flechas a tipos
    d.crear_flecha(3.5, 2.5, 1.1, 1.7, 'new', 'normal')
    d.crear_flecha(4.5, 2.5, 3.2, 1.7, 'new', 'normal')
    d.crear_flecha(5.5, 2.5, 5.3, 1.7, 'new', 'normal')
    d.crear_flecha(6.5, 2.5, 7.4, 1.7, 'new', 'normal')

    # Panel de ejemplo
    d.crear_caja(0.3, 9.5, 2.2, 0.8,
                'Example Input:\n57-ST-CU:\n  prob: 4.0\n  dur: 12.0',
                COLORES['gris_claro'], borde_color=COLORES['borde_claro'])

    d.crear_flecha(1.4, 9.5, 3.0, 9.2, 'input', 'normal', COLORES['texto_gris'])

    # Resultado final
    d.crear_caja(8.6, 0.8, 1.2, 0.9,
                'Output:\nDisruption\nobject\nready',
                COLORES['verde_claro'], borde_color=COLORES['success'])

    d.guardar('diagrama_4_flujo_yaml_riesgos.png')


def diagrama_5_flujo_entidades():
    """Diagrama 5: Flujo de procesos y entidades - Estilo Wes Anderson."""
    d = DiagramadorTesis()
    d.crear_lienzo('Flujo de Simulación: Procesos y Entidades', figsize=(12, 10))

    # INICIO
    d.crear_caja(4.5, 9, 1.5, 0.5, 'INICIO',
                COLORES['bordo'])

    d.crear_flecha(5.25, 9, 5.25, 8.5, '', 'normal')

    # Inicialización
    d.crear_caja(3.75, 8, 2.5, 0.6, 'Inicializar\nSimPy.Environment',
                COLORES['azul_pastel'], borde_color=COLORES['azul_oscuro'])

    d.crear_flecha(5, 8, 5, 7.3, '', 'normal')

    # Crear entidades (4 en línea)
    d.crear_caja(0.5, 6.5, 1.8, 0.7, 'Crear\nPlanta',
                COLORES['lavanda'], borde_color=COLORES['azul_oscuro'])
    d.crear_caja(2.8, 6.5, 1.8, 0.7, 'Crear\nProveedor',
                COLORES['verde_menta'], borde_color=COLORES['verde_bosque'])
    d.crear_caja(5.1, 6.5, 1.8, 0.7, 'Crear\nCamiones',
                COLORES['amarillo_mostaza'], borde_color=COLORES['terracota'])
    d.crear_caja(7.4, 6.5, 1.8, 0.7, 'Crear\nDemanda',
                COLORES['coral'], borde_color=COLORES['bordo'])

    # Flechas a entidades
    d.crear_flecha(4.5, 8, 1.4, 7.2, '', 'normal')
    d.crear_flecha(5, 8, 3.7, 7.2, '', 'normal')
    d.crear_flecha(5.5, 8, 6, 7.2, '', 'normal')
    d.crear_flecha(6, 8, 8.3, 7.2, '', 'normal')

    # Procesos (4 en línea, más compactos)
    d.crear_caja(0.5, 5, 1.8, 1,
                'while True:\nmonitorear()\nif crítico:\n  emit()',
                COLORES['lavanda'], borde_color=COLORES['azul_oscuro'])

    d.crear_caja(2.8, 5, 1.8, 1,
                'while True:\ntimeout(10d)\nput(vol)',
                COLORES['verde_menta'], borde_color=COLORES['verde_bosque'])

    d.crear_caja(5.1, 5, 1.8, 1,
                'while True:\ncarga()\nviaje()\ndescarga()',
                COLORES['amarillo_mostaza'], borde_color=COLORES['terracota'])

    d.crear_caja(7.4, 5, 1.8, 1,
                'while True:\ntimeout(24h)\nget(dem)',
                COLORES['coral'], borde_color=COLORES['bordo'])

    # Flechas a procesos
    d.crear_flecha(1.4, 6.5, 1.4, 6.0, '', 'normal')
    d.crear_flecha(3.7, 6.5, 3.7, 6.0, '', 'normal')
    d.crear_flecha(6, 6.5, 6, 6.0, '', 'normal')
    d.crear_flecha(8.3, 6.5, 8.3, 6.0, '', 'normal')

    # Ejecución central
    d.crear_caja(3.75, 3.5, 2.5, 0.6, 'env.run(until=T)',
                COLORES['azul_oscuro'])

    # Flechas convergentes
    d.crear_flecha(1.4, 5, 4.5, 4.1, '', 'normal', COLORES['texto_gris'])
    d.crear_flecha(3.7, 5, 4.8, 4.1, '', 'normal', COLORES['texto_gris'])
    d.crear_flecha(6, 5, 5.2, 4.1, '', 'normal', COLORES['texto_gris'])
    d.crear_flecha(8.3, 5, 5.5, 4.1, '', 'normal', COLORES['texto_gris'])

    d.crear_flecha(5, 3.5, 5, 2.8, '', 'normal')

    # Métricas
    d.crear_caja(3.75, 2.2, 2.5, 0.6, 'Recolectar Métricas',
                COLORES['beige'], borde_color=COLORES['terracota'])

    d.crear_flecha(5, 2.2, 5, 1.6, '', 'normal')

    # Outputs (3 cilindros)
    d.crear_cilindro(1.2, 0.5, 1.8, 0.7, 'events\n.parquet',
                    COLORES['rosa_pastel'])
    d.crear_cilindro(3.6, 0.5, 1.8, 0.7, 'metadata\n.json',
                    COLORES['rosa_pastel'])
    d.crear_cilindro(6, 0.5, 1.8, 0.7, 'summary\n.csv',
                    COLORES['rosa_pastel'])

    # Flechas a outputs
    d.crear_flecha(4.5, 2.2, 2.1, 1.2, '', 'normal')
    d.crear_flecha(5, 2.2, 4.5, 1.2, '', 'normal')
    d.crear_flecha(5.5, 2.2, 6.9, 1.2, '', 'normal')

    d.guardar('diagrama_5_flujo_entidades.png')


# === EJECUTAR GENERACIÓN ===
if __name__ == '__main__':
    import sys
    import io

    # Fix encoding for Windows console
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Generando diagramas de flujo profesionales...")
    print("=" * 60)

    diagrama_1_flujo_principal()
    diagrama_2_ciclo_disrupcion()
    diagrama_3_arquitectura_sistema()
    diagrama_4_flujo_yaml_riesgos()
    diagrama_5_flujo_entidades()

    print("=" * 60)
    print("Todos los diagramas generados exitosamente!")
    print("\nArchivos creados:")
    print("  1. diagrama_1_flujo_principal.png")
    print("  2. diagrama_2_ciclo_disrupcion.png")
    print("  3. diagrama_3_arquitectura_sistema.png")
    print("  4. diagrama_4_flujo_yaml_riesgos.png")
    print("  5. diagrama_5_flujo_entidades.png")
    print("\nListos para tu presentacion de tesis!")
