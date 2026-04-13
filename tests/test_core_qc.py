"""Tests for spacegen.core.qc — pure QC functions."""

import anndata as ad
import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from spacegen.core.qc import calculate_qc_metrics, filter_cells_condition_aware


@pytest.fixture
def mock_adata():
    """Create a small mock AnnData for testing."""
    n_cells = 20
    n_genes = 50
    np.random.seed(42)

    X = sp.random(n_cells, n_genes, density=0.3, format="csr")
    X.data = np.round(X.data * 100).astype(np.float32)

    gene_names = [f"Gene{i}" for i in range(n_genes)]
    gene_names[0] = "mt-Co1"
    gene_names[1] = "mt-Co2"
    gene_names[2] = "mt-Nd1"

    obs = pd.DataFrame(
        {
            "condition": (["Space Flight"] * 12) + (["Ground Control"] * 8),
            "sample_name": (["S1"] * 6) + (["S2"] * 6) + (["S3"] * 4) + (["S4"] * 4),
        },
        index=[f"cell_{i}" for i in range(n_cells)],
    )

    var = pd.DataFrame(index=gene_names)

    return ad.AnnData(X=X, obs=obs, var=var)


class TestCalculateQcMetrics:
    def test_adds_mt_flag(self, mock_adata):
        result = calculate_qc_metrics(mock_adata)
        assert "mt" in result.var.columns
        assert result.var["mt"].sum() == 3

    def test_adds_qc_columns(self, mock_adata):
        result = calculate_qc_metrics(mock_adata)
        assert "n_genes_by_counts" in result.obs.columns
        assert "total_counts" in result.obs.columns
        assert "pct_counts_mt" in result.obs.columns

    def test_does_not_modify_input(self, mock_adata):
        original_cols = list(mock_adata.obs.columns)
        calculate_qc_metrics(mock_adata)
        assert list(mock_adata.obs.columns) == original_cols


class TestFilterCellsConditionAware:
    def test_returns_fewer_cells(self, mock_adata):
        adata_qc = calculate_qc_metrics(mock_adata)
        result = filter_cells_condition_aware(
            adata_qc, min_genes=1, min_counts=1, max_counts=999999
        )
        assert result.n_obs <= adata_qc.n_obs

    def test_preserves_condition_labels(self, mock_adata):
        adata_qc = calculate_qc_metrics(mock_adata)
        result = filter_cells_condition_aware(
            adata_qc, min_genes=0, min_counts=0, max_counts=999999,
            mt_threshold_gc=100, mt_threshold_flight=100,
        )
        conditions = set(result.obs["condition"].unique())
        assert conditions.issubset({"Space Flight", "Ground Control"})

    def test_does_not_modify_input(self, mock_adata):
        adata_qc = calculate_qc_metrics(mock_adata)
        n_before = adata_qc.n_obs
        filter_cells_condition_aware(adata_qc, min_genes=1, min_counts=1)
        assert adata_qc.n_obs == n_before
