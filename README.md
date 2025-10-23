# SimRes GLP Aysén

Simulación de Resiliencia del Sistema de Suministro de GLP en la Región de Aysén, Chile.

## 📋 Descripción

Modelo de simulación de eventos discretos (DES) para evaluar la resiliencia de la cadena de suministro de Gas Licuado de Petróleo (GLP) en la Región de Aysén, con énfasis en la sensibilidad del sistema a factores endógenos (capacidad de almacenamiento) versus factores exógenos (disrupciones en la ruta de suministro).

## 🎯 Objetivo de la Investigación

Evaluar cuantitativamente si el sistema es más sensible a:
- **Factores ENDÓGENOS:** Capacidad de almacenamiento (controlable por inversión)
- **Factores EXÓGENOS:** Duración de disrupciones (NO controlable directamente)

## 🏗️ Estructura del Proyecto

```
simres-glp-aysen/
├── src/                          # Código fuente principal
│   ├── modelo_simple.py          # Motor de simulación (SimPy)
│   └── monitores.py              # Sistema de métricas
├── scripts/                      # Scripts de ejecución
│   ├── experimento_tesis.py      # Diseño factorial 2×3 (180 sims)
│   └── visualizar_resultados_tesis.py  # Generación de figuras
├── results/                      # Resultados experimentales
│   ├── experimento_tesis/        # CSVs y JSONs con KPIs
│   └── figuras_tesis/            # Figuras para la tesis (PDF)
├── _legacy/                      # Código obsoleto (no usar)
└── informe.pdf                   # Informe CNE 2024 (fuente de datos)
```

## 🚀 Instalación

### Requisitos

- Python 3.10+
- SimPy 4.0+
- NumPy, Pandas, Matplotlib, Seaborn

### Instalación con pip

```bash
pip install simpy numpy pandas matplotlib seaborn
```

## 📊 Uso

### 1. Ejecutar simulación simple

```bash
cd simres-glp-aysen
python src/modelo_simple.py
```

### 2. Ejecutar experimento completo (180 simulaciones)

```bash
python scripts/experimento_tesis.py
```

**Salida:**
- `results/experimento_tesis/resultados_experimento.csv` (180 filas, 1 por réplica)
- `results/experimento_tesis/resumen_experimento.json` (métricas agregadas)

### 3. Generar figuras

```bash
python scripts/visualizar_resultados_tesis.py
```

**Salida:** 5 figuras PDF en `results/figuras_tesis/`

## 📈 Diseño Experimental

**Factorial 2 × 3:**

| Factor | Niveles |
|--------|---------|
| **Capacidad** (Endógeno) | Status Quo (431 TM), Propuesta (681 TM) |
| **Duración Máx Disrupciones** (Exógeno) | Corta (7d), Media (14d), Larga (21d) |

**Total:** 6 configuraciones × 30 réplicas = **180 simulaciones**

## 🔑 Parámetros Clave

### Del Informe CNE 2024

- **Demanda GLP 2023:** 15,061 TM/año → **41.3 TM/día**
- **Capacidad Status Quo:** 431 TM (Abastible 150 + Lipigas 240 + Gasco 41)
- **Autonomía teórica:** ~10.4 días (431 / 41.3)
- **Frecuencia disrupciones:** λ = 4 eventos/año (Nivel 4, matriz de riesgos)
- **Lead time nominal:** 6 días (Neuquén/Cabo Negro → Coyhaique)

### Política de Inventario (Q,R)

- **Punto de reorden (R):** 70% de capacidad
- **Cantidad de pedido (Q):** 65% de capacidad
- **Máximo pedidos simultáneos:** 2

## 📊 Resultados Principales

```
Sensibilidad ENDÓGENA (capacidad):  +0.58%
Sensibilidad EXÓGENA (duración):    -1.23%

Ratio: 2.12×

✅ HIPÓTESIS CONFIRMADA: El sistema es 2.12× más sensible a
factores exógenos (disrupciones) que a factores endógenos (capacidad).
```

### Implicación Práctica

Las inversiones en **mitigación de disrupciones** (barcazas de emergencia, rutas alternativas, protocolos de coordinación) ofrecen un **retorno 2× mayor** en resiliencia que las inversiones en expansión de capacidad de almacenamiento.

## 📚 Referencias

- Informe CNE 2024: *"Vulnerabilidad de Suministro Energético en Aysén"*
- SimPy Documentation: https://simpy.readthedocs.io/

## 👨‍💻 Autor

**Carlos Subiabre Saldivia**
Ingeniería Civil Informática
Universidad de Aysén
2024-2025

## 📄 Licencia

Ver archivo `LICENSE`
