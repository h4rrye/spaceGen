from abc import ABC, abstractmethod
import polars as pl
from pathlib import Path
from typing import Any

class ExpressionReader(ABC):
    """Reads expression data from a medallion layer."""
    @abstractmethod
    def read(self, dataset: str, layer: str) -> pl.DataFrame: ...

class DataWriter(ABC):
    """Writes processed data to a medallion layer."""
    @abstractmethod
    def write(self, df: pl.DataFrame, dataset: str, layer: str, version: str | None = None) -> Path: ...

class ExperimentLogger(ABC):
    """Logs ML experiment parameters, metrics, and artifacts."""
    @abstractmethod
    def log_params(self, params: dict[str, Any]) -> None: ...

    @abstractmethod
    def log_metrics(self, metrics: dict[str, float]) -> None: ...

    @abstractmethod
    def log_artifact(self, path: Path) -> None: ...
