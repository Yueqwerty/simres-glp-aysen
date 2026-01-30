# simres-glp-aysen

Modelo de simulacion de eventos discretos para evaluar la resiliencia del sistema de suministro de GLP en la Region de Aysen, Chile.

## Requisitos

- Python 3.11+
- Node.js 18+
- Poetry

## Instalacion

```bash
git clone https://github.com/tu-usuario/simres-glp-aysen.git
cd simres-glp-aysen

# Backend
poetry install

# Frontend
cd frontend
npm install
```

## Uso

### Backend

```bash
cd backend
poetry run python start_server.py
```

API disponible en `http://localhost:8000/api/docs`

### Frontend

```bash
cd frontend
npm run dev
```

Interfaz disponible en `http://localhost:5173`

### Simulacion directa

```python
from bll import SimulationConfig, run_simulation

config = SimulationConfig(
    capacity_tm=431.0,
    simulation_days=365,
    seed=42
)

result = run_simulation(config)
print(f"Nivel de servicio: {result['service_level_pct']}%")
```

## Estructura

```
bll/       Logica de negocio (simulacion, estadisticas)
dal/       Acceso a datos
backend/   API FastAPI
frontend/  Interfaz React
```

## Licencia

MIT
