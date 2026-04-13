"""Adapter for reading bronze layer data (Parquet + HDF5)."""

from pathlib import Path

import anndata as ad
import h5py
import pandas as pd
import scipy.sparse as sp

from spacegen.ports.data_port import DataReader


class BronzeH5Reader(DataReader):
    """Read bronze layer files and reconstruct AnnData.

    Expects a directory containing:
        obs.parquet  — cell metadata
        var.parquet  — gene metadata
        X.h5         — sparse count matrix (CSR components)
    """

    def read(self, path: Path) -> ad.AnnData:
        """Read bronze directory into AnnData.

        Args:
            path: Path to bronze partition directory
                  (e.g., data/bronze/osd352_brain/ingest_date=2026-03-12/).

        Returns:
            AnnData with sparse X, obs, and var.
        """
        path = Path(path)

        obs = pd.read_parquet(path / "obs.parquet")
        var = pd.read_parquet(path / "var.parquet")

        with h5py.File(path / "X.h5", "r") as f:
            data = f["data"][:]
            indices = f["indices"][:]
            indptr = f["indptr"][:]
            shape = f["shape"][:]

        X = sp.csr_matrix((data, indices, indptr), shape=shape)

        return ad.AnnData(X=X, obs=obs, var=var)
