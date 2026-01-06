## Simulacion de Resiliencia del Sistema de Suministro de GLP en Aysen

**Tesis de Ingenieria Civil Industrial**

**Autor:** Carlos Subiabre
**Instituciones:** Universidad de Chile
**Fecha:** Octubre 2024

---

## Descripcion del Proyecto

Este proyecto implementa un modelo de simulacion de eventos discretos para cuantificar el impacto de parametros logisticos criticos sobre la resiliencia del sistema de suministro de Gas Licuado de Petroleo en la Region de Aysen, Chile.

### Objetivo General

Diseñar y validar un modelo de simulacion para evaluar como factores endogenos (capacidad de almacenamiento) y exogenos (disrupciones de ruta) afectan la seguridad energetica regional.

### Hipotesis Central

La resiliencia del sistema exhibe sensibilidad significativamente mayor a parametros exogenos (duracion de disrupciones) que a parametros endogenos (capacidad de almacenamiento).

---

## Arquitectura del Proyecto

```
simres-glp-aysen/
├── src/
│   ├── modelo.py                  # Modelo DES principal
│   └── monitores.py               # Herramientas de monitoreo
├── scripts/
│   ├── experimento_montecarlo.py  # Diseno factorial 2x3 con 10,000 replicas
│   ├── generar_figuras_tesis.py   # Generacion de figuras profesionales
│   └── test_modelo.py             # Pruebas del modelo
├── results/
│   ├── montecarlo/                # Resultados del experimento
│   └── figuras/                   # Figuras para la tesis
├── mitesis/
│   └── figuras/                   # Figuras exportadas para documento
└── README.md
```

---

## Diseno Experimental

### Diseno Factorial 2x3

| Factor | Tipo | Niveles |
|--------|------|---------|
| **Capacidad de Almacenamiento** | Endogeno | Status Quo: 431 TM<br>Propuesta: 681 TM (+58%) |
| **Duracion Maxima de Disrupciones** | Exogeno | Corta: 7 dias<br>Media: 14 dias<br>Larga: 21 dias |

**Total:** 6 configuraciones x 10,000 replicas = 60,000 simulaciones Monte Carlo

### Parametros del Sistema

#### Calibracion con Datos Reales (Informe CNE 2024)

| Parametro | Valor | Fuente |
|-----------|-------|--------|
| Demanda base diaria | 52.5 TM/dia | Mes de mayor consumo (8.2 dias autonomia) |
| Capacidad Status Quo | 431 TM | Abastible (150) + Lipigas (240) + Gasco (41) |
| Capacidad Propuesta | 681 TM | Propuesta 10.4 del informe (+250 TM) |
| Lead time nominal | 6 dias | Datos operativos distribuidores |
| Frecuencia disrupciones | lambda = 4/ano | Matriz de Riesgos (Nivel 4: "Casi Seguro") |
| Duracion disrupciones | Tri(3, mode, max) | Historico nevadas/conflictos Argentina |

#### Caracteristicas del Modelo

- Demanda del mes pico (52.5 TM/dia) para analisis conservador
- Estacionalidad invernal implementada (±30% variacion)
- Politica (Q,R) ajustada a valores realistas (ROP=50%, Q=50%, Inv.Inicial=60%)
- Variabilidad estocastica (±15%)

---

## Instalacion y Uso

### Requisitos

```bash
Python 3.8+
numpy
pandas
simpy
matplotlib
seaborn
scipy
statsmodels
tqdm
```

### Instalacion

```bash
cd simres-glp-aysen

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instalar dependencias
pip install numpy pandas simpy matplotlib seaborn scipy statsmodels tqdm
```

### Ejecutar Experimento

```bash
# Ejecutar experimento Monte Carlo (60,000 simulaciones)
# Puede tomar 5-8 horas segun hardware
python scripts/experimento_montecarlo.py

# Generar figuras para la tesis
python scripts/generar_figuras_tesis.py
```

### Resultados

Los resultados se guardan en:

- `results/montecarlo/resultados_montecarlo.csv` - Datos completos (60,000 filas)
- `results/montecarlo/resumen_estadisticas.csv` - Estadisticas por configuracion
- `results/montecarlo/intervalos_confianza.csv` - Intervalos de confianza al 95%
- `results/montecarlo/metadata_experimento.json` - Metadatos y resultados ANOVA
- `mitesis/figuras/` - Figuras en PDF y SVG (publication-ready)

---

## Figuras Generadas

1. **distribuciones.pdf** - Violin plots del nivel de servicio por configuracion
2. **efectos_principales.pdf** - Efectos principales con intervalos de confianza 95%
3. **heatmap_interacciones.pdf** - Heatmap de interacciones Capacidad x Duracion
4. **analisis_sensibilidad.pdf** - Tornado diagram (analisis de sensibilidad)
5. **distribuciones_kde.pdf** - Distribuciones de probabilidad (KDE)
6. **qq_plots.pdf** - Q-Q plots (validacion de normalidad)
7. **boxplot_comparativo.pdf** - Boxplot comparativo de todas las configuraciones

---

## Analisis Estadistico

### ANOVA de Dos Vias

El experimento calcula automaticamente:

- ANOVA Tipo II con interaccion Capacidad x Duracion
- Valores p para cada factor e interaccion (alpha = 0.05)
- Tamano del efecto (eta cuadrado)
- R cuadrado ajustado del modelo
- Tests post-hoc (Tukey HSD) para comparaciones multiples
- Intervalos de confianza al 95% para cada configuracion

### Metricas Clave (KPIs)

| KPI | Descripcion |
|-----|-------------|
| **Nivel de Servicio** | % de demanda satisfecha (metrica principal de resiliencia) |
| **Probabilidad de Quiebre** | % de dias con inventario insuficiente |
| **Dias con Quiebre** | Numero de dias con quiebre de stock |
| **Autonomia Promedio** | Dias de inventario restantes |
| **Disrupciones Totales** | Numero de eventos de disrupcion |
| **% Tiempo Bloqueado** | Porcentaje del ano con ruta bloqueada |

---

## Validacion del Modelo

### Criterios de Validacion

1. **Autonomia Status Quo:** Debe estar cerca de 8.2 dias (dato real del informe CNE)
2. **Rango de Nivel de Servicio:** 90-100% (sistema resiliente pero con variabilidad)
3. **Disrupciones/ano:** Aproximadamente 4 eventos (Nivel 4 de frecuencia)
4. **Normalidad:** Distribuciones pasan tests de Shapiro-Wilk (validado con Q-Q plots)

---

## Distribuciones Probabilisticas Utilizadas

| Variable | Distribucion | Parametros | Justificacion |
|----------|--------------|------------|---------------|
| **Tiempo entre disrupciones** | Exponencial | lambda = 4/365 dia^-1 | Proceso de Poisson (eventos raros independientes) |
| **Duracion de disrupciones** | Triangular | (min, mode, max) | Parametros interpretables, datos limitados |
| **Demanda diaria** | Normal | mu=1.0, sigma=0.15 | Variabilidad estocastica (ruido) |
| **Estacionalidad** | Sinusoidal | A=0.30, T=365 dias | Ciclo invernal conocido |

### Generacion de Numeros Aleatorios

- **Generador:** Mersenne Twister (MT19937) de NumPy
- **Semillas:** Unicas por configuracion y replica: s = 42 + (config-1)*100000 + replica
- **Garantiza:** Reproducibilidad exacta y independencia estadistica

---

## Como Funciona el Modelo

### Procesos SimPy Concurrentes

```python
1. procesoDemandaDiaria()
   - Genera demanda con estacionalidad y ruido
   - Intenta satisfacer demanda desde inventario
   - Registra quiebres de stock

2. procesoReabastecimiento()
   - Monitorea inventario vs punto de reorden (ROP)
   - Crea pedidos cuando inventario <= ROP
   - Maximo 2 pedidos simultaneos

3. procesoDisrupciones()
   - Genera disrupciones segun Proceso de Poisson
   - Bloquea ruta por duracion ~ Triangular(min, mode, max)
   - Extiende lead time de pedidos en transito
```

### Politica de Inventario (Q, R)

- **R (Punto de Reorden):** 50% de la capacidad
- **Q (Cantidad de Pedido):** 50% de la capacidad
- **Inventario Inicial:** 60% de la capacidad
- **Lead Time:** 6 dias nominal (+extension por disrupciones)

---

## Extensiones y Trabajo Futuro

### Extensiones Implementables

1. Multiples nodos de distribucion regional
2. Crecimiento de demanda con tendencia anual
3. Central termica con demanda adicional
4. Rutas alternativas para redundancia logistica
5. Politicas dinamicas de inventario

### Lineas de Investigacion

- Optimizacion de politicas de inventario bajo incertidumbre
- Analisis costo-beneficio de inversiones en resiliencia
- Modelos de riesgo sistemico multi-region
- Integracion con modelos de cambio climatico

---

## Referencias

- Informe CNE 2024: "Vulnerabilidad de Suministro de GLP en Region de Aysen"
- Politica Energetica 2050 Aysen, Seremi de Energia, Gobierno de Chile
- SimPy Documentation: https://simpy.readthedocs.io
- Law & Kelton (2015): Simulation Modeling and Analysis, 5th ed.

---

## Contacto

**Autor:** Carlos Subiabre
**Instituciones:** Universidad de Chile / Universidad Austral de Chile

---

## Licencia

Este proyecto es parte de una tesis de grado y esta disponible para fines academicos y de investigacion.

---

## Agradecimientos

- Seremía de Energia de Aysen por facilitar acceso a datos operativos
- Centro de Innovacion y Emprendimiento de la Patagonia (CIEP) por el informe de referencia
- Distribuidores de GLP (Abastible, Lipigas, Gasco) por datos de capacidad
