"""Tests for spacegen.core.normalization — pure normalization functions."""

import anndata as ad
import numpy as np
import pandas as pd
import pytest
import scipy.sparse as sp

from spacegen.core.normalization import normalize_counts, select_hvgs


@pytest.fixture
def mock_adata():
    """Create a small mock AnnData with raw counts."""
    np.random.seed(42)
    X = sp.random(100, 200, density=0.2, format="csr")
    X.data = np.round(X.data * 100).astype(np.float32)

    obs = pd.DataFrame(index=[f"cell_{i}" for i in range(100)])
    var = pd.DataFrame(index=[f"Gene{i}" for i in range(200)])

    return ad.AnnData(X=X, obs=obs, var=var)


class TestNormalizeCounts:
    def test_preserves_raw(self, mock_adata):
        result = normalize_counts(mock_adata, save_raw=True)
        assert result.raw is not None
        assert result.raw.n_obs == mock_adata.n_obs

    def test_no_raw_when_disabled(self, mock_adata):
        result = normalize_counts(mock_adata, save_raw=False)
        assert result.raw is None

    def test_does_not_modify_input(self, mock_adata):
        original_sum = mock_adata.X.sum()
        normalize_counts(mock_adata)
        assert mock_adata.X.sum() == original_sum

    def test_output_is_log_transformed(self, mock_adata):
        result = normalize_counts(mock_adata)
        max_val = result.X.max()
        assert max_val < 20  # log-transformed values should be small


class TestSelectHvgs:
    def test_selects_correct_number(self, mock_adata):
        normalized = normalize_counts(mock_adata)
        result = select_hvgs(normalized, n_top_genes=50)
        assert result.var["highly_variable"].sum() == 50

    def test_does_not_modify_input(self, mock_adata):
        normalized = normalize_counts(mock_adata)
        assert "highly_variable" not in normalized.var.columns
        select_hvgs(normalized, n_top_genes=50)
        assert "highly_variable" not in normalized.var.columns
