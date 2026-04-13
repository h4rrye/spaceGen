"""Abstract interfaces for data reading and writing.

Ports define what the core needs — adapters implement how.
"""

from abc import ABC, abstractmethod
from pathlib import Path

import anndata as ad
import pandas as pd


class DataReader(ABC):
    """Abstract interface for reading data into AnnData."""

    @abstractmethod
    def read(self, path: Path) -> ad.AnnData:
        """Read data from path and return AnnData object."""
        ...


class DataWriter(ABC):
    """Abstract interface for writing data."""

    @abstractmethod
    def write_h5ad(self, adata: ad.AnnData, path: Path) -> None:
        """Write AnnData to .h5ad file."""
        ...

    @abstractmethod
    def write_parquet(self, df: pd.DataFrame, path: Path) -> None:
        """Write DataFrame to Parquet file."""
        ...

    @abstractmethod
    def write_json(self, data: dict, path: Path) -> None:
        """Write dict to JSON file (for D3 visualization layer)."""
        ...
