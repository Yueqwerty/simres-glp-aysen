from __future__ import annotations
import json
from pathlib import Path
from typing import Any

import pandas as pd


def export_csv(df: pd.DataFrame, path: Path, index: bool = False):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=index)


def export_json(data: dict[str, Any], path: Path, indent: int = 2):
    Path(path).parent.mkdir(parents=True, exist_ok=True)

    def convert(obj):
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        if hasattr(obj, "tolist"):
            return obj.tolist()
        if hasattr(obj, "__dict__"):
            return {k: convert(v) for k, v in obj.__dict__.items()}
        return obj

    with open(path, "w") as f:
        json.dump(convert(data), f, indent=indent, default=str)


def generate_latex_table(
    df: pd.DataFrame,
    caption: str = "Results",
    label: str = "tab:results"
) -> str:
    latex = df.to_latex(index=True, float_format="%.4f", escape=False)

    full = f"""\\begin{{table}}[htbp]
\\centering
\\caption{{{caption}}}
\\label{{{label}}}
{latex}
\\end{{table}}"""

    return full


def export_latex(df: pd.DataFrame, path: Path, caption: str = "Results", label: str = "tab:results"):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    latex = generate_latex_table(df, caption, label)
    with open(path, "w") as f:
        f.write(latex)
