"""Tests for spacegen.core.features — pure feature engineering functions."""

import anndata as ad
import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from spacegen.core.features import (
    build_pseudobulk_expression,
    build_cell_type_proportions,
    build_qc_features,
    merge_features,
)


@pytest.fixture
def mock_annotated_adata():
    """Create a mock annotated AnnData (like gold layer output)."""
    np.random.seed(42)
    n_cells = 60
    n_genes = 30

    X = sp.random(n_cells, n_genes, density=0.3, format="csr")
    X.data = np.round(X.data * 10).astype(np.float32)

    gene_names = [f"Gene{i}" for i in range(n_genes)]

    samples = (["S1"] * 20) + (["S2"] * 20) + (["S3"] * 20)
    conditions = (["Space Flight"] * 20) + (["Space Flight"] * 20) + (["Ground Control"] * 20)
    cell_types = (["TypeA"] * 10 + ["TypeB"] * 10) * 3

    obs = pd.DataFrame(
        {
            "sample_name": samples,
            "condition": conditions,
            "cell_type": cell_types,
            "n_genes_by_counts": np.random.randint(100, 2000, n_cells),
            "total_counts": np.random.randint(500, 5000, n_cells).astype(float),
            "pct_counts_mt": np.random.uniform(0, 5, n_cells),
        },
        index=[f"cell_{i}" for i in range(n_cells)],
    )

    var = pd.DataFrame(index=gene_names)
    return ad.AnnData(X=X, obs=obs, var=var)


class TestBuildPseudobulkExpression:
    def test_correct_number_of_profiles(self, mock_annotated_adata):
        result = build_pseudobulk_expression(
            mock_annotated_adata,
            gene_names=["Gene0", "Gene1"],
            cell_types=["TypeA", "TypeB"],
        )
        # 3 samples × 2 cell types = 6 profiles
        assert len(result) == 6

    def test_has_expression_columns(self, mock_annotated_adata):
        result = build_pseudobulk_expression(
            mock_annotated_adata,
            gene_names=["Gene0", "Gene1"],
            cell_types=["TypeA"],
        )
        assert "expr_Gene0" in result.columns
        assert "expr_Gene1" in result.columns

    def test_min_cells_filter(self, mock_annotated_adata):
        result = build_pseudobulk_expression(
            mock_annotated_adata,
            gene_names=["Gene0"],
            cell_types=["TypeA"],
            min_cells=100,  # no profile has 100 cells
        )
        assert len(result) == 0


class TestBuildCellTypeProportions:
    def test_correct_number_of_rows(self, mock_annotated_adata):
        result = build_cell_type_proportions(
            mock_annotated_adata,
            cell_types=["TypeA", "TypeB"],
        )
        assert len(result) == 3  # 3 samples

    def test_proportions_sum_to_one(self, mock_annotated_adata):
        result = build_cell_type_proportions(
            mock_annotated_adata,
            cell_types=["TypeA", "TypeB"],
        )
        prop_cols = [c for c in result.columns if c.startswith("prop_")]
        row_sums = result[prop_cols].sum(axis=1)
        np.testing.assert_allclose(row_sums, 1.0, atol=0.01)


class TestMergeFeatures:
    def test_adds_label_column(self, mock_annotated_adata):
        pb = build_pseudobulk_expression(
            mock_annotated_adata,
            gene_names=["Gene0"],
            cell_types=["TypeA", "TypeB"],
        )
        qc = build_qc_features(mock_annotated_adata, pb)
        prop = build_cell_type_proportions(
            mock_annotated_adata, cell_types=["TypeA", "TypeB"]
        )
        result = merge_features(pb, qc, prop)
        assert "label" in result.columns
        assert set(result["label"].unique()).issubset({0, 1})
