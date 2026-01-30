"""Servicio para Simulaciones."""

from sqlalchemy.orm import Session, joinedload

from app.core.simulation_runner import run_simulation_async
from app.models.configuracion import Configuracion
from app.models.simulacion import Simulacion


async def execute_simulation(db: Session, configuracion_id: int) -> Simulacion:
    """
    Ejecutar simulación para una configuración.

    Args:
        db: Sesión de base de datos
        configuracion_id: ID de la configuración

    Returns:
        Simulación con resultados

    Raises:
        ValueError: Si la configuración no existe
        Exception: Si la simulación falla
    """
    # Obtener configuración
    config = db.query(Configuracion).filter(Configuracion.id == configuracion_id).first()
    if not config:
        raise ValueError(f"Configuración {configuracion_id} no encontrada")

    # Crear registro de simulación
    db_sim = Simulacion(
        configuracion_id=configuracion_id,
        estado="running",
    )
    db.add(db_sim)
    db.commit()
    db.refresh(db_sim)

    try:
        # Ejecutar simulación
        resultado = await run_simulation_async(config.parametros)

        # Actualizar con resultados
        db_sim.estado = "completed"
        db_sim.duracion_segundos = resultado.pop("_duracion_segundos")

        # Asignar KPIs
        for key, value in resultado.items():
            if hasattr(db_sim, key):
                setattr(db_sim, key, value)

        db.commit()
        db.refresh(db_sim)

    except Exception as e:
        db_sim.estado = "failed"
        db_sim.error_mensaje = str(e)
        db.commit()
        db.refresh(db_sim)
        raise

    return db_sim


def get_simulacion(db: Session, simulacion_id: int) -> Simulacion | None:
    """Obtener simulación por ID."""
    return (
        db.query(Simulacion)
        .options(joinedload(Simulacion.configuracion))
        .filter(Simulacion.id == simulacion_id)
        .first()
    )


def get_simulaciones(
    db: Session,
    configuracion_id: int | None = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Simulacion]:
    """Obtener lista de simulaciones."""
    query = db.query(Simulacion).options(joinedload(Simulacion.configuracion))

    if configuracion_id:
        query = query.filter(Simulacion.configuracion_id == configuracion_id)

    return query.order_by(Simulacion.ejecutada_en.desc()).offset(skip).limit(limit).all()


async def ejecutar_modelo(params: dict):
    """Ejecutar el modelo de simulación y retornar resultados con series temporales."""
    return await run_simulation_async(params)
