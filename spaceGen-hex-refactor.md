# spaceGen — Hexagonal Architecture Refactor

## Context
Restructure `src/spacegen/` from flat module layout into hexagonal (ports and adapters) architecture. The current files are `config.py`, `features.py`, `io.py`, `models.py`, `__init__.py`. Preserve any existing logic inside these files — move it into the correct layer, don't delete it. For any new empty directories, add a `.gitkeep` file.

---

## Target Structure

```
src/spacegen/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── features.py       # pure feature engineering logic (gene filtering, pathway scores)
│   └── models.py         # pure ML logic (training, evaluation, metrics)
├── ports/
│   ├── __init__.py
│   └── interfaces.py     # abstract base classes defining what core needs
├── adapters/
│   ├── __init__.py
│   ├── local_io.py       # local Parquet read/write implementations
│   └── mlflow_logger.py  # MLflow experiment tracking implementation
└── config.py             # wires adapters to ports, loads pipeline settings
```

---

## Step-by-step Instructions

### 1. Create the directory structure
- Create `src/spacegen/core/` with `__init__.py`
- Create `src/spacegen/ports/` with `__init__.py`
- Create `src/spacegen/adapters/` with `__init__.py`

### 2. Create `src/spacegen/ports/interfaces.py`
Define abstract base classes using Python's `abc` module. These are the contracts the core depends on — no implementations here.

```python
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
```

### 3. Move `features.py` → `src/spacegen/core/features.py`
- Move all feature engineering logic from the current `features.py`
- Ensure functions are pure: take `pl.DataFrame` in, return `pl.DataFrame` out
- No file I/O, no MLflow calls, no path references
- If any I/O exists in the current file, extract it out — it belongs in adapters

### 4. Move `models.py` → `src/spacegen/core/models.py`
- Move all ML logic from the current `models.py`
- Functions should take dataframes/arrays and return trained models, predictions, metric dicts
- No file saving, no MLflow logging inside core — that happens through ports
- If any MLflow calls exist in the current file, replace them with calls to an `ExperimentLogger` port passed as a parameter

### 5. Create `src/spacegen/adapters/local_io.py`
Implement the reader/writer ports for local Parquet files using the existing medallion directory structure:

```python
import polars as pl
from pathlib import Path
from ..ports.interfaces import ExpressionReader, DataWriter

DATA_ROOT = Path("data")

class LocalParquetReader(ExpressionReader):
    def read(self, dataset: str, layer: str) -> pl.DataFrame:
        path = DATA_ROOT / layer / dataset
        return pl.read_parquet(path)

class LocalParquetWriter(DataWriter):
    def write(self, df: pl.DataFrame, dataset: str, layer: str, version: str | None = None) -> Path:
        path = DATA_ROOT / layer / dataset
        if version:
            path = path / version
        path.mkdir(parents=True, exist_ok=True)
        out = path / "data.parquet"
        df.write_parquet(out)
        return out
```

### 6. Create `src/spacegen/adapters/mlflow_logger.py`
Implement the experiment logger port:

```python
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
```

### 7. Move `io.py` logic into adapters
- Any read/write logic from the current `io.py` should go into `local_io.py`
- Any MLflow logic should go into `mlflow_logger.py`
- Delete `src/spacegen/io.py` after migration

### 8. Update `config.py`
This stays at `src/spacegen/config.py`. It wires adapters to ports — this is where you decide local vs cloud. Move any existing config logic here and add adapter wiring:

```python
from .adapters.local_io import LocalParquetReader, LocalParquetWriter
from .adapters.mlflow_logger import MLflowLogger

def get_reader():
    return LocalParquetReader()

def get_writer():
    return LocalParquetWriter()

def get_logger():
    return MLflowLogger()
```

### 9. Delete old flat files
After all logic has been moved:
- Delete `src/spacegen/features.py` (now at `core/features.py`)
- Delete `src/spacegen/models.py` (now at `core/models.py`)
- Delete `src/spacegen/io.py` (split into `adapters/local_io.py` and `adapters/mlflow_logger.py`)
- Keep `src/spacegen/__init__.py` and `src/spacegen/config.py`

### 10. Add `.gitkeep` to empty project directories
Add `.gitkeep` to these directories if they are empty:
- `conf/.gitkeep`
- `notebooks/.gitkeep`
- `reports/.gitkeep`
- `tests/.gitkeep`

---

## Key Principles
- **Core has zero external I/O.** No `open()`, no `read_parquet()`, no `mlflow.*` inside `core/`. It only operates on data passed to it.
- **Ports are abstract.** Just ABCs defining method signatures. No implementations.
- **Adapters implement ports.** Each adapter is swappable — local today, S3/Databricks later.
- **Config wires it together.** The only place that knows which adapters are in use.
- **Keep it minimal.** No extra abstractions, helper files, or boilerplate beyond what's listed here.
