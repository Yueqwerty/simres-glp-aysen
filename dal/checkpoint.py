from __future__ import annotations
import json
from pathlib import Path
from typing import Any


class CheckpointManager:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.data_path = self.path / "checkpoint.json"
        self.results_path = self.path / "results"

    def exists(self) -> bool:
        return self.data_path.exists()

    def load(self) -> tuple[int, list[dict]]:
        if not self.exists():
            return 0, []

        with open(self.data_path, "r") as f:
            data = json.load(f)

        config_id = data.get("last_config_id", 0)
        results = []

        for batch_file in sorted(self.results_path.glob("batch_*.json")):
            with open(batch_file, "r") as f:
                batch = json.load(f)
                results.extend(batch)

        return config_id, results

    def save(self, config_id: int, batch: list[dict], batch_num: int):
        self.path.mkdir(parents=True, exist_ok=True)
        self.results_path.mkdir(exist_ok=True)

        with open(self.data_path, "w") as f:
            json.dump({"last_config_id": config_id}, f)

        batch_file = self.results_path / f"batch_{batch_num:06d}.json"
        with open(batch_file, "w") as f:
            json.dump(batch, f)

    def clear(self):
        if self.results_path.exists():
            for f in self.results_path.glob("batch_*.json"):
                f.unlink()
            self.results_path.rmdir()
        if self.data_path.exists():
            self.data_path.unlink()
        if self.path.exists() and not any(self.path.iterdir()):
            self.path.rmdir()
