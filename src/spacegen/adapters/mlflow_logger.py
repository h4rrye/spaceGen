from pathlib import Path
from typing import Any
from ..ports.interfaces import ExperimentLogger


class MLflowLogger(ExperimentLogger):
    def log_params(self, params: dict[str, Any]) -> None:
        import mlflow
        mlflow.log_params(params)

    def log_metrics(self, metrics: dict[str, float]) -> None:
        import mlflow
        mlflow.log_metrics(metrics)

    def log_artifact(self, path: Path) -> None:
        import mlflow
        mlflow.log_artifact(str(path))
