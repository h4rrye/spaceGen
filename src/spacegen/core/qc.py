"""Quality control functions for scRNA-seq data.

All functions are pure — they take AnnData in and return AnnData out.
No file I/O, no side effects.
"""

import anndata as ad
import pandas as pd
import scanpy as sc

from spacegen.models.configs import QCConfig


def calculate_qc_metrics(adata: ad.AnnData, mt_prefix: str = "mt-") -> ad.AnnData:
    """Flag mitochondrial genes and compute per-cell QC metrics.

    Args:
        adata: AnnData object with raw counts.
        mt_prefix: Prefix for mitochondrial gene names (mouse = "mt-").

    Returns:
        AnnData with mt flag in var and QC columns in obs:
        n_genes_by_counts, total_counts, pct_counts_mt.
    """
    adata = adata.copy()
    adata.var["mt"] = adata.var_names.str.startswith(mt_prefix)

    sc.pp.calculate_qc_metrics(
        adata,
        qc_vars=["mt"],
        percent_top=None,
        log1p=False,
        inplace=True,
    )
    return adata


def filter_cells_condition_aware(
    adata: ad.AnnData,
    config: QCConfig = None,
    **kwargs,
) -> ad.AnnData:
    """Apply condition-aware QC filtering.

    Uses different mitochondrial thresholds per condition to preserve
    biologically relevant stressed cells in spaceflight samples.

    Args:
        adata: AnnData with QC metrics already computed.
        config: QCConfig with validated parameters. If None, builds from kwargs.
        **kwargs: Passed to QCConfig if config is None.

    Returns:
        Filtered AnnData (copy).
    """
    if config is None:
        config = QCConfig(**kwargs)

    is_gc = adata.obs[config.condition_col] == config.gc_label
    is_flight = adata.obs[config.condition_col] == config.flight_label

    mt_pass_gc = adata.obs.loc[is_gc, "pct_counts_mt"] < config.mt_threshold_gc
    mt_pass_flight = adata.obs.loc[is_flight, "pct_counts_mt"] < config.mt_threshold_flight

    mt_pass = pd.Series(False, index=adata.obs.index)
    mt_pass[mt_pass_gc.index] = mt_pass_gc
    mt_pass[mt_pass_flight.index] = mt_pass_flight

    keep = (
        (adata.obs["n_genes_by_counts"] >= config.min_genes)
        & (adata.obs["total_counts"] >= config.min_counts)
        & (adata.obs["total_counts"] <= config.max_counts)
        & mt_pass
    )

    return adata[keep].copy()
