"""Endpoints para Simulaciones."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.resultado import ResultadoResponse
from app.schemas.simulacion import SimulacionRequest, SimulacionResponse
from app.services import simulacion_service

router = APIRouter()


@router.post("/execute", response_model=SimulacionResponse, status_code=status.HTTP_201_CREATED)
async def execute_simulation(
    request: SimulacionRequest,
    db: Session = Depends(get_db),
):
    """Ejecutar simulación única."""
    try:
        simulacion = await simulacion_service.execute_simulation(db, request.configuracion_id)
        return simulacion
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error ejecutando simulación: {str(e)}",
        )


@router.get("/{simulacion_id}", response_model=SimulacionResponse)
def get_simulacion(
    simulacion_id: int,
    db: Session = Depends(get_db),
):
    """Obtener simulación por ID."""
    sim = simulacion_service.get_simulacion(db, simulacion_id)
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulación {simulacion_id} no encontrada",
        )
    # Incluir nombre de configuración
    response = SimulacionResponse.model_validate(sim)
    if sim.configuracion:
        response.configuracion_nombre = sim.configuracion.nombre
    return response


@router.get("/{simulacion_id}/resultados", response_model=ResultadoResponse)
def get_resultados(
    simulacion_id: int,
    db: Session = Depends(get_db),
):
    """Obtener resultados (21 KPIs) de simulación."""
    sim = simulacion_service.get_simulacion(db, simulacion_id)
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulación {simulacion_id} no encontrada",
        )

    if sim.estado != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Simulación en estado '{sim.estado}', no hay resultados disponibles",
        )

    # Construir ResultadoResponse
    return ResultadoResponse(
        simulacion_id=sim.id,
        nivel_servicio_pct=sim.nivel_servicio_pct or 0.0,
        probabilidad_quiebre_stock_pct=sim.probabilidad_quiebre_stock_pct or 0.0,
        dias_con_quiebre=sim.dias_con_quiebre or 0,
        inventario_promedio_tm=sim.inventario_promedio_tm or 0.0,
        inventario_minimo_tm=sim.inventario_minimo_tm or 0.0,
        inventario_maximo_tm=sim.inventario_maximo_tm or 0.0,
        inventario_final_tm=sim.inventario_final_tm or 0.0,
        inventario_inicial_tm=sim.inventario_inicial_tm or 0.0,
        inventario_std_tm=sim.inventario_std_tm or 0.0,
        autonomia_promedio_dias=sim.autonomia_promedio_dias or 0.0,
        autonomia_minima_dias=sim.autonomia_minima_dias or 0.0,
        demanda_total_tm=sim.demanda_total_tm or 0.0,
        demanda_satisfecha_tm=sim.demanda_satisfecha_tm or 0.0,
        demanda_insatisfecha_tm=sim.demanda_insatisfecha_tm or 0.0,
        demanda_promedio_diaria_tm=sim.demanda_promedio_diaria_tm or 0.0,
        demanda_maxima_diaria_tm=sim.demanda_maxima_diaria_tm or 0.0,
        demanda_minima_diaria_tm=sim.demanda_minima_diaria_tm or 0.0,
        total_recibido_tm=sim.total_recibido_tm or 0.0,
        total_despachado_tm=sim.total_despachado_tm or 0.0,
        disrupciones_totales=sim.disrupciones_totales or 0,
        dias_bloqueados_total=sim.dias_bloqueados_total or 0,
        pct_tiempo_bloqueado=sim.pct_tiempo_bloqueado or 0.0,
        dias_simulados=sim.dias_simulados or 0,
    )


@router.get("/{simulacion_id}/series-temporales", response_model=dict)
async def get_series_temporales(
    simulacion_id: int,
    db: Session = Depends(get_db),
):
    """Obtener series temporales de una simulación (re-ejecuta con la misma semilla)."""
    sim = simulacion_service.get_simulacion(db, simulacion_id)
    if not sim:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Simulación {simulacion_id} no encontrada",
        )

    if sim.estado != "completed":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Simulación en estado '{sim.estado}', no hay datos disponibles",
        )

    # Re-ejecutar simulación para obtener series temporales
    try:
        from app.models.configuracion import Configuracion
        config_db = db.query(Configuracion).filter(Configuracion.id == sim.configuracion_id).first()
        if not config_db:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Configuración no encontrada",
            )

        # Re-ejecutar con los mismos parámetros
        resultado = await simulacion_service.ejecutar_modelo(config_db.parametros)

        # Retornar solo las series temporales
        return {
            "simulacion_id": simulacion_id,
            "series_temporales": resultado.get("series_temporales", [])
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error obteniendo series temporales: {str(e)}",
        )


@router.get("/", response_model=list[SimulacionResponse])
def list_simulaciones(
    configuracion_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Listar simulaciones (opcionalmente filtradas por configuración)."""
    sims = simulacion_service.get_simulaciones(
        db,
        configuracion_id=configuracion_id,
        skip=skip,
        limit=limit,
    )
    # Incluir nombre de configuración en cada simulación
    responses = []
    for sim in sims:
        response = SimulacionResponse.model_validate(sim)
        if sim.configuracion:
            response.configuracion_nombre = sim.configuracion.nombre
        responses.append(response)
    return responses
