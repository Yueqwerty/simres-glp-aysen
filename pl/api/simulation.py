from fastapi import APIRouter, HTTPException
from bll.simulation import run_simulation
from pl.dto.schemas import SimulationConfigDTO, SimulationResultDTO

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.post("/run", response_model=SimulationResultDTO)
async def run(config: SimulationConfigDTO) -> SimulationResultDTO:
    try:
        bll_config = config.to_bll()
        kpis = run_simulation(bll_config)
        return SimulationResultDTO.from_kpis(kpis)
    except AssertionError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/run-quick", response_model=SimulationResultDTO)
async def run_quick(
    capacity_tm: float = 431.0,
    disruption_max_days: float = 21.0,
    seed: int = 42
) -> SimulationResultDTO:
    config = SimulationConfigDTO(
        capacity_tm=capacity_tm,
        reorder_point_tm=capacity_tm * 0.91,
        order_quantity_tm=capacity_tm * 0.53,
        initial_inventory_tm=capacity_tm * 0.60,
        disruption_max_days=disruption_max_days,
        seed=seed
    )
    return await run(config)
