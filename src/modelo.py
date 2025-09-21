# src/modelo.py
import simpy
from dataclasses import dataclass

# Usamos dataclasses para estructurar los datos que registraremos.
# Es una forma moderna y limpia de crear clases que solo contienen datos.
@dataclass
class LogInventario:
    tiempo: float
    nivel: float
    planta_id: str

class PlantaAlmacenamiento:
    """Representa una planta de almacenamiento con una capacidad y nivel de inventario."""
    def __init__(self, env: simpy.Environment, id_planta: str, capacidad_tons: float, nivel_inicial_tons: float):
        self.env = env
        self.id_planta = id_planta
        self.capacidad = capacidad_tons
        # El Container de SimPy es perfecto para modelar inventarios o recursos limitados.
        self.inventario = simpy.Container(env, capacity=capacidad_tons, init=nivel_inicial_tons)

class Camion:
    """Representa un camión que realiza ciclos de carga, viaje y descarga."""
    def __init__(self, env: simpy.Environment, id_camion: str, capacidad_tons: float, planta_origen: PlantaAlmacenamiento):
        self.env = env
        self.id_camion = id_camion
        self.capacidad = capacidad_tons
        self.planta_origen = planta_origen
        # Iniciamos el proceso del camión tan pronto como se crea.
        self.proceso = env.process(self.run())

    def run(self):
        """El ciclo de vida y comportamiento del camión."""
        print(f"[{self.env.now:7.2f}] Camión {self.id_camion} listo para operar.")
        while True:
            # 1. Cargar en la planta de origen
            print(f"[{self.env.now:7.2f}] Camión {self.id_camion} esperando para cargar en {self.planta_origen.id_planta}.")
            # 'yield' le cede el control a SimPy. El proceso se reanudará cuando se cumpla la condición.
            yield self.planta_origen.inventario.get(self.capacidad)
            print(f"[{self.env.now:7.2f}] Camión {self.id_camion} cargado. Nivel planta: {self.planta_origen.inventario.level:.2f} tons.")
            yield self.env.timeout(1) # Simula 1 hora para la operación de carga

            # 2. Viajar (tiempo fijo por ahora)
            print(f"[{self.env.now:7.2f}] Camión {self.id_camion} en ruta a destino.")
            yield self.env.timeout(10) # Simula 10 horas de viaje

            # 3. Descargar (el GLP simplemente "desaparece" por ahora)
            print(f"[{self.env.now:7.2f}] Camión {self.id_camion} ha llegado y descargado.")
            yield self.env.timeout(2) # Simula 2 horas para la descarga