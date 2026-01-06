"""
Script para arreglar el bug de semilla_aleatoria y recalcular resultados agregados.

PROBLEMAS DETECTADOS:
1. semilla_aleatoria puede ser null → causa NoneType * int error
2. Experimentos marcados como "completed" aunque todas las réplicas fallaron
3. resultados_agregados queda vacío

SOLUCIÓN:
1. Arreglar el servicio para manejar null
2. Re-calcular resultados agregados si hay réplicas completadas
3. Listar experimentos que necesitan re-ejecución
"""

import sys
from pathlib import Path

# Agregar backend al path
sys.path.insert(0, str(Path(__file__).parent))

from app.db.session import SessionLocal
from app.models.montecarlo import MonteCarloExperiment, MonteCarloReplica
from app.services.montecarlo_service import calcular_estadisticas_agregadas


def analizar_experimentos():
    """Analiza el estado de todos los experimentos Monte Carlo."""
    db = SessionLocal()

    try:
        experiments = db.query(MonteCarloExperiment).filter(
            MonteCarloExperiment.estado == "completed"
        ).all()

        print("="*80)
        print("ANÁLISIS DE EXPERIMENTOS MONTECARLO")
        print("="*80)
        print(f"\nExperimentos completados: {len(experiments)}\n")

        sin_resultados = []
        con_resultados = []
        necesitan_reejecucion = []

        for exp in experiments:
            replicas = db.query(MonteCarloReplica).filter(
                MonteCarloReplica.experiment_id == exp.id
            ).all()

            completadas = sum(1 for r in replicas if r.estado == "completed")
            fallidas = sum(1 for r in replicas if r.estado == "failed")

            if exp.resultados_agregados:
                con_resultados.append(exp)
                status = "✓"
            else:
                sin_resultados.append(exp)
                status = "✗"

            print(f"{status} ID {exp.id}: {exp.nombre}")
            print(f"   Réplicas: {len(replicas)}/{exp.num_replicas}")
            print(f"   Completadas: {completadas}, Fallidas: {fallidas}")
            print(f"   Resultados agregados: {'SÍ' if exp.resultados_agregados else 'NO'}")

            if fallidas == exp.num_replicas:
                print(f"   ⚠️  TODAS LAS RÉPLICAS FALLARON - NECESITA RE-EJECUCIÓN")
                necesitan_reejecucion.append(exp.id)
            elif completadas > 0 and not exp.resultados_agregados:
                print(f"   ⚠️  HAY RÉPLICAS COMPLETADAS - RECALCULAR RESULTADOS")

            print()

        print("\n" + "="*80)
        print("RESUMEN")
        print("="*80)
        print(f"Con resultados agregados: {len(con_resultados)}")
        print(f"Sin resultados agregados: {len(sin_resultados)}")
        print(f"Necesitan re-ejecución: {len(necesitan_reejecucion)}")

        if necesitan_reejecucion:
            print("\n⚠️  EXPERIMENTOS QUE NECESITAN RE-EJECUCIÓN:")
            print(f"IDs: {necesitan_reejecucion}")
            print("\nESTOS EXPERIMENTOS FALLARON POR EL BUG DE semilla_aleatoria=null")

    finally:
        db.close()


def recalcular_resultados_agregados():
    """Recalcula resultados agregados para experimentos con réplicas completadas."""
    db = SessionLocal()

    try:
        experiments = db.query(MonteCarloExperiment).filter(
            MonteCarloExperiment.estado == "completed",
            MonteCarloExperiment.resultados_agregados == None
        ).all()

        print("\n" + "="*80)
        print("RECALCULANDO RESULTADOS AGREGADOS")
        print("="*80)

        for exp in experiments:
            print(f"\nExperimento {exp.id}: {exp.nombre}")

            # Verificar si hay réplicas completadas
            replicas_completadas = db.query(MonteCarloReplica).filter(
                MonteCarloReplica.experiment_id == exp.id,
                MonteCarloReplica.estado == "completed"
            ).count()

            if replicas_completadas == 0:
                print(f"   ✗ No hay réplicas completadas - SALTAR")
                continue

            print(f"   ✓ {replicas_completadas} réplicas completadas")

            # Cargar todas las réplicas
            replicas = db.query(MonteCarloReplica).filter(
                MonteCarloReplica.experiment_id == exp.id
            ).all()

            # Calcular estadísticas
            stats = calcular_estadisticas_agregadas(replicas)

            if stats:
                exp.resultados_agregados = stats
                db.commit()
                print(f"   ✓ Resultados agregados calculados:")
                print(f"      Nivel de servicio: {stats['nivel_servicio_mean']:.2f}% ± {stats['nivel_servicio_std']:.2f}")
            else:
                print(f"   ✗ No se pudieron calcular estadísticas")

    finally:
        db.close()


if __name__ == "__main__":
    print("\n🔧 DIAGNÓSTICO Y REPARACIÓN DE EXPERIMENTOS MONTECARLO\n")

    # 1. Analizar
    analizar_experimentos()

    # 2. Preguntar si recalcular
    print("\n" + "="*80)
    respuesta = input("\n¿Deseas recalcular resultados agregados para experimentos con réplicas válidas? (s/n): ")

    if respuesta.lower() in ['s', 'si', 'y', 'yes']:
        recalcular_resultados_agregados()
        print("\n✓ Proceso completado")
    else:
        print("\n✗ Operación cancelada")

    print("\n" + "="*80)
    print("SIGUIENTE PASO:")
    print("="*80)
    print("\nPara arreglar el bug y re-ejecutar los experimentos fallidos:")
    print("1. Editar backend/app/services/montecarlo_service.py")
    print("2. Línea 66-68, cambiar:")
    print("   DE:  config_params.get('semilla_aleatoria', 42) * 100000")
    print("   A:   (config_params.get('semilla_aleatoria') or 42) * 100000")
    print("\n3. Reiniciar el backend")
    print("4. Re-ejecutar los experimentos fallidos desde la interfaz web")
    print("="*80 + "\n")
