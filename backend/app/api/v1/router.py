"""API v1 main router."""

from fastapi import APIRouter

from app.api.v1 import configuracion, simulacion, montecarlo

api_router = APIRouter()

api_router.include_router(configuracion.router, prefix="/configuraciones", tags=["configuraciones"])
api_router.include_router(simulacion.router, prefix="/simulaciones", tags=["simulaciones"])
api_router.include_router(montecarlo.router, prefix="/monte-carlo", tags=["monte-carlo"])
