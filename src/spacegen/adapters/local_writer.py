"""Adapter for writing data to local filesystem."""

import json
from pathlib import Path

import anndata as ad
import pandas as pd

from spacegen.ports.data_port import DataWriter


class LocalWriter(DataWriter):
    """Write data to local files."""

    def write_h5ad(self, adata: ad.AnnData, path: Path) -> None:
        """Write AnnData to .h5ad file.

        Args:
            adata: AnnData object to save.
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        adata.write(path)

    def write_parquet(self, df: pd.DataFrame, path: Path) -> None:
        """Write DataFrame to Parquet file.

        Args:
            df: DataFrame to save.
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(path, index=False)

    def write_json(self, data: dict, path: Path) -> None:
        """Write dict to JSON file (for D3 visualization).

        Args:
            data: Dictionary to serialize.
            path: Output file path.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2, default=str)
