"""Adapter for reading .h5ad files (silver/gold layers)."""

from pathlib import Path

import anndata as ad
import scanpy as sc

from spacegen.ports.data_port import DataReader


class H5adReader(DataReader):
    """Read .h5ad files into AnnData."""

    def read(self, path: Path) -> ad.AnnData:
        """Read .h5ad file.

        Args:
            path: Path to .h5ad file.

        Returns:
            AnnData object.
        """
        return sc.read_h5ad(str(path))
