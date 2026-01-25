from __future__ import annotations
import math
from typing import Any

import simpy
import numpy as np

from .config import SimulationConfig, SAFETY_MARGIN, MAX_CONCURRENT_ORDERS
from .entities import Hub, Route, OrderInTransit, DailyMetrics


class GLPSimulation:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.rng = np.random.default_rng(config.seed)
        self.env = simpy.Environment()
        self.hub = Hub(self.env, config)
        self.route = Route(self.env, config, self.rng)
        self.orders_in_transit: list[OrderInTransit] = []
        self.daily_metrics: list[DailyMetrics] = []
        self.total_demand_tm = 0.0
        self.satisfied_demand_tm = 0.0

    def run(self):
        self.env.process(self._demand_process())
        self.env.process(self._replenishment_process())
        self.env.process(self._disruption_process())
        self.env.run(until=self.config.simulation_days)

    def _calculate_demand(self, day: int) -> float:
        base = self.config.base_daily_demand_tm
        if self.config.use_seasonality:
            phase = 2 * math.pi * (day - self.config.peak_winter_day) / 365.0
            seasonal = 1.0 + self.config.seasonal_amplitude * math.sin(phase)
        else:
            seasonal = 1.0
        noise = self.rng.normal(1.0, self.config.demand_variability)
        return max(0.0, base * seasonal * noise)

    def _inventory_in_transit(self) -> float:
        return sum(o.quantity_tm for o in self.orders_in_transit)

    def _position_inventory(self) -> float:
        return self.hub.inventory.level + self._inventory_in_transit()

    def _dynamic_order_quantity(self) -> float:
        effective_lt = self.route.calculate_lead_time()
        demand_during_lt = self.config.base_daily_demand_tm * effective_lt
        q = demand_during_lt * (1.0 + SAFETY_MARGIN)
        available_capacity = self.config.capacity_tm - self.hub.inventory.level
        return max(0.0, min(q, available_capacity))

    def _demand_process(self):
        day = 0
        while True:
            demand = self._calculate_demand(day)
            dispatched = self.hub.dispatch(demand)
            self.total_demand_tm += demand
            self.satisfied_demand_tm += dispatched

            inv = self.hub.inventory.level
            autonomy = inv / demand if demand > 0 else 0.0

            is_blocked = self.route._blocked and self.env.now < self.route._unblock_time

            self.daily_metrics.append(DailyMetrics(
                day=day,
                inventory_tm=inv,
                demand_tm=demand,
                satisfied_demand_tm=dispatched,
                supply_received_tm=0.0,
                stockout=(dispatched < demand),
                route_blocked=is_blocked,
                pending_orders=len(self.orders_in_transit),
                autonomy_days=autonomy
            ))
            yield self.env.timeout(1.0)
            day += 1

    def _replenishment_process(self):
        while True:
            position = self._position_inventory()
            can_order = (
                position <= self.config.reorder_point_tm and
                len(self.orders_in_transit) < MAX_CONCURRENT_ORDERS and
                self.route.is_operational()
            )
            if can_order:
                quantity = self._dynamic_order_quantity()
                if quantity > 0:
                    lt = self.route.calculate_lead_time()
                    order = OrderInTransit(quantity, lt, self.env.now)
                    self.orders_in_transit.append(order)
                    self.env.process(self._supply_arrival(order))
            yield self.env.timeout(1.0)

    def _supply_arrival(self, order: OrderInTransit):
        yield self.env.timeout(order.lead_time_days)
        yield self.hub.receive_supply(order.quantity_tm)
        if self.daily_metrics:
            self.daily_metrics[-1].supply_received_tm += order.quantity_tm
        if order in self.orders_in_transit:
            self.orders_in_transit.remove(order)

    def _disruption_process(self):
        if self.config.disruption_max_days <= 0 or self.config.annual_disruption_rate <= 0:
            return

        lambda_days = self.config.annual_disruption_rate / 365.0
        while True:
            time_to_next = self.rng.exponential(1.0 / lambda_days)
            yield self.env.timeout(time_to_next)

            if self.config.disruption_min_days == self.config.disruption_mode_days == self.config.disruption_max_days:
                duration = self.config.disruption_max_days
            else:
                duration = self.rng.triangular(
                    self.config.disruption_min_days,
                    self.config.disruption_mode_days,
                    self.config.disruption_max_days
                )
            self.route.block(duration)

    def calculate_kpis(self) -> dict[str, Any]:
        if not self.daily_metrics:
            return {}

        inventories = [m.inventory_tm for m in self.daily_metrics]
        autonomies = [m.autonomy_days for m in self.daily_metrics]
        demands = [m.demand_tm for m in self.daily_metrics]
        stockout_days = sum(1 for m in self.daily_metrics if m.stockout)
        total_days = len(self.daily_metrics)

        service_level = (self.satisfied_demand_tm / self.total_demand_tm * 100.0) if self.total_demand_tm > 0 else 0.0
        stockout_prob = (stockout_days / total_days * 100.0) if total_days > 0 else 0.0
        blocked_pct = (self.route.total_blocked_days / self.config.simulation_days * 100.0)

        return {
            "service_level_pct": round(service_level, 4),
            "stockout_probability_pct": round(stockout_prob, 4),
            "stockout_days": stockout_days,
            "avg_inventory_tm": round(float(np.mean(inventories)), 2),
            "min_inventory_tm": round(float(np.min(inventories)), 2),
            "max_inventory_tm": round(float(np.max(inventories)), 2),
            "std_inventory_tm": round(float(np.std(inventories)), 2),
            "final_inventory_tm": round(self.hub.inventory.level, 2),
            "initial_inventory_tm": round(self.config.initial_inventory_tm, 2),
            "avg_autonomy_days": round(float(np.mean(autonomies)), 2),
            "min_autonomy_days": round(float(np.min(autonomies)), 2),
            "total_demand_tm": round(self.total_demand_tm, 2),
            "satisfied_demand_tm": round(self.satisfied_demand_tm, 2),
            "unsatisfied_demand_tm": round(self.total_demand_tm - self.satisfied_demand_tm, 2),
            "avg_daily_demand_tm": round(float(np.mean(demands)), 2),
            "max_daily_demand_tm": round(float(np.max(demands)), 2),
            "min_daily_demand_tm": round(float(np.min(demands)), 2),
            "total_received_tm": round(self.hub.total_received_tm, 2),
            "total_dispatched_tm": round(self.hub.total_dispatched_tm, 2),
            "total_disruptions": self.route.total_disruptions,
            "total_blocked_days": round(self.route.total_blocked_days, 2),
            "blocked_time_pct": round(blocked_pct, 2),
            "simulated_days": total_days,
        }


def run_simulation(config: SimulationConfig) -> dict[str, Any]:
    sim = GLPSimulation(config)
    sim.run()
    kpis = sim.calculate_kpis()
    kpis["time_series"] = [
        {
            "day": m.day,
            "inventory": m.inventory_tm,
            "demand": m.demand_tm,
            "satisfied_demand": m.satisfied_demand_tm,
            "supply_received": m.supply_received_tm,
            "stockout": m.stockout,
            "route_blocked": m.route_blocked,
            "pending_orders": m.pending_orders,
            "autonomy_days": m.autonomy_days,
        }
        for m in sim.daily_metrics
    ]
    return kpis
