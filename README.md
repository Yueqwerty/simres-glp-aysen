# simres-glp-aysen

Simulacion de Resiliencia del Sistema de Suministro de GLP en la Region de Aysen, Chile.

Modelo de simulacion de eventos discretos (DES) para evaluar el impacto de la capacidad de almacenamiento y disrupciones de ruta sobre el nivel de servicio del sistema energetico regional.

## Requisitos

- Python 3.11+
- Poetry (gestor de dependencias)

## Instalacion

```bash
# Clonar repositorio
git clone https://github.com/tu-usuario/simres-glp-aysen.git
cd simres-glp-aysen

# Instalar dependencias con Poetry
poetry install
```

## Uso Rapido

### Ejecutar una simulacion

```python
from bll import SimulationConfig, run_simulation

config = SimulationConfig(
    capacity_tm=431.0,          # Capacidad en toneladas metricas
    simulation_days=365,        # Dias a simular
    seed=42                     # Semilla para reproducibilidad
)

result = run_simulation(config)
print(f"Nivel de servicio: {result['service_level_pct']}%")
print(f"Dias de stockout: {result['stockout_days']}")
```

### Ejecutar experimento Monte Carlo

```python
from bll.experiment import run_experiment_sequential

# Ejecuta diseno factorial 2x3 con N replicas
df = run_experiment_sequential(num_replicas=100)
print(df.groupby('config_name')['service_level_pct'].mean())
```

### Iniciar API (backend)

```bash
cd backend
poetry run python start_server.py
```

La API estara disponible en `http://localhost:8000/api/docs`

## Configuraciones del Diseno Experimental

| Configuracion | Capacidad | Duracion Max. Disrupcion |
|---------------|-----------|--------------------------|
| SQ_Short      | 431 TM    | 7 dias                   |
| SQ_Medium     | 431 TM    | 14 dias                  |
| SQ_Long       | 431 TM    | 21 dias                  |
| P_Short       | 681 TM    | 7 dias                   |
| P_Medium      | 681 TM    | 14 dias                  |
| P_Long        | 681 TM    | 21 dias                  |

SQ = Status Quo, P = Propuesta

## KPIs Principales

- **service_level_pct**: Porcentaje de demanda satisfecha
- **stockout_probability_pct**: Porcentaje de dias con quiebre de stock
- **avg_autonomy_days**: Dias promedio de autonomia del inventario
- **blocked_time_pct**: Porcentaje de tiempo con ruta bloqueada

## Comandos Utiles

```bash
# Ejecutar tests
poetry run pytest

# Formatear codigo
poetry run ruff format .

# Verificar linting
poetry run ruff check .
```

## Estructura Principal

- `bll/` - Logica de negocio (simulacion, estadisticas)
- `dal/` - Acceso a datos (checkpoints, exportacion)
- `backend/` - API FastAPI

## Licencia

MIT
