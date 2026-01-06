from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Any

from bll.config import SimulationConfig, CAPACITY_STATUS_QUO, BASE_DAILY_DEMAND, NOMINAL_LEAD_TIME


class SimulationConfigDTO(BaseModel):
    capacity_tm: float = Field(default=CAPACITY_STATUS_QUO, gt=0)
    reorder_point_tm: float = Field(default=394.0, gt=0)
    order_quantity_tm: float = Field(default=230.0, gt=0)
    initial_inventory_tm: float = Field(default=258.6, ge=0)
    base_daily_demand_tm: float = Field(default=BASE_DAILY_DEMAND, gt=0)
    demand_variability: float = Field(default=0.15, ge=0, lt=1)
    seasonal_amplitude: float = Field(default=0.30, ge=0, lt=1)
    peak_winter_day: int = Field(default=200, ge=1, le=365)
    nominal_lead_time_days: float = Field(default=NOMINAL_LEAD_TIME, gt=0)
    annual_disruption_rate: float = Field(default=4.0, ge=0)
    disruption_min_days: float = Field(default=3.0, ge=0)
    disruption_mode_days: float = Field(default=7.0, ge=0)
    disruption_max_days: float = Field(default=21.0, ge=0)
    simulation_days: int = Field(default=365, gt=0)
    seed: int = Field(default=42)
    use_seasonality: bool = Field(default=True)

    def to_bll(self) -> SimulationConfig:
        return SimulationConfig(**self.model_dump())

    @classmethod
    def from_bll(cls, config: SimulationConfig) -> SimulationConfigDTO:
        return cls(
            capacity_tm=config.capacity_tm,
            reorder_point_tm=config.reorder_point_tm,
            order_quantity_tm=config.order_quantity_tm,
            initial_inventory_tm=config.initial_inventory_tm,
            base_daily_demand_tm=config.base_daily_demand_tm,
            demand_variability=config.demand_variability,
            seasonal_amplitude=config.seasonal_amplitude,
            peak_winter_day=config.peak_winter_day,
            nominal_lead_time_days=config.nominal_lead_time_days,
            annual_disruption_rate=config.annual_disruption_rate,
            disruption_min_days=config.disruption_min_days,
            disruption_mode_days=config.disruption_mode_days,
            disruption_max_days=config.disruption_max_days,
            simulation_days=config.simulation_days,
            seed=config.seed,
            use_seasonality=config.use_seasonality,
        )


class TimeSeriesPointDTO(BaseModel):
    day: int
    inventory: float
    demand: float
    satisfied_demand: float
    supply_received: float
    stockout: bool
    route_blocked: bool
    pending_orders: int
    autonomy_days: float


class SimulationResultDTO(BaseModel):
    service_level_pct: float
    stockout_probability_pct: float
    stockout_days: int
    avg_inventory_tm: float
    min_inventory_tm: float
    max_inventory_tm: float
    std_inventory_tm: float
    final_inventory_tm: float
    initial_inventory_tm: float
    avg_autonomy_days: float
    min_autonomy_days: float
    total_demand_tm: float
    satisfied_demand_tm: float
    unsatisfied_demand_tm: float
    avg_daily_demand_tm: float
    max_daily_demand_tm: float
    min_daily_demand_tm: float
    total_received_tm: float
    total_dispatched_tm: float
    total_disruptions: int
    total_blocked_days: float
    blocked_time_pct: float
    simulated_days: int
    time_series: list[TimeSeriesPointDTO] = []

    @classmethod
    def from_kpis(cls, kpis: dict[str, Any]) -> SimulationResultDTO:
        ts = kpis.pop("time_series", [])
        return cls(
            **kpis,
            time_series=[TimeSeriesPointDTO(**p) for p in ts]
        )


class ExperimentConfigDTO(BaseModel):
    num_replicas: int = Field(default=1000, gt=0)
    max_workers: int | None = Field(default=None)
    base_seed: int = Field(default=42)
    use_factorial: bool = Field(default=True)
    configs: list[SimulationConfigDTO] | None = Field(default=None)


class ExperimentProgressDTO(BaseModel):
    experiment_id: int
    status: str
    completed: int
    total: int
    progress_pct: float
    elapsed_seconds: float | None = None
    estimated_remaining_seconds: float | None = None


class AnovaResultDTO(BaseModel):
    eta_squared_capacity: float
    eta_squared_disruption: float
    eta_squared_interaction: float
    main_effect_capacity: float
    main_effect_disruption: float
    interaction_effect: float
    r_squared: float
    p_value_capacity: float | None = None
    p_value_disruption: float | None = None
    p_value_interaction: float | None = None
