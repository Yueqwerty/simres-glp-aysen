from __future__ import annotations
import asyncio
from concurrent.futures import ProcessPoolExecutor
from typing import Any
import time

from fastapi import APIRouter, HTTPException, BackgroundTasks
import pandas as pd

from bll.experiment import run_experiment_sequential
from bll.statistics import anova_two_way, confidence_intervals, descriptive_statistics, parse_config_name
from bll.config import create_factorial_configs
from pl.dto.schemas import ExperimentConfigDTO, ExperimentProgressDTO, AnovaResultDTO

router = APIRouter(prefix="/experiment", tags=["experiment"])

_experiments: dict[int, dict[str, Any]] = {}
_experiment_counter = 0


def _run_experiment_task(experiment_id: int, config: ExperimentConfigDTO):
    global _experiments
    _experiments[experiment_id]["status"] = "running"
    _experiments[experiment_id]["start_time"] = time.time()

    try:
        def on_progress(completed: int, total: int):
            _experiments[experiment_id]["completed"] = completed
            _experiments[experiment_id]["total"] = total

        df = run_experiment_sequential(
            num_replicas=config.num_replicas,
            base_seed=config.base_seed,
            on_progress=on_progress
        )

        _experiments[experiment_id]["results"] = df
        _experiments[experiment_id]["status"] = "completed"
        _experiments[experiment_id]["end_time"] = time.time()

    except Exception as e:
        _experiments[experiment_id]["status"] = "failed"
        _experiments[experiment_id]["error"] = str(e)


@router.post("/start")
async def start_experiment(
    config: ExperimentConfigDTO,
    background_tasks: BackgroundTasks
) -> dict[str, Any]:
    global _experiment_counter
    _experiment_counter += 1
    experiment_id = _experiment_counter

    factorial_configs = create_factorial_configs(config.base_seed)
    total = len(factorial_configs) * config.num_replicas

    _experiments[experiment_id] = {
        "id": experiment_id,
        "config": config,
        "status": "pending",
        "completed": 0,
        "total": total,
        "results": None,
        "start_time": None,
        "end_time": None,
        "error": None,
    }

    background_tasks.add_task(_run_experiment_task, experiment_id, config)

    return {"experiment_id": experiment_id, "total_simulations": total}


@router.get("/{experiment_id}/progress", response_model=ExperimentProgressDTO)
async def get_progress(experiment_id: int) -> ExperimentProgressDTO:
    if experiment_id not in _experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")

    exp = _experiments[experiment_id]
    progress_pct = (exp["completed"] / exp["total"] * 100) if exp["total"] > 0 else 0

    elapsed = None
    remaining = None
    if exp["start_time"]:
        elapsed = time.time() - exp["start_time"]
        if exp["completed"] > 0 and exp["status"] == "running":
            rate = exp["completed"] / elapsed
            remaining_count = exp["total"] - exp["completed"]
            remaining = remaining_count / rate if rate > 0 else None

    return ExperimentProgressDTO(
        experiment_id=experiment_id,
        status=exp["status"],
        completed=exp["completed"],
        total=exp["total"],
        progress_pct=round(progress_pct, 2),
        elapsed_seconds=round(elapsed, 2) if elapsed else None,
        estimated_remaining_seconds=round(remaining, 2) if remaining else None,
    )


@router.get("/{experiment_id}/results")
async def get_results(experiment_id: int) -> dict[str, Any]:
    if experiment_id not in _experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")

    exp = _experiments[experiment_id]
    if exp["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Experiment status: {exp['status']}")

    df: pd.DataFrame = exp["results"]
    return {
        "experiment_id": experiment_id,
        "total_simulations": len(df),
        "summary": df.groupby("config_name")["service_level_pct"].agg(["mean", "std", "min", "max"]).to_dict(),
    }


@router.get("/{experiment_id}/anova", response_model=AnovaResultDTO)
async def get_anova(experiment_id: int) -> AnovaResultDTO:
    if experiment_id not in _experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")

    exp = _experiments[experiment_id]
    if exp["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Experiment status: {exp['status']}")

    df = parse_config_name(exp["results"])
    result = anova_two_way(df)

    p_cap = result.table.loc["C(capacity)", "PR(>F)"] if "C(capacity)" in result.table.index else None
    p_dis = result.table.loc["C(disruption)", "PR(>F)"] if "C(disruption)" in result.table.index else None
    p_int = result.table.loc["C(capacity):C(disruption)", "PR(>F)"] if "C(capacity):C(disruption)" in result.table.index else None

    return AnovaResultDTO(
        eta_squared_capacity=round(result.eta_squared["capacity"], 6),
        eta_squared_disruption=round(result.eta_squared["disruption"], 6),
        eta_squared_interaction=round(result.eta_squared["interaction"], 6),
        main_effect_capacity=round(result.main_effects["capacity"], 4),
        main_effect_disruption=round(result.main_effects["disruption"], 4),
        interaction_effect=round(result.interaction_effect, 4),
        r_squared=round(result.r_squared, 4),
        p_value_capacity=round(p_cap, 6) if p_cap else None,
        p_value_disruption=round(p_dis, 6) if p_dis else None,
        p_value_interaction=round(p_int, 6) if p_int else None,
    )


@router.get("/{experiment_id}/confidence-intervals")
async def get_confidence_intervals(experiment_id: int, alpha: float = 0.05) -> list[dict]:
    if experiment_id not in _experiments:
        raise HTTPException(status_code=404, detail="Experiment not found")

    exp = _experiments[experiment_id]
    if exp["status"] != "completed":
        raise HTTPException(status_code=400, detail=f"Experiment status: {exp['status']}")

    ci_df = confidence_intervals(exp["results"], alpha=alpha)
    return ci_df.to_dict(orient="records")
