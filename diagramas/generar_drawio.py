"""
Generador de diagramas de flujo para Draw.io (.drawio format)
Genera XML compatible con diagrams.net/draw.io
"""
import xml.etree.ElementTree as ET
from xml.dom import minidom


class DrawIOFlowchart:
    """Generador de diagramas de flujo en formato Draw.io XML."""

    def __init__(self, nombre="Diagrama"):
        self.nombre = nombre
        self.shapes = []
        self.connections = []
        self.shape_id = 0

        # Estilos Draw.io
        self.estilos = {
            'inicio_fin': 'rounded=1;whiteSpace=wrap;html=1;fillColor=#8B4049;strokeColor=#8B4049;fontColor=#ffffff;fontSize=14;fontStyle=1',
            'proceso': 'whiteSpace=wrap;html=1;fillColor=#81B29A;strokeColor=#6B8E23;fontSize=12',
            'decision': 'rhombus;whiteSpace=wrap;html=1;fillColor=#F2CC8F;strokeColor=#C17767;fontSize=11',
            'datos': 'shape=parallelogram;whiteSpace=wrap;html=1;fillColor=#A8DADC;strokeColor=#3D5A80;fontSize=11',
            'base_datos': 'shape=cylinder3;whiteSpace=wrap;html=1;fillColor=#F4C2C2;strokeColor=#8B4049;fontSize=11',
            'conector': 'ellipse;whiteSpace=wrap;html=1;aspect=fixed;fillColor=#F4E8C1;strokeColor=#C17767;fontSize=10',
        }

    def agregar_inicio_fin(self, x, y, width, height, texto):
        """Agrega forma de inicio/fin (rectángulo redondeado)."""
        shape_id = f"shape_{self.shape_id}"
        self.shape_id += 1

        self.shapes.append({
            'id': shape_id,
            'value': texto,
            'style': self.estilos['inicio_fin'],
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'vertex': '1'
        })
        return shape_id

    def agregar_proceso(self, x, y, width, height, texto):
        """Agrega forma de proceso (rectángulo)."""
        shape_id = f"shape_{self.shape_id}"
        self.shape_id += 1

        self.shapes.append({
            'id': shape_id,
            'value': texto,
            'style': self.estilos['proceso'],
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'vertex': '1'
        })
        return shape_id

    def agregar_decision(self, x, y, width, height, texto):
        """Agrega forma de decisión (rombo)."""
        shape_id = f"shape_{self.shape_id}"
        self.shape_id += 1

        self.shapes.append({
            'id': shape_id,
            'value': texto,
            'style': self.estilos['decision'],
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'vertex': '1'
        })
        return shape_id

    def agregar_datos(self, x, y, width, height, texto):
        """Agrega forma de datos (paralelogramo)."""
        shape_id = f"shape_{self.shape_id}"
        self.shape_id += 1

        self.shapes.append({
            'id': shape_id,
            'value': texto,
            'style': self.estilos['datos'],
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'vertex': '1'
        })
        return shape_id

    def agregar_base_datos(self, x, y, width, height, texto):
        """Agrega forma de base de datos (cilindro)."""
        shape_id = f"shape_{self.shape_id}"
        self.shape_id += 1

        self.shapes.append({
            'id': shape_id,
            'value': texto,
            'style': self.estilos['base_datos'],
            'x': x,
            'y': y,
            'width': width,
            'height': height,
            'vertex': '1'
        })
        return shape_id

    def conectar(self, source_id, target_id, etiqueta=""):
        """Conecta dos formas con una flecha."""
        conn_id = f"conn_{len(self.connections)}"

        self.connections.append({
            'id': conn_id,
            'source': source_id,
            'target': target_id,
            'label': etiqueta,
            'style': 'edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;strokeColor=#8B4049;strokeWidth=2;'
        })

    def generar_xml(self):
        """Genera el XML compatible con Draw.io."""
        # Estructura básica
        mxfile = ET.Element('mxfile', {
            'host': 'app.diagrams.net',
            'modified': '2024-01-01T00:00:00.000Z',
            'agent': 'Python Script',
            'version': '21.1.0',
            'type': 'device'
        })

        diagram = ET.SubElement(mxfile, 'diagram', {
            'id': 'diagram_1',
            'name': self.nombre
        })

        mxGraphModel = ET.SubElement(diagram, 'mxGraphModel', {
            'dx': '1422',
            'dy': '794',
            'grid': '1',
            'gridSize': '10',
            'guides': '1',
            'tooltips': '1',
            'connect': '1',
            'arrows': '1',
            'fold': '1',
            'page': '1',
            'pageScale': '1',
            'pageWidth': '1169',
            'pageHeight': '1654',
            'math': '0',
            'shadow': '0'
        })

        root = ET.SubElement(mxGraphModel, 'root')

        # Células raíz requeridas por Draw.io
        ET.SubElement(root, 'mxCell', {'id': '0'})
        ET.SubElement(root, 'mxCell', {'id': '1', 'parent': '0'})

        # Agregar todas las formas
        for shape in self.shapes:
            cell = ET.SubElement(root, 'mxCell', {
                'id': shape['id'],
                'value': shape['value'],
                'style': shape['style'],
                'vertex': shape['vertex'],
                'parent': '1'
            })

            ET.SubElement(cell, 'mxGeometry', {
                'x': str(shape['x']),
                'y': str(shape['y']),
                'width': str(shape['width']),
                'height': str(shape['height']),
                'as': 'geometry'
            })

        # Agregar todas las conexiones
        for conn in self.connections:
            cell = ET.SubElement(root, 'mxCell', {
                'id': conn['id'],
                'value': conn['label'],
                'style': conn['style'],
                'edge': '1',
                'parent': '1',
                'source': conn['source'],
                'target': conn['target']
            })

            ET.SubElement(cell, 'mxGeometry', {
                'relative': '1',
                'as': 'geometry'
            })

        # Convertir a string con formato
        xml_str = ET.tostring(mxfile, encoding='unicode')
        dom = minidom.parseString(xml_str)
        return dom.toprettyxml(indent="  ")

    def guardar(self, filename):
        """Guarda el diagrama en formato .drawio."""
        xml_content = self.generar_xml()

        with open(filename, 'w', encoding='utf-8') as f:
            f.write(xml_content)

        print(f"[OK] Diagrama guardado: {filename}")
        print(f"     Abre este archivo en https://app.diagrams.net o Draw.io Desktop")


def crear_diagrama_simulacion():
    """Crea el diagrama de flujo de la simulación."""
    d = DrawIOFlowchart("Flujo de Simulación - Sistema GLP")

    # INICIO
    inicio = d.agregar_inicio_fin(500, 50, 120, 60, "INICIO")

    # Inicialización
    init_env = d.agregar_proceso(450, 150, 220, 60, "Inicializar\nSimPy.Environment")
    d.conectar(inicio, init_env)

    # Crear entidades (4 paralelas)
    crear_planta = d.agregar_proceso(100, 260, 180, 60, "Crear\nPlantaAlmacenamiento")
    crear_proveedor = d.agregar_proceso(320, 260, 180, 60, "Crear\nProveedorExterno")
    crear_camiones = d.agregar_proceso(540, 260, 180, 60, "Crear\nCamiones[N]")
    crear_demanda = d.agregar_proceso(760, 260, 180, 60, "Crear\nNodoDemanda")

    d.conectar(init_env, crear_planta)
    d.conectar(init_env, crear_proveedor)
    d.conectar(init_env, crear_camiones)
    d.conectar(init_env, crear_demanda)

    # Procesos paralelos
    proc_planta = d.agregar_proceso(100, 370, 180, 80, "while True:\n  monitorear()\n  if crítico:\n    emit()")
    proc_proveedor = d.agregar_proceso(320, 370, 180, 80, "while True:\n  timeout(10d)\n  put(volumen)")
    proc_camion = d.agregar_proceso(540, 370, 180, 80, "while True:\n  carga()\n  viaje()\n  descarga()")
    proc_demanda = d.agregar_proceso(760, 370, 180, 80, "while True:\n  timeout(24h)\n  get(demanda)")

    d.conectar(crear_planta, proc_planta, "env.process()")
    d.conectar(crear_proveedor, proc_proveedor, "env.process()")
    d.conectar(crear_camiones, proc_camion, "env.process()")
    d.conectar(crear_demanda, proc_demanda, "env.process()")

    # Motor de simulación
    run_sim = d.agregar_proceso(450, 510, 220, 60, "env.run(until=T)")

    d.conectar(proc_planta, run_sim)
    d.conectar(proc_proveedor, run_sim)
    d.conectar(proc_camion, run_sim)
    d.conectar(proc_demanda, run_sim)

    # Recolectar métricas
    metricas = d.agregar_proceso(450, 620, 220, 60, "Recolectar Métricas")
    d.conectar(run_sim, metricas)

    # Outputs (bases de datos)
    db1 = d.agregar_base_datos(200, 730, 150, 80, "events\n.parquet")
    db2 = d.agregar_base_datos(475, 730, 150, 80, "metadata\n.json")
    db3 = d.agregar_base_datos(750, 730, 150, 80, "summary\n.csv")

    d.conectar(metricas, db1)
    d.conectar(metricas, db2)
    d.conectar(metricas, db3)

    # FIN
    fin = d.agregar_inicio_fin(500, 860, 120, 60, "FIN")
    d.conectar(db2, fin)

    d.guardar('diagrama_simulacion.drawio')


if __name__ == '__main__':
    print("Generando diagrama de flujo para Draw.io...")
    print("=" * 60)
    crear_diagrama_simulacion()
    print("=" * 60)
    print("\nPasos para abrir:")
    print("1. Ve a https://app.diagrams.net")
    print("2. File > Open From > Device")
    print("3. Selecciona 'diagrama_simulacion.drawio'")
    print("4. Edita y exporta como quieras (PNG, PDF, SVG, etc.)")
