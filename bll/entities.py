from __future__ import annotations
from dataclasses import dataclass
from typing import TYPE_CHECKING

import simpy
import numpy as np

if TYPE_CHECKING:
    from .config import SimulationConfig


@dataclass
class OrderInTransit:
    quantity_tm: float
    lead_time_days: float
    creation_day: float


@dataclass
class DailyMetrics:
    day: int
    inventory_tm: float
    demand_tm: float
    satisfied_demand_tm: float
    supply_received_tm: float
    stockout: bool
    route_blocked: bool
    pending_orders: int
    autonomy_days: float


class Hub:
    def __init__(self, env: simpy.Environment, config: SimulationConfig):
        self.env = env
        self.config = config
        self.inventory = simpy.Container(
            env,
            capacity=config.capacity_tm,
            init=config.initial_inventory_tm
        )
        self.total_received_tm = 0.0
        self.total_dispatched_tm = 0.0
        self.stockout_count = 0

    def receive_supply(self, quantity_tm: float) -> simpy.Event:
        self.total_received_tm += quantity_tm
        return self.inventory.put(quantity_tm)

    def dispatch(self, demand_tm: float) -> float:
        available = self.inventory.level
        if available >= demand_tm:
            self.inventory.get(demand_tm)
            self.total_dispatched_tm += demand_tm
            return demand_tm

        if available > 0:
            self.inventory.get(available)
            self.total_dispatched_tm += available
        self.stockout_count += 1
        return available


class Route:
    def __init__(
        self,
        env: simpy.Environment,
        config: SimulationConfig,
        rng: np.random.Generator
    ):
        self.env = env
        self.config = config
        self.rng = rng
        self._blocked = False
        self._unblock_time = 0.0
        self.total_disruptions = 0
        self.total_blocked_days = 0.0

    def is_operational(self) -> bool:
        self._update_state()
        return not self._blocked

    def _update_state(self):
        if self._blocked and self.env.now >= self._unblock_time:
            self._blocked = False

    def block(self, duration_days: float):
        self._blocked = True
        self._unblock_time = self.env.now + duration_days
        self.total_disruptions += 1
        self.total_blocked_days += duration_days

    def calculate_lead_time(self) -> float:
        base_lt = self.config.nominal_lead_time_days
        if self._blocked:
            remaining = max(0, self._unblock_time - self.env.now)
            return base_lt + remaining
        return base_lt
