from __future__ import annotations
from dataclasses import dataclass
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

try:
    import statsmodels.api as sm
    from statsmodels.formula.api import ols
    from statsmodels.stats.multicomp import pairwise_tukeyhsd
    HAS_STATSMODELS = True
except ImportError:
    HAS_STATSMODELS = False


@dataclass
class AnovaResult:
    table: pd.DataFrame
    eta_squared: dict[str, float]
    main_effects: dict[str, float]
    interaction_effect: float
    r_squared: float
    tukey_capacity: pd.DataFrame | None
    tukey_disruption: pd.DataFrame | None


def anova_two_way(
    df: pd.DataFrame,
    response: str = "service_level_pct",
    factor1: str = "capacity",
    factor2: str = "disruption"
) -> AnovaResult:
    if not HAS_STATSMODELS:
        raise ImportError("statsmodels required for ANOVA")

    formula = f"{response} ~ C({factor1}) + C({factor2}) + C({factor1}):C({factor2})"
    model = ols(formula, data=df).fit()
    anova_table = sm.stats.anova_lm(model, typ=2)

    ss_total = anova_table["sum_sq"].sum()
    eta_squared = {
        factor1: anova_table.loc[f"C({factor1})", "sum_sq"] / ss_total,
        factor2: anova_table.loc[f"C({factor2})", "sum_sq"] / ss_total,
        "interaction": anova_table.loc[f"C({factor1}):C({factor2})", "sum_sq"] / ss_total,
    }

    main_effects = {}
    for factor in [factor1, factor2]:
        means = df.groupby(factor)[response].mean()
        main_effects[factor] = means.max() - means.min()

    interaction_means = df.groupby([factor1, factor2])[response].mean()
    interaction_effect = interaction_means.std()

    tukey1 = pairwise_tukeyhsd(df[response], df[factor1])
    tukey2 = pairwise_tukeyhsd(df[response], df[factor2])

    return AnovaResult(
        table=anova_table,
        eta_squared=eta_squared,
        main_effects=main_effects,
        interaction_effect=interaction_effect,
        r_squared=model.rsquared_adj,
        tukey_capacity=pd.DataFrame(data=tukey1._results_table.data[1:], columns=tukey1._results_table.data[0]),
        tukey_disruption=pd.DataFrame(data=tukey2._results_table.data[1:], columns=tukey2._results_table.data[0]),
    )


def confidence_intervals(
    df: pd.DataFrame,
    group_col: str = "config_name",
    value_col: str = "service_level_pct",
    alpha: float = 0.05
) -> pd.DataFrame:
    results = []
    for name, group in df.groupby(group_col):
        values = group[value_col].values
        n = len(values)
        mean = np.mean(values)
        std = np.std(values, ddof=1)
        se = std / np.sqrt(n)
        t_crit = stats.t.ppf(1 - alpha / 2, n - 1)
        margin = t_crit * se

        results.append({
            "config": name,
            "n": n,
            "mean": round(mean, 4),
            "std": round(std, 4),
            "se": round(se, 4),
            "ci_lower": round(mean - margin, 4),
            "ci_upper": round(mean + margin, 4),
            "margin": round(margin, 4),
        })

    return pd.DataFrame(results)


def descriptive_statistics(
    df: pd.DataFrame,
    group_col: str = "config_name",
    metrics: list[str] | None = None
) -> pd.DataFrame:
    if metrics is None:
        metrics = [
            "service_level_pct",
            "stockout_probability_pct",
            "avg_autonomy_days",
            "avg_inventory_tm",
        ]

    agg_funcs = ["count", "mean", "std", "min", "max"]
    stats_df = df.groupby(group_col)[metrics].agg(agg_funcs)
    stats_df.columns = ["_".join(col).strip() for col in stats_df.columns.values]

    return stats_df.round(4)


def parse_config_name(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["capacity"] = df["config_name"].apply(
        lambda x: "StatusQuo" if x.startswith("SQ") else "Proposed"
    )
    df["disruption"] = df["config_name"].apply(
        lambda x: x.split("_")[1] if "_" in x else "Unknown"
    )
    return df
