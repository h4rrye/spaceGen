"""Feature engineering for ML classification.

Pure functions — no I/O. Takes AnnData/DataFrames in, returns DataFrames out.
"""

from typing import List

import anndata as ad
import numpy as np
import pandas as pd


def build_pseudobulk_expression(
    adata: ad.AnnData,
    gene_names: List[str],
    cell_types: List[str],
    sample_col: str = "sample_name",
    cell_type_col: str = "cell_type",
    condition_col: str = "condition",
    min_cells: int = 5,
) -> pd.DataFrame:
    """Aggregate mean expression per sample × cell type.

    Args:
        adata: Annotated AnnData.
        gene_names: List of gene names to use as features.
        cell_types: List of cell types to include.
        sample_col: Column for sample identifiers.
        cell_type_col: Column for cell type labels.
        condition_col: Column for condition labels.
        min_cells: Minimum cells per profile (skip if fewer).

    Returns:
        DataFrame with columns: sample_name, cell_type, condition,
        n_cells, expr_{gene} for each gene.
    """
    rows = []

    for sample in adata.obs[sample_col].unique():
        for cell_type in cell_types:
            mask = (
                (adata.obs[sample_col] == sample)
                & (adata.obs[cell_type_col] == cell_type)
            )
            subset = adata[mask]

            if subset.n_obs < min_cells:
                continue

            expr_data = subset[:, gene_names].X
            if hasattr(expr_data, "toarray"):
                expr_data = expr_data.toarray()
            mean_expr = np.mean(expr_data, axis=0)

            row = {
                sample_col: sample,
                cell_type_col: cell_type,
                condition_col: subset.obs[condition_col].iloc[0],
                "n_cells": subset.n_obs,
            }

            for i, gene in enumerate(gene_names):
                row[f"expr_{gene}"] = mean_expr[i]

            rows.append(row)

    return pd.DataFrame(rows)


def build_cell_type_proportions(
    adata: ad.AnnData,
    cell_types: List[str],
    sample_col: str = "sample_name",
    cell_type_col: str = "cell_type",
    condition_col: str = "condition",
) -> pd.DataFrame:
    """Compute cell type fractions per sample.

    Args:
        adata: Annotated AnnData.
        cell_types: Cell types to compute proportions for.
        sample_col: Column for sample identifiers.
        cell_type_col: Column for cell type labels.
        condition_col: Column for condition labels.

    Returns:
        DataFrame with columns: sample_name, condition,
        prop_{cell_type} for each cell type.
    """
    rows = []

    for sample in adata.obs[sample_col].unique():
        sample_mask = adata.obs[sample_col] == sample
        total_cells = sample_mask.sum()
        condition = adata.obs.loc[sample_mask, condition_col].iloc[0]

        row = {sample_col: sample, condition_col: condition}

        for cell_type in cell_types:
            ct_mask = sample_mask & (adata.obs[cell_type_col] == cell_type)
            row[f"prop_{cell_type}"] = ct_mask.sum() / total_cells

        rows.append(row)

    return pd.DataFrame(rows)


def build_qc_features(
    adata: ad.AnnData,
    pseudobulk_df: pd.DataFrame,
    sample_col: str = "sample_name",
    cell_type_col: str = "cell_type",
) -> pd.DataFrame:
    """Compute QC summary metrics per pseudobulk profile.

    Args:
        adata: AnnData with QC metrics in obs.
        pseudobulk_df: DataFrame with sample_name and cell_type columns.
        sample_col: Column for sample identifiers.
        cell_type_col: Column for cell type labels.

    Returns:
        DataFrame with QC feature columns.
    """
    rows = []

    for _, row in pseudobulk_df[[sample_col, cell_type_col]].iterrows():
        mask = (
            (adata.obs[sample_col] == row[sample_col])
            & (adata.obs[cell_type_col] == row[cell_type_col])
        )
        subset = adata.obs[mask]

        rows.append({
            sample_col: row[sample_col],
            cell_type_col: row[cell_type_col],
            "qc_mean_genes": subset["n_genes_by_counts"].mean(),
            "qc_mean_counts": subset["total_counts"].mean(),
            "qc_mean_mt_pct": subset["pct_counts_mt"].mean(),
            "qc_median_genes": subset["n_genes_by_counts"].median(),
            "qc_median_counts": subset["total_counts"].median(),
        })

    return pd.DataFrame(rows)


def merge_features(
    pseudobulk_df: pd.DataFrame,
    qc_df: pd.DataFrame,
    prop_df: pd.DataFrame,
    sample_col: str = "sample_name",
    cell_type_col: str = "cell_type",
    condition_col: str = "condition",
    flight_label: str = "Space Flight",
) -> pd.DataFrame:
    """Merge all feature sources into a single ML-ready DataFrame.

    Args:
        pseudobulk_df: Expression features.
        qc_df: QC summary features.
        prop_df: Cell type proportion features.
        sample_col: Sample column name.
        cell_type_col: Cell type column name.
        condition_col: Condition column name.
        flight_label: Label for spaceflight condition (becomes label=1).

    Returns:
        Merged DataFrame with binary label column.
    """
    features_df = pseudobulk_df.merge(
        qc_df,
        on=[sample_col, cell_type_col],
        how="left",
    )

    features_df = features_df.merge(
        prop_df,
        on=[sample_col, condition_col],
        how="left",
    )

    features_df["label"] = (
        features_df[condition_col] == flight_label
    ).astype(int)

    return features_df
