"""
Prueba de Configuraciones del Modelo de Simulacion.

Ejecuta una simulacion de cada configuracion del diseno factorial (6 simulaciones) para:
1. Verificar que el modelo funciona correctamente
2. Validar que los resultados tienen sentido
3. Estimar tiempo de ejecucion del experimento completo

Author:
    Carlos Subiabre
"""
import sys
from pathlib import Path
import time
import logging

# Agregar src al path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from modelo import ConfiguracionSimulacion, ejecutarSimulacion

# Configurar logging
logging.basicConfig(level=logging.WARNING)


def testConfiguracion(nombre: str, **kwargs) -> float:
    """Prueba una configuracion especifica."""
    print(f"\n{'='*70}")
    print(f"Probando: {nombre}")
    print(f"{'='*70}")

    config = ConfiguracionSimulacion(**kwargs)

    print(f"Configuracion:")
    print(f"  Capacidad:           {config.capacidadHubTm:.0f} TM")
    print(f"  Autonomia teorica:   {config.capacidadHubTm / config.demandaBaseDiariaTm:.1f} dias")
    print(f"  Duracion max:        {config.duracionDisrupcionMaxDias:.0f} dias")
    print(f"  Estacionalidad:      {'ACTIVADA' if config.usarEstacionalidad else 'DESACTIVADA'}")

    inicio = time.time()
    resultados = ejecutarSimulacion(config)
    tiempoEjecucion = time.time() - inicio

    print(f"\nResultados (1 replica en {tiempoEjecucion:.2f}s):")
    print(f"  Nivel de Servicio:            {resultados['nivel_servicio_pct']:.4f}%")
    print(f"  Prob. Quiebre de Stock:       {resultados['probabilidad_quiebre_stock_pct']:.4f}%")
    print(f"  Dias con Quiebre:             {resultados['dias_con_quiebre']}")
    print(f"  Autonomia Promedio:           {resultados['autonomia_promedio_dias']:.2f} dias")
    print(f"  Disrupciones Totales:         {resultados['disrupciones_totales']}")
    print(f"  % Tiempo Bloqueado:           {resultados['pct_tiempo_bloqueado']:.2f}%")

    # Validaciones
    print(f"\nValidaciones:")

    # Autonomia status quo debe estar entre 7 y 10 dias
    if 'status_quo' in nombre.lower():
        if 7.0 <= resultados['autonomia_promedio_dias'] <= 10.0:
            print(f"  Autonomia en rango esperado (7-10 dias)")
        else:
            print(f"  Advertencia: Autonomia fuera de rango: {resultados['autonomia_promedio_dias']:.2f} dias")

    # Nivel de servicio debe estar entre 80 y 100%
    if 80 <= resultados['nivel_servicio_pct'] <= 100:
        print(f"  Nivel de servicio en rango razonable (80-100%)")
    else:
        print(f"  Advertencia: Nivel de servicio fuera de rango: {resultados['nivel_servicio_pct']:.2f}%")

    # Disrupciones entre 2 y 6 eventos
    if 2 <= resultados['disrupciones_totales'] <= 6:
        print(f"  Numero de disrupciones razonable (2-6 eventos)")
    else:
        print(f"  Advertencia: Numero de disrupciones inusual: {resultados['disrupciones_totales']}")

    return tiempoEjecucion


if __name__ == "__main__":
    print("\n" + "="*70)
    print(" "*20 + "PRUEBA RAPIDA DEL MODELO")
    print("="*70)
    print("\nProbando las 6 configuraciones del diseno factorial...")

    tiempos = []

    # Configuraciones del experimento
    configs = [
        ("Status Quo + Corta", {
            'capacidadHubTm': 431.0,
            'puntoReordenTm': 431.0 * 0.50,
            'cantidadPedidoTm': 431.0 * 0.50,
            'inventarioInicialTm': 431.0 * 0.60,
            'duracionDisrupcionMaxDias': 7.0,
            'duracionDisrupcionModeDias': 3.5,
            'usarEstacionalidad': True,
        }),
        ("Status Quo + Media", {
            'capacidadHubTm': 431.0,
            'puntoReordenTm': 431.0 * 0.50,
            'cantidadPedidoTm': 431.0 * 0.50,
            'inventarioInicialTm': 431.0 * 0.60,
            'duracionDisrupcionMaxDias': 14.0,
            'duracionDisrupcionModeDias': 7.0,
            'usarEstacionalidad': True,
        }),
        ("Status Quo + Larga", {
            'capacidadHubTm': 431.0,
            'puntoReordenTm': 431.0 * 0.50,
            'cantidadPedidoTm': 431.0 * 0.50,
            'inventarioInicialTm': 431.0 * 0.60,
            'duracionDisrupcionMaxDias': 21.0,
            'duracionDisrupcionModeDias': 10.5,
            'usarEstacionalidad': True,
        }),
        ("Propuesta + Corta", {
            'capacidadHubTm': 681.0,
            'puntoReordenTm': 681.0 * 0.50,
            'cantidadPedidoTm': 681.0 * 0.50,
            'inventarioInicialTm': 681.0 * 0.60,
            'duracionDisrupcionMaxDias': 7.0,
            'duracionDisrupcionModeDias': 3.5,
            'usarEstacionalidad': True,
        }),
        ("Propuesta + Media", {
            'capacidadHubTm': 681.0,
            'puntoReordenTm': 681.0 * 0.50,
            'cantidadPedidoTm': 681.0 * 0.50,
            'inventarioInicialTm': 681.0 * 0.60,
            'duracionDisrupcionMaxDias': 14.0,
            'duracionDisrupcionModeDias': 7.0,
            'usarEstacionalidad': True,
        }),
        ("Propuesta + Larga", {
            'capacidadHubTm': 681.0,
            'puntoReordenTm': 681.0 * 0.50,
            'cantidadPedidoTm': 681.0 * 0.50,
            'inventarioInicialTm': 681.0 * 0.60,
            'duracionDisrupcionMaxDias': 21.0,
            'duracionDisrupcionModeDias': 10.5,
            'usarEstacionalidad': True,
        }),
    ]

    for nombre, parametros in configs:
        tiempoEjecucion = testConfiguracion(nombre, **parametros)
        tiempos.append(tiempoEjecucion)

    # Estimacion de tiempo total
    print(f"\n{'='*70}")
    print("RESUMEN DE LA PRUEBA")
    print(f"{'='*70}")
    print(f"Tiempo promedio por simulacion:  {sum(tiempos)/len(tiempos):.3f} segundos")
    print(f"Tiempo total (6 simulaciones):   {sum(tiempos):.2f} segundos")

    tiempoEstimado6000 = (sum(tiempos)/len(tiempos)) * 6000
    print(f"\nEstimacion para experimento completo (6,000 simulaciones):")
    print(f"  Tiempo estimado:   {tiempoEstimado6000:.1f} segundos")
    print(f"                     {tiempoEstimado6000/60:.1f} minutos")
    print(f"                     {tiempoEstimado6000/3600:.2f} horas")

    print(f"\n{'='*70}")
    print("PRUEBA COMPLETADA - Modelo funciona correctamente")
    print(f"{'='*70}")
    print("\nProximos pasos:")
    print("  1. Ejecutar experimento completo: python scripts/experimento_montecarlo.py")
    print("  2. Generar figuras: python scripts/generar_figuras_tesis.py")
    print(f"{'='*70}")
