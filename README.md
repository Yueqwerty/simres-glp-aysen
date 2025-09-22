# SimRes-GLP-Aysén: Gemelo Digital para Análisis de Resiliencia

![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)
![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)
![Status](https://img.shields.io/badge/status-en--desarrollo-green.svg)
![Built with](https://img.shields.io/badge/Built%20with-SimPy%20%7C%20NumPy%20%7C%20Pandas-red)

Un prototipo de simulación de eventos discretos para el análisis cuantitativo de la resiliencia en la cadena de suministro de GLP de la Región de Aysén.

---

## 1. Planteamiento del Problema y Propósito

La Región de Aysén presenta una **vulnerabilidad energética estructural** debido a su alta dependencia del GLP, cuyo suministro se basa en una topología logística lineal con un único punto de fallo. Los marcos de análisis actuales son estáticos y no permiten cuantificar el **impacto dinámico** de las disrupciones ni evaluar el retorno en resiliencia de posibles inversiones.

Este proyecto aborda esa brecha metodológica mediante la construcción de un **Gemelo Digital**: un laboratorio virtual de alta fidelidad que simula la cadena de suministro completa. El propósito de este prototipo es:

-   **Cuantificar la Resiliencia:** Medir el rendimiento del sistema (ej. Nivel de Servicio) bajo estrés estocástico.
-   **Probar la Hipótesis:** Evaluar si la resiliencia es más sensible a factores exógenos (disrupciones) que a endógenos (inversiones en capacidad).
-   **Descubrir Patrones de Fallo:** Utilizar técnicas de Machine Learning y Teoría de Grafos para identificar las "secuencias de la fatalidad" y los arquetipos de crisis sistémicas.
-   **Facilitar la Toma de Decisiones:** Proveer una herramienta empírica para evaluar el impacto de distintas estrategias de mitigación e inversión.

## 2. Arquitectura del Sistema

El sistema está diseñado con una arquitectura modular desacoplada, siguiendo el principio de responsabilidad única.
+--------------------------------+
| Orquestadores (scripts/) |
| (Typer, Multiprocessing) |
+--------------------------------+
|
v
+--------------------------------+
| Motor de Simulación (src/) |
| (Python, SimPy, NumPy) |
+----------------+---------------+
| | |
| v v
| +-------------------------+ +---------------------------+
| | Configuración | | Sistema de Disrupciones |
| | (YAML Parser) | | (Gestor de Eventos) |
| +-------------------------+ +---------------------------+
| | |
| v v
| +-------------------------------------------------------+
| | Gemelo Digital (Entidades: Planta, Camión, Proveedor) |
| +-------------------------------------------------------+
| |
| v
+--------------------------------+ +--------------------------+
| Pipeline de Datos |------>| Motor de Análisis |
| (Monitores, Pandas) | | (Scikit-learn, NetworkX) |
+--------------------------------+ +-------------+------------+
| |
v v
+--------------------------------+ +--------------------------+
| Almacenamiento (results/) | | Kernel de Cómputo en C |
| (Parquet, JSON) | | (Análisis de Grafos) |
+--------------------------------+ +--------------------------+
code
Code
## 3. Stack Tecnológico

| Categoría | Tecnología | Propósito en el Proyecto |
| :--- | :--- | :--- |
| **Núcleo de Simulación**| Python 3.11+ | Lenguaje principal por su ecosistema científico y legibilidad. |
| | SimPy | Motor de Simulación de Eventos Discretos (DES) para la gestión del tiempo. |
| | NumPy | Implementación de la estocasticidad (generación de variables aleatorias). |
| **Pipeline de Datos** | YAML | Definición de escenarios experimentales de forma declarativa y legible. |
| | Pandas | Estructuración y manipulación de los datos de series de tiempo generados. |
| | Apache Parquet | Almacenamiento columnar de alto rendimiento para los resultados masivos del DoE. |
| **Motor de Análisis** | Scikit-learn | Aplicación de algoritmos de Machine Learning (Clustering) para identificar arquetipos de fallo. |
| | NetworkX | Modelado y análisis de los grafos de transición de eventos. |
| | Matplotlib / Seaborn | Generación de visualizaciones y gráficos de alta calidad para la memoria. |
| **Optimización** | Lenguaje C (GCC) | Implementación de un kernel de cómputo para los algoritmos de análisis de secuencias más intensivos, llamado desde Python. |
| **Orquestación y Entorno** | Poetry | Gestión de dependencias y garantía de un entorno 100% reproducible. |
| | Typer | Construcción de una Interfaz de Línea de Comandos (CLI) robusta y auto-documentada. |

## 4. Guía de Uso

### 4.1. Configuración del Entorno

**Pre-requisitos:**
-   Python 3.11+
-   Poetry (gestor de paquetes de Python)
-   Un compilador de C (GCC) disponible en el PATH del sistema (recomendado: [MSYS2](https://www.msys2.org/) para Windows).

**Instalación:**

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/TU_USUARIO/simres-glp-aysen.git
    cd simres-glp-aysen
    ```

2.  **Instalar dependencias de Python:**
    Este comando creará un entorno virtual y descargará todas las librerías necesarias.
    ```bash
    poetry install
    ```

3.  **Compilar el kernel de análisis en C:**
    ```bash
    # Navegar al directorio del kernel
    cd src/analisis_c
    
    # Compilar (usando el Makefile simplificado)
    make 
    
    # Volver a la raíz del proyecto
    cd ../..
    ```

### 4.2. Flujo de Trabajo de Simulación y Análisis

Todos los comandos se ejecutan desde el directorio raíz del proyecto.

> **Nota:** Se utiliza `python -m <ruta.modulo>` para asegurar que Python reconozca la estructura del proyecto (`src/`, `scripts/`) correctamente.

1.  **Validar un archivo de configuración (Dry Run):**
    ```bash
    poetry run python -m scripts.ejecutar_simulacion validar-config configs/escenario_aysen_real.yml
    ```

2.  **Ejecutar una única simulación:**
    Ideal para depuración y pruebas rápidas.
    ```bash
    poetry run python -m scripts.ejecutar_simulacion ejecutar configs/escenario_aysen_real.yml results/sim_individual_01
    ```

3.  **Generar un Diseño de Experimentos (DoE):**
    Crea automáticamente múltiples archivos de configuración para un análisis factorial.
    ```bash
    # Crear un nuevo directorio para las configuraciones generadas
    mkdir generated_configs
    
    # Generar los archivos
    poetry run python -m scripts.ejecutar_experimentos generar-factorial configs/escenario_base.yml generated_configs/ --factores "planta.capacidad_maxima:180000,250000;riesgos.57-ST-CU.probabilidad_anual:4,6"
    ```

4.  **Ejecutar el DoE en Paralelo:**
    Lanza todas las simulaciones del DoE, utilizando todos los núcleos de la CPU.
    ```bash
    poetry run python -m scripts.ejecutar_experimentos ejecutar-paralelo generated_configs/ results_doe/
    ```

5.  **Analizar los Resultados Masivos:**
    Una vez completado el DoE, utiliza el motor de análisis para extraer conocimiento.
    ```bash
    # Análisis estadístico y de sensibilidad
    poetry run python -m scripts.analizar_resultados stats results_doe/ --output-path results_doe/analisis_estadistico.json
    
    # Clustering para encontrar arquetipos de fallo
    poetry run python -m scripts.analizar_resultados cluster results_doe/ --output-dir results_doe/clustering/
    
    # Análisis de grafos para encontrar secuencias críticas
    poetry run python -m scripts.analizar_resultados graph results_doe/ --output-dir results_doe/grafos/
    ```

## 5. Hoja de Ruta del Proyecto

-   [x] **Hito 0: Configuración del Entorno Profesional.**
-   [ ] **Hito 1: Implementación del Gemelo Digital Base.** (Modelo estocástico con reabastecimiento y demanda realista).
-   [ ] **Hito 2: Activación del Sistema de Disrupciones.** (Implementación completa de la lógica de los 77 riesgos).
-   [ ] **Hito 3: Ejecución del Diseño de Experimentos.** (Generación del dataset masivo).
-   [ ] **Hito 4: Análisis de Resultados y Validación de Hipótesis.** (Extracción de conclusiones).

## 6. Licencia

Este proyecto está licenciado bajo los términos de la **Licencia MIT**. Puedes encontrar el texto completo en el archivo `LICENSE`.```