from __future__ import annotations
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, replace
from typing import Callable

import pandas as pd

from .config import SimulationConfig, create_factorial_configs
from .simulation import run_simulation


@dataclass
class ExperimentResult:
    config_name: str
    replica: int
    kpis: dict


def _run_replica(args: tuple[str, SimulationConfig, int]) -> ExperimentResult:
    config_name, config, replica = args
    kpis = run_simulation(config)
    del kpis["time_series"]
    return ExperimentResult(config_name, replica, kpis)


def run_experiment(
    configs: list[tuple[str, SimulationConfig]] | None = None,
    num_replicas: int = 1000,
    max_workers: int | None = None,
    base_seed: int = 42,
    on_progress: Callable[[int, int], None] | None = None,
) -> pd.DataFrame:
    if configs is None:
        configs = create_factorial_configs(base_seed)

    tasks = []
    for config_id, (name, base_config) in enumerate(configs, start=1):
        for replica in range(1, num_replicas + 1):
            seed = base_seed + (config_id - 1) * 1_000_000 + replica
            config = replace(base_config, seed=seed)
            tasks.append((name, config, replica))

    results = []
    completed = 0
    total = len(tasks)

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_run_replica, task): task for task in tasks}
        for future in as_completed(futures):
            result = future.result()
            row = {
                "config_name": result.config_name,
                "replica": result.replica,
                **result.kpis
            }
            results.append(row)
            completed += 1
            if on_progress:
                on_progress(completed, total)

    return pd.DataFrame(results)


def run_experiment_sequential(
    configs: list[tuple[str, SimulationConfig]] | None = None,
    num_replicas: int = 100,
    base_seed: int = 42,
    on_progress: Callable[[int, int], None] | None = None,
) -> pd.DataFrame:
    if configs is None:
        configs = create_factorial_configs(base_seed)

    results = []
    completed = 0
    total = len(configs) * num_replicas

    for config_id, (name, base_config) in enumerate(configs, start=1):
        for replica in range(1, num_replicas + 1):
            seed = base_seed + (config_id - 1) * 1_000_000 + replica
            config = replace(base_config, seed=seed)
            kpis = run_simulation(config)
            del kpis["time_series"]
            row = {"config_name": name, "replica": replica, **kpis}
            results.append(row)
            completed += 1
            if on_progress:
                on_progress(completed, total)

    return pd.DataFrame(results)
