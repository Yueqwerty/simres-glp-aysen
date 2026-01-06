"""Endpoints para Configuraciones."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.configuracion import (
    ConfiguracionCreate,
    ConfiguracionRead,
    ConfiguracionUpdate,
)
from app.services import configuracion_service

router = APIRouter()


@router.get("/", response_model=list[ConfiguracionRead])
def list_configuraciones(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    """Listar todas las configuraciones."""
    configs = configuracion_service.get_configuraciones(db, skip=skip, limit=limit)
    return configs


@router.get("/defaults", response_model=dict)
def get_defaults():
    """Obtener parámetros por defecto."""
    return configuracion_service.get_defaults()


@router.get("/{configuracion_id}", response_model=ConfiguracionRead)
def get_configuracion(
    configuracion_id: int,
    db: Session = Depends(get_db),
):
    """Obtener configuración por ID."""
    config = configuracion_service.get_configuracion(db, configuracion_id)
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuración {configuracion_id} no encontrada",
        )
    return config


@router.post("/", response_model=ConfiguracionRead, status_code=status.HTTP_201_CREATED)
def create_configuracion(
    config: ConfiguracionCreate,
    db: Session = Depends(get_db),
):
    """Crear nueva configuración."""
    # Validar nombre único
    existing = configuracion_service.get_configuracion_by_nombre(db, config.nombre)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ya existe una configuración con el nombre '{config.nombre}'",
        )

    return configuracion_service.create_configuracion(db, config)


@router.put("/{configuracion_id}", response_model=ConfiguracionRead)
def update_configuracion(
    configuracion_id: int,
    config: ConfiguracionUpdate,
    db: Session = Depends(get_db),
):
    """Actualizar configuración existente."""
    updated = configuracion_service.update_configuracion(db, configuracion_id, config)
    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuración {configuracion_id} no encontrada",
        )
    return updated


@router.delete("/{configuracion_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_configuracion(
    configuracion_id: int,
    db: Session = Depends(get_db),
):
    """Eliminar configuración."""
    deleted = configuracion_service.delete_configuracion(db, configuracion_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuración {configuracion_id} no encontrada",
        )
