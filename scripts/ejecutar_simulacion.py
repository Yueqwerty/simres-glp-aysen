# scripts/ejecutar_simulacion.py
import typer
import simpy
import yaml
from pathlib import Path
from src.modelo import PlantaAlmacenamiento, Camion

# Creamos una aplicación de línea de comandos con Typer
app = typer.Typer()

@app.command()
def ejecutar(
    config_path: Path = typer.Option(
        "configs/escenario_base.yaml",
        exists=True,
        readable=True,
        resolve_path=True,
    )
):
    """
    Ejecuta el modelo de simulación leyendo una configuración.
    """
    print(f"Iniciando simulación con configuración desde: {config_path}")
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # Extraemos la configuración para mayor legibilidad
    cfg_sim = config['simulacion']
    cfg_planta = config['planta_coyhaique']
    cfg_flota = config['flota']

    # 1. Crear el entorno de SimPy
    env = simpy.Environment()

    # 2. Crear las entidades del modelo
    planta_coyhaique = PlantaAlmacenamiento(
        env,
        id_planta="Coyhaique",
        capacidad_tons=cfg_planta['capacidad_tons'],
        nivel_inicial_tons=cfg_planta['nivel_inicial_tons']
    )

    for i in range(cfg_flota['num_camiones']):
        Camion(
            env,
            id_camion=f"C-{i+1}",
            capacidad_tons=cfg_flota['capacidad_camion_tons'],
            planta_origen=planta_coyhaique
        )

    # 3. Ejecutar la simulación
    print("\n--- Inicio de la Simulación ---")
    env.run(until=cfg_sim['duracion_horas'])
    print("\n--- Fin de la Simulación ---")

if __name__ == "__main__":
    app()