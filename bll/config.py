from __future__ import annotations
from dataclasses import dataclass

SAFETY_MARGIN = 0.20
MAX_CONCURRENT_ORDERS = 3
CAPACITY_STATUS_QUO = 431.0
CAPACITY_PROPOSED = 681.0
BASE_DAILY_DEMAND = 52.5
NOMINAL_LEAD_TIME = 6.0


@dataclass
class SimulationConfig:
    capacity_tm: float = CAPACITY_STATUS_QUO
    reorder_point_tm: float = 394.0
    order_quantity_tm: float = 230.0
    initial_inventory_tm: float = 258.6
    base_daily_demand_tm: float = BASE_DAILY_DEMAND
    demand_variability: float = 0.15
    seasonal_amplitude: float = 0.30
    peak_winter_day: int = 200
    nominal_lead_time_days: float = NOMINAL_LEAD_TIME
    annual_disruption_rate: float = 4.0
    disruption_min_days: float = 3.0
    disruption_mode_days: float = 7.0
    disruption_max_days: float = 21.0
    simulation_days: int = 365
    seed: int = 42
    use_seasonality: bool = True

    def __post_init__(self):
        self._validate()

    def _validate(self):
        assert self.capacity_tm > 0
        assert self.reorder_point_tm < self.capacity_tm
        assert self.order_quantity_tm > 0
        assert self.initial_inventory_tm <= self.capacity_tm
        assert self.base_daily_demand_tm > 0
        assert 0 <= self.demand_variability < 1
        assert 0 <= self.seasonal_amplitude < 1
        assert self.nominal_lead_time_days > 0
        assert self.annual_disruption_rate >= 0
        assert self.disruption_min_days <= self.disruption_mode_days <= self.disruption_max_days
        assert self.simulation_days > 0

    def theoretical_autonomy_days(self) -> float:
        return self.capacity_tm / self.base_daily_demand_tm

    def safety_stock_days(self) -> float:
        demand_during_lt = self.base_daily_demand_tm * self.nominal_lead_time_days
        return (self.reorder_point_tm - demand_during_lt) / self.base_daily_demand_tm


@dataclass
class DisruptionConfig:
    name: str
    min_days: float
    mode_days: float
    max_days: float


DISRUPTION_SHORT = DisruptionConfig("Short", 3.0, 5.0, 7.0)
DISRUPTION_MEDIUM = DisruptionConfig("Medium", 3.0, 7.0, 14.0)
DISRUPTION_LONG = DisruptionConfig("Long", 3.0, 10.5, 21.0)


def create_factorial_configs(
    base_seed: int = 42,
    simulation_days: int = 365
) -> list[tuple[str, SimulationConfig]]:
    capacities = [
        ("SQ", CAPACITY_STATUS_QUO),
        ("P", CAPACITY_PROPOSED),
    ]
    disruptions = [DISRUPTION_SHORT, DISRUPTION_MEDIUM, DISRUPTION_LONG]

    configs = []
    for cap_name, cap_value in capacities:
        for dis in disruptions:
            name = f"{cap_name}_{dis.name}"
            config = SimulationConfig(
                capacity_tm=cap_value,
                reorder_point_tm=cap_value * 0.91,
                order_quantity_tm=cap_value * 0.53,
                initial_inventory_tm=cap_value * 0.60,
                disruption_min_days=dis.min_days,
                disruption_mode_days=dis.mode_days,
                disruption_max_days=dis.max_days,
                simulation_days=simulation_days,
                seed=base_seed,
            )
            configs.append((name, config))

    return configs
