#!/bin/bash
# Script para ejecutar simulación completa de GLP Aysén
# Uso: ./ejecutar_todo.sh

set -e  # Salir si cualquier comando falla

echo "================================================================================"
echo "SIMULACION COMPLETA - CADENA DE SUMINISTRO GLP AYSEN"
echo "================================================================================"
echo ""

# Verificar que estamos en el directorio correcto
if [ ! -f "configs/escenario_aysen_base.yml" ]; then
    echo "ERROR: No se encuentra el archivo de configuracion"
    echo "Asegurate de estar en el directorio correcto del proyecto"
    exit 1
fi

echo "Paso 1/3: Instalando dependencias con Poetry..."
echo "--------------------------------------------------------------------------------"
poetry install
echo "OK"
echo ""

echo "Paso 2/3: Ejecutando simulacion base (365 dias)..."
echo "--------------------------------------------------------------------------------"
poetry run python scripts/ejecutar_simulacion_base.py
echo "OK"
echo ""

echo "Paso 3/3: Generando graficos de analisis..."
echo "--------------------------------------------------------------------------------"
poetry run python scripts/visualizar_resultados.py
echo "OK"
echo ""

echo "================================================================================"
echo "PROCESO COMPLETADO EXITOSAMENTE"
echo "================================================================================"
echo ""
echo "Resultados guardados en:"
echo "  - JSON: results/simulacion_base_resultados.json"
echo "  - Graficos: results/graficos/*.png"
echo ""

# Intentar abrir carpeta de gráficos
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open results/graficos
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open results/graficos 2>/dev/null || echo "Abre manualmente: results/graficos/"
fi

echo ""
echo "Presiona Enter para continuar..."
read
