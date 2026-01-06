"""API v1 main router."""

from fastapi import APIRouter

from app.api.v1 import configuracion, simulacion, montecarlo

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from pl.api import simulation_router, experiment_router

api_router = APIRouter()

api_router.include_router(configuracion.router, prefix="/configuraciones", tags=["configuraciones"])
api_router.include_router(simulacion.router, prefix="/simulaciones", tags=["simulaciones"])
api_router.include_router(montecarlo.router, prefix="/monte-carlo", tags=["monte-carlo"])

api_router.include_router(simulation_router, tags=["sim"])
api_router.include_router(experiment_router, tags=["exp"])
