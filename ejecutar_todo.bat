@echo off
REM Script para ejecutar simulación completa de GLP Aysén
REM Uso: Doble clic o ejecutar desde terminal

echo ================================================================================
echo SIMULACION COMPLETA - CADENA DE SUMINISTRO GLP AYSEN
echo ================================================================================
echo.

REM Verificar que estamos en el directorio correcto
if not exist "configs\escenario_aysen_base.yml" (
    echo ERROR: No se encuentra el archivo de configuracion
    echo Asegurate de estar en el directorio correcto del proyecto
    pause
    exit /b 1
)

echo Paso 1/3: Instalando dependencias con Poetry...
echo --------------------------------------------------------------------------------
poetry install
if errorlevel 1 (
    echo ERROR: Fallo la instalacion de dependencias
    pause
    exit /b 1
)
echo OK
echo.

echo Paso 2/3: Ejecutando simulacion base (365 dias)...
echo --------------------------------------------------------------------------------
poetry run python scripts\ejecutar_simulacion_base.py
if errorlevel 1 (
    echo ERROR: Fallo la simulacion
    pause
    exit /b 1
)
echo OK
echo.

echo Paso 3/3: Generando graficos de analisis...
echo --------------------------------------------------------------------------------
poetry run python scripts\visualizar_resultados.py
if errorlevel 1 (
    echo ERROR: Fallo la generacion de graficos
    pause
    exit /b 1
)
echo OK
echo.

echo ================================================================================
echo PROCESO COMPLETADO EXITOSAMENTE
echo ================================================================================
echo.
echo Resultados guardados en:
echo   - JSON: results\simulacion_base_resultados.json
echo   - Graficos: results\graficos\*.png
echo.
echo Abriendo carpeta de graficos...
start results\graficos
echo.
echo Presiona cualquier tecla para cerrar...
pause >nul
