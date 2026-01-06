"""Servicio para Configuraciones."""

from sqlalchemy.orm import Session

from app.models.configuracion import Configuracion
from app.schemas.configuracion import ConfiguracionCreate, ConfiguracionUpdate


def get_configuraciones(db: Session, skip: int = 0, limit: int = 100) -> list[Configuracion]:
    """Obtener lista de configuraciones."""
    return db.query(Configuracion).offset(skip).limit(limit).all()


def get_configuracion(db: Session, configuracion_id: int) -> Configuracion | None:
    """Obtener configuración por ID."""
    return db.query(Configuracion).filter(Configuracion.id == configuracion_id).first()


def get_configuracion_by_nombre(db: Session, nombre: str) -> Configuracion | None:
    """Obtener configuración por nombre."""
    return db.query(Configuracion).filter(Configuracion.nombre == nombre).first()


def create_configuracion(db: Session, config: ConfiguracionCreate) -> Configuracion:
    """Crear nueva configuración."""
    # Convertir ParametrosBase a dict
    parametros_dict = config.model_dump(exclude={"nombre", "descripcion"})

    db_config = Configuracion(
        nombre=config.nombre,
        descripcion=config.descripcion,
        parametros=parametros_dict,
    )
    db.add(db_config)
    db.commit()
    db.refresh(db_config)
    return db_config


def update_configuracion(
    db: Session, configuracion_id: int, config: ConfiguracionUpdate
) -> Configuracion | None:
    """Actualizar configuración existente."""
    db_config = get_configuracion(db, configuracion_id)
    if not db_config:
        return None

    update_data = config.model_dump(exclude_unset=True)

    if "nombre" in update_data:
        db_config.nombre = update_data["nombre"]
    if "descripcion" in update_data:
        db_config.descripcion = update_data["descripcion"]
    if "parametros" in update_data:
        db_config.parametros = update_data["parametros"].model_dump()

    db.commit()
    db.refresh(db_config)
    return db_config


def delete_configuracion(db: Session, configuracion_id: int) -> bool:
    """Eliminar configuración."""
    db_config = get_configuracion(db, configuracion_id)
    if not db_config:
        return False

    db.delete(db_config)
    db.commit()
    return True


def get_defaults() -> dict:
    """Obtener parámetros por defecto."""
    return {
        "capacidad_hub_tm": 431.0,
        "punto_reorden_tm": 394.0,
        "cantidad_pedido_tm": 230.0,
        "inventario_inicial_pct": 60.0,
        "demanda_base_diaria_tm": 52.5,
        "variabilidad_demanda": 0.15,
        "amplitud_estacional": 0.30,
        "dia_pico_invernal": 200,
        "usar_estacionalidad": True,
        "tasa_disrupciones_anual": 4.0,
        "duracion_disrupcion_min_dias": 3.0,
        "duracion_disrupcion_mode_dias": 7.0,
        "duracion_disrupcion_max_dias": 21.0,
        "lead_time_nominal_dias": 6.0,
        "duracion_simulacion_dias": 365,
        "semilla_aleatoria": None,
    }
