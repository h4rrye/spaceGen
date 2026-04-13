"""Normalization and feature selection for scRNA-seq data.

Pure functions — no I/O.
"""

import anndata as ad
import scanpy as sc


def normalize_counts(
    adata: ad.AnnData,
    target_sum: float = 1e4,
    save_raw: bool = True,
) -> ad.AnnData:
    """Total count normalization + log1p transform.

    Args:
        adata: AnnData with raw counts in X.
        target_sum: Target total counts per cell (default 10,000).
        save_raw: If True, store raw counts in adata.raw before normalizing.

    Returns:
        Normalized AnnData (copy). X contains log-normalized values.
    """
    adata = adata.copy()

    if save_raw:
        adata.raw = adata

    sc.pp.normalize_total(adata, target_sum=target_sum)
    sc.pp.log1p(adata)

    return adata


def select_hvgs(
    adata: ad.AnnData,
    n_top_genes: int = 2000,
    flavor: str = "seurat_v3",
) -> ad.AnnData:
    """Select highly variable genes.

    Args:
        adata: Normalized AnnData.
        n_top_genes: Number of HVGs to select.
        flavor: Method for HVG selection.

    Returns:
        AnnData with highly_variable flag in var (copy).
    """
    adata = adata.copy()

    sc.pp.highly_variable_genes(
        adata,
        n_top_genes=n_top_genes,
        flavor=flavor,
    )

    return adata
