"""Endpoints API para experimentos Monte Carlo.

Este módulo expone los endpoints REST para crear, ejecutar y consultar
experimentos Monte Carlo con múltiples réplicas.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.orm import Session
import pandas as pd

from app.api.deps import get_db
from app.models.configuracion import Configuracion
from app.models.montecarlo import MonteCarloExperiment
from app.schemas.montecarlo import (
    MonteCarloExperiment as MonteCarloExperimentSchema,
    MonteCarloExperimentCreate,
    MonteCarloExperimentDetail,
    MonteCarloProgress,
)
from app.services.montecarlo_service import ejecutar_experimento_montecarlo
from app.services.anova_service import calcular_anova_dos_vias, formatear_resultados_anova

router = APIRouter()


@router.post(
    "/start",
    response_model=MonteCarloExperimentSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar experimento Monte Carlo",
    description="""
    Crea e inicia un nuevo experimento Monte Carlo.

    El experimento ejecutará múltiples réplicas de la simulación en paralelo
    usando diferentes semillas aleatorias para cada réplica.

    Los resultados se procesarán de forma asíncrona en segundo plano.
    Use el endpoint /experiments/{id} para consultar el progreso y resultados.

    Límites:
    - Mínimo 100 réplicas
    - Máximo 100,000 réplicas
    - Mínimo 1 worker
    - Máximo 16 workers paralelos
    """,
)
def start_monte_carlo(
    *,
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks,
    experiment_in: MonteCarloExperimentCreate,
) -> MonteCarloExperiment:
    """Crear e iniciar un experimento Monte Carlo.

    Args:
        db: Sesión de base de datos
        background_tasks: Gestor de tareas en segundo plano
        experiment_in: Datos del experimento a crear

    Returns:
        Experimento creado (en estado 'pending')

    Raises:
        HTTPException: Si la configuración no existe
    """
    # Verificar que la configuración existe
    config = db.query(Configuracion).filter(
        Configuracion.id == experiment_in.configuracion_id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuración {experiment_in.configuracion_id} no encontrada",
        )

    # Generar nombre si no se proveyó
    nombre = experiment_in.nombre
    if not nombre:
        nombre = f"MC-{config.nombre}-{experiment_in.num_replicas}rep"

    # Crear experimento
    experiment = MonteCarloExperiment(
        configuracion_id=experiment_in.configuracion_id,
        nombre=nombre,
        num_replicas=experiment_in.num_replicas,
        max_workers=experiment_in.max_workers,
        estado="pending",
        progreso=0,
    )

    db.add(experiment)
    db.commit()
    db.refresh(experiment)

    # Ejecutar en segundo plano (sin pasar db, se creará nueva sesión)
    background_tasks.add_task(
        ejecutar_experimento_montecarlo,
        experiment_id=experiment.id,
    )

    return experiment


@router.get(
    "/experiments",
    response_model=list[MonteCarloExperimentSchema],
    summary="Listar experimentos Monte Carlo",
    description="""
    Obtiene la lista de todos los experimentos Monte Carlo.

    Los experimentos se devuelven ordenados del más reciente al más antiguo.
    """,
)
def list_experiments(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
) -> list[MonteCarloExperiment]:
    """Listar todos los experimentos Monte Carlo.

    Args:
        db: Sesión de base de datos
        skip: Número de experimentos a saltar (paginación)
        limit: Número máximo de experimentos a devolver

    Returns:
        Lista de experimentos
    """
    experiments = (
        db.query(MonteCarloExperiment)
        .order_by(MonteCarloExperiment.iniciado_en.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    return experiments


@router.get(
    "/experiments/{experiment_id}",
    response_model=MonteCarloExperimentDetail,
    summary="Obtener detalles de un experimento",
    description="""
    Obtiene los detalles completos de un experimento Monte Carlo,
    incluyendo todas sus réplicas.

    Use este endpoint para obtener resultados detallados una vez
    que el experimento haya completado.
    """,
)
def get_experiment(
    *,
    db: Session = Depends(get_db),
    experiment_id: int,
) -> MonteCarloExperiment:
    """Obtener detalles de un experimento específico.

    Args:
        db: Sesión de base de datos
        experiment_id: ID del experimento

    Returns:
        Experimento con réplicas incluidas

    Raises:
        HTTPException: Si el experimento no existe
    """
    experiment = db.query(MonteCarloExperiment).filter(
        MonteCarloExperiment.id == experiment_id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experimento {experiment_id} no encontrado",
        )

    return experiment


@router.get(
    "/experiments/{experiment_id}/progress",
    response_model=MonteCarloProgress,
    summary="Obtener progreso de un experimento",
    description="""
    Consulta el progreso actual de un experimento en ejecución.

    Use este endpoint para polling del estado mientras el experimento
    está ejecutándose (estado 'running').

    El progreso se reporta como porcentaje (0-100) y número de réplicas
    completadas vs. totales.
    """,
)
def get_experiment_progress(
    *,
    db: Session = Depends(get_db),
    experiment_id: int,
) -> MonteCarloProgress:
    """Obtener progreso de un experimento en ejecución.

    Args:
        db: Sesión de base de datos
        experiment_id: ID del experimento

    Returns:
        Información de progreso actual

    Raises:
        HTTPException: Si el experimento no existe
    """
    experiment = db.query(MonteCarloExperiment).filter(
        MonteCarloExperiment.id == experiment_id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experimento {experiment_id} no encontrado",
        )

    # Contar réplicas completadas
    replicas_completadas = len([
        r for r in experiment.replicas
        if r.estado in ("completed", "failed")
    ])

    # Calcular tiempo transcurrido
    import datetime
    tiempo_transcurrido = (
        datetime.datetime.utcnow() - experiment.iniciado_en
    ).total_seconds()

    # Estimar tiempo restante
    tiempo_estimado_restante = None
    if replicas_completadas > 0 and experiment.estado == "running":
        tiempo_por_replica = tiempo_transcurrido / replicas_completadas
        replicas_restantes = experiment.num_replicas - replicas_completadas
        tiempo_estimado_restante = tiempo_por_replica * replicas_restantes

    return MonteCarloProgress(
        experiment_id=experiment.id,
        estado=experiment.estado,
        progreso=experiment.progreso,
        replicas_completadas=replicas_completadas,
        replicas_totales=experiment.num_replicas,
        tiempo_transcurrido_segundos=tiempo_transcurrido,
        tiempo_estimado_restante_segundos=tiempo_estimado_restante,
    )


@router.delete(
    "/experiments/{experiment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar o cancelar un experimento",
    description="""
    Elimina un experimento Monte Carlo y todas sus réplicas.

    Si el experimento está en ejecución, se marca como 'failed' para cancelarlo.
    Los experimentos completados o fallidos se eliminan permanentemente.

    Esta operación es irreversible.
    """,
)
def delete_experiment(
    *,
    db: Session = Depends(get_db),
    experiment_id: int,
) -> None:
    """Eliminar o cancelar un experimento Monte Carlo.

    Args:
        db: Sesión de base de datos
        experiment_id: ID del experimento a eliminar/cancelar

    Raises:
        HTTPException: Si el experimento no existe
    """
    experiment = db.query(MonteCarloExperiment).filter(
        MonteCarloExperiment.id == experiment_id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experimento {experiment_id} no encontrado",
        )

    if experiment.estado == "running":
        # Cancelar experimento en ejecución
        experiment.estado = "failed"
        experiment.error_mensaje = "Experimento cancelado por el usuario"
        import datetime
        experiment.completado_en = datetime.datetime.utcnow()
        if experiment.iniciado_en:
            experiment.duracion_segundos = (experiment.completado_en - experiment.iniciado_en).total_seconds()
        db.commit()
    else:
        # Eliminar experimento completado/fallido
        db.delete(experiment)
        db.commit()


@router.get(
    "/experiments/{experiment_id}/anova",
    summary="Análisis ANOVA del experimento",
    description="""
    Calcula y retorna el análisis ANOVA de dos vías para un experimento Monte Carlo.

    El análisis incluye:
    - Tabla ANOVA completa (Suma de Cuadrados, grados de libertad, Media Cuadrática, F, p-valor)
    - Efectos principales de cada factor
    - Tamaños del efecto (eta cuadrado)
    - Tests post-hoc (Tukey HSD)
    - R² ajustado del modelo
    - Medias por configuración con intervalos de confianza

    Requiere que el experimento esté completado y tenga al menos 2 niveles
    de cada factor para poder calcular el ANOVA.
    """,
)
def get_experiment_anova(
    *,
    db: Session = Depends(get_db),
    experiment_id: int,
):
    """Calcula ANOVA de dos vías para los resultados del experimento.

    Args:
        db: Sesión de base de datos
        experiment_id: ID del experimento

    Returns:
        Resultados completos del análisis ANOVA

    Raises:
        HTTPException: Si el experimento no existe o no está completado
    """
    # Obtener experimento
    experiment = db.query(MonteCarloExperiment).filter(
        MonteCarloExperiment.id == experiment_id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experimento {experiment_id} no encontrado",
        )

    if experiment.estado != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El experimento debe estar completado para calcular ANOVA. Estado actual: {experiment.estado}",
        )

    if not experiment.replicas or len(experiment.replicas) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El experimento no tiene réplicas para analizar",
        )

    # Extraer datos de las réplicas
    # IMPORTANTE: MonteCarloReplica tiene los KPIs desnormalizados directamente
    datos_replicas = []
    for replica in experiment.replicas:
        # Solo incluir réplicas completadas con datos válidos
        if replica.estado == "completed" and replica.nivel_servicio_pct is not None:
            datos_replicas.append({
                'replica_id': replica.id,
                'nivel_servicio': replica.nivel_servicio_pct,
                'prob_quiebre': replica.probabilidad_quiebre_stock_pct or 0,
                'dias_quiebre': replica.dias_con_quiebre or 0,
                'autonomia_promedio': replica.autonomia_promedio_dias or 0,
                'inventario_promedio': replica.inventario_promedio_tm or 0,
                'capacidad': experiment.configuracion.parametros.get('capacidad_hub_tm', 431),
                'duracion_max': experiment.configuracion.parametros.get('duracion_maxima_disrupcion', 14),
            })

    if len(datos_replicas) < 4:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Se necesitan al menos 4 réplicas completadas para calcular ANOVA. Solo se encontraron {len(datos_replicas)} réplicas válidas.",
        )

    # Convertir a DataFrame
    df = pd.DataFrame(datos_replicas)

    # Crear factores categóricos
    # Capacidad: convertir a Status Quo (431) / Propuesta (681)
    df['capacidad_cat'] = df['capacidad'].apply(
        lambda x: 'Status Quo' if x <= 450 else 'Propuesta'
    )

    # Duración: Corta (7) / Media (14) / Larga (21)
    df['duracion_cat'] = df['duracion_max'].apply(
        lambda x: 'Corta' if x <= 7 else ('Media' if x <= 14 else 'Larga')
    )

    # Validar que hay al menos 2 niveles de cada factor
    num_capacidades = df['capacidad_cat'].nunique()
    num_duraciones = df['duracion_cat'].nunique()

    if num_capacidades < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Se necesitan al menos 2 niveles del factor Capacidad para ANOVA. Solo se encontró: {num_capacidades} nivel(es). Este experimento solo tiene una configuración de capacidad.",
        )

    if num_duraciones < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Se necesitan al menos 2 niveles del factor Duración para ANOVA. Solo se encontró: {num_duraciones} nivel(es). Este experimento solo tiene una configuración de duración.",
        )

    # Debug: imprimir información del DataFrame
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"DataFrame shape: {df.shape}")
    logger.info(f"DataFrame columns: {df.columns.tolist()}")
    logger.info(f"Capacidades únicas: {df['capacidad_cat'].unique()}")
    logger.info(f"Duraciones únicas: {df['duracion_cat'].unique()}")
    logger.info(f"Primeras filas:\n{df.head()}")

    try:
        # Calcular ANOVA
        resultado = calcular_anova_dos_vias(
            data=df,
            variable_respuesta='nivel_servicio',
            factor_1='capacidad_cat',
            factor_2='duracion_cat'
        )

        # Formatear para JSON
        return formatear_resultados_anova(resultado)

    except Exception as e:
        import traceback
        logger.error(f"Error completo al calcular ANOVA: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al calcular ANOVA: {str(e)}. Tipo: {type(e).__name__}",
        )


@router.get(
    "/experiments/{experiment_id}/replicas",
    summary="Obtener réplicas de un experimento",
    description="""
    Devuelve todas las réplicas completadas de un experimento Monte Carlo
    en formato simplificado para visualizaciones.

    Los datos incluyen métricas clave de cada réplica:
    - Nivel de servicio
    - Días con quiebre
    - Inventario promedio
    - Autonomía promedio
    - Probabilidad de quiebre de stock

    Útil para generar histogramas, boxplots, y otros gráficos de distribución.
    """,
)
def get_experiment_replicas(
    *,
    db: Session = Depends(get_db),
    experiment_id: int,
):
    """Obtener réplicas de un experimento para visualizaciones.

    Args:
        db: Sesión de base de datos
        experiment_id: ID del experimento

    Returns:
        Lista de réplicas con métricas clave

    Raises:
        HTTPException: Si el experimento no existe o no está completado
    """
    from app.models.montecarlo import MonteCarloReplica

    experiment = db.query(MonteCarloExperiment).filter(
        MonteCarloExperiment.id == experiment_id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experimento {experiment_id} no encontrado",
        )

    if experiment.estado != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El experimento debe estar completado. Estado actual: {experiment.estado}",
        )

    # Obtener réplicas completadas
    replicas = db.query(MonteCarloReplica).filter(
        MonteCarloReplica.experiment_id == experiment_id,
        MonteCarloReplica.estado == "completed"
    ).all()

    # Formatear datos
    datos = []
    for replica in replicas:
        datos.append({
            "replica_id": replica.id,
            "nivel_servicio_pct": replica.nivel_servicio_pct,
            "dias_con_quiebre": replica.dias_con_quiebre or 0,
            "inventario_promedio_tm": replica.inventario_promedio_tm or 0,
            "autonomia_promedio_dias": replica.autonomia_promedio_dias or 0,
            "probabilidad_quiebre_stock_pct": replica.probabilidad_quiebre_stock_pct or 0,
            "demanda_insatisfecha_tm": replica.demanda_insatisfecha_tm or 0,
            "disrupciones_totales": replica.disrupciones_totales or 0,
        })

    return {
        "experiment_id": experiment_id,
        "experiment_nombre": experiment.nombre,
        "num_replicas": len(datos),
        "replicas": datos
    }


@router.get(
    "/experiments/{experiment_id}/series-temporales",
    summary="Obtener series temporales agregadas del experimento",
    description="""
    Genera series temporales agregadas para un experimento Monte Carlo.

    Ejecuta un subconjunto de réplicas (por defecto 50) con las mismas configuraciones
    y calcula estadísticas por día:
    - Media, desviación estándar
    - Percentiles 5, 25, 50, 75, 95

    Ideal para visualizar bandas de confianza en gráficos de series temporales
    en la tesis.
    """,
)
def get_experiment_series_temporales(
    *,
    db: Session = Depends(get_db),
    experiment_id: int,
    num_muestras: int = 50,
):
    """Genera series temporales agregadas para visualización.

    Args:
        db: Sesión de base de datos
        experiment_id: ID del experimento
        num_muestras: Número de réplicas a ejecutar para generar series (default: 50)

    Returns:
        Series temporales agregadas con estadísticas por día
    """
    import numpy as np
    from bll.config import SimulationConfig
    from bll.simulation import run_simulation

    experiment = db.query(MonteCarloExperiment).filter(
        MonteCarloExperiment.id == experiment_id
    ).first()

    if not experiment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Experimento {experiment_id} no encontrado",
        )

    # Obtener configuración
    config = db.query(Configuracion).filter(
        Configuracion.id == experiment.configuracion_id
    ).first()

    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuración no encontrada",
        )

    params = config.parametros
    cap = params.get("capacidad_hub_tm", 431.0)
    inv_pct = params.get("inventario_inicial_pct", 60.0)
    seed_base = params.get("semilla_aleatoria") or 42
    sim_days = params.get("duracion_simulacion_dias", 365)

    # Ejecutar múltiples réplicas y recolectar series temporales
    all_series = []

    for i in range(num_muestras):
        sim_config = SimulationConfig(
            capacity_tm=cap,
            reorder_point_tm=params.get("punto_reorden_tm", cap * 0.7),
            order_quantity_tm=params.get("cantidad_pedido_tm", cap * 0.5),
            initial_inventory_tm=cap * inv_pct / 100.0,
            base_daily_demand_tm=params.get("demanda_base_diaria_tm", 52.5),
            nominal_lead_time_days=params.get("lead_time_nominal_dias", 6.0),
            disruption_min_days=params.get("duracion_disrupcion_min_dias", 3.0),
            disruption_mode_days=params.get("duracion_disrupcion_mode_dias", 7.0),
            disruption_max_days=params.get("duracion_disrupcion_max_dias", 21.0),
            annual_disruption_rate=params.get("tasa_disrupciones_anual", 4.0),
            use_seasonality=params.get("usar_estacionalidad", True),
            simulation_days=sim_days,
            seed=seed_base * 100000 + i + 1000000,  # Semillas diferentes
        )

        result = run_simulation(sim_config)
        all_series.append(result["time_series"])

    # Agregar por día
    series_agregadas = []

    for day in range(sim_days):
        day_data = {
            "inventario": [],
            "demanda": [],
            "demanda_satisfecha": [],
            "dias_autonomia": [],
            "quiebre_stock": [],
            "ruta_bloqueada": [],
        }

        for series in all_series:
            if day < len(series):
                row = series[day]
                day_data["inventario"].append(row["inventory"])
                day_data["demanda"].append(row["demand"])
                day_data["demanda_satisfecha"].append(row["satisfied_demand"])
                day_data["dias_autonomia"].append(row["autonomy_days"])
                day_data["quiebre_stock"].append(1 if row["stockout"] else 0)
                day_data["ruta_bloqueada"].append(1 if row["route_blocked"] else 0)

        # Calcular estadísticas
        inv = np.array(day_data["inventario"])
        dem = np.array(day_data["demanda"])
        dem_sat = np.array(day_data["demanda_satisfecha"])
        aut = np.array(day_data["dias_autonomia"])

        series_agregadas.append({
            "dia": day,
            # Inventario
            "inventario_mean": float(np.mean(inv)),
            "inventario_std": float(np.std(inv)),
            "inventario_p5": float(np.percentile(inv, 5)),
            "inventario_p25": float(np.percentile(inv, 25)),
            "inventario_p50": float(np.percentile(inv, 50)),
            "inventario_p75": float(np.percentile(inv, 75)),
            "inventario_p95": float(np.percentile(inv, 95)),
            # Demanda
            "demanda_mean": float(np.mean(dem)),
            "demanda_satisfecha_mean": float(np.mean(dem_sat)),
            # Autonomía
            "dias_autonomia_mean": float(np.mean(aut)),
            "dias_autonomia_p5": float(np.percentile(aut, 5)),
            "dias_autonomia_p95": float(np.percentile(aut, 95)),
            # Probabilidades
            "prob_quiebre_stock": float(np.mean(day_data["quiebre_stock"])) * 100,
            "prob_ruta_bloqueada": float(np.mean(day_data["ruta_bloqueada"])) * 100,
        })

    return {
        "experiment_id": experiment_id,
        "experiment_nombre": experiment.nombre,
        "num_muestras": num_muestras,
        "dias_simulados": sim_days,
        "series_temporales": series_agregadas,
    }
