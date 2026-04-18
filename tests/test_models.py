"""Tests for spacegen.models — Pydantic validation."""

from datetime import date

import pytest
from pydantic import ValidationError

from spacegen.models.configs import (
    QCConfig,
    NormalizationConfig,
    FeatureConfig,
    ProvenanceMetadata,
)


class TestQCConfig:
    def test_defaults_are_valid(self):
        config = QCConfig()
        assert config.min_genes == 200
        assert config.mt_threshold_flight >= config.mt_threshold_gc

    def test_rejects_max_below_min_counts(self):
        with pytest.raises(ValidationError):
            QCConfig(min_counts=5000, max_counts=1000)

    def test_rejects_flight_mt_below_gc(self):
        with pytest.raises(ValidationError):
            QCConfig(mt_threshold_gc=10.0, mt_threshold_flight=3.0)

    def test_rejects_negative_min_genes(self):
        with pytest.raises(ValidationError):
            QCConfig(min_genes=-1)

    def test_accepts_custom_thresholds(self):
        config = QCConfig(min_genes=300, mt_threshold_gc=3.0, mt_threshold_flight=8.0)
        assert config.min_genes == 300


class TestNormalizationConfig:
    def test_defaults_are_valid(self):
        config = NormalizationConfig()
        assert config.target_sum == 1e4
        assert config.n_top_genes == 2000

    def test_rejects_zero_target_sum(self):
        with pytest.raises(ValidationError):
            NormalizationConfig(target_sum=0)

    def test_rejects_invalid_flavor(self):
        with pytest.raises(ValidationError):
            NormalizationConfig(hvg_flavor="invalid_method")

    def test_rejects_too_few_hvgs(self):
        with pytest.raises(ValidationError):
            NormalizationConfig(n_top_genes=10)


class TestFeatureConfig:
    def test_defaults_are_valid(self):
        config = FeatureConfig()
        assert config.min_cells == 5

    def test_rejects_duplicate_genes(self):
        with pytest.raises(ValidationError):
            FeatureConfig(gene_names=["Malat1", "Gfap", "Malat1"])

    def test_rejects_duplicate_cell_types(self):
        with pytest.raises(ValidationError):
            FeatureConfig(cell_types=["Oligo NN", "Oligo NN"])

    def test_accepts_valid_lists(self):
        config = FeatureConfig(
            gene_names=["Malat1", "Gfap"],
            cell_types=["Oligo NN", "Microglia NN"],
        )
        assert len(config.gene_names) == 2


class TestProvenanceMetadata:
    def test_valid_provenance(self):
        meta = ProvenanceMetadata(
            ingest_date=date(2026, 3, 12),
            source_file="GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5",
            dataset_id="OSD-352",
            organism="Mus musculus",
            tissue="brain",
            technology="10X Chromium snRNA-seq",
            genome_build="mm10",
            processing_pipeline="GeneLab scRNA-seq",
        )
        assert meta.dataset_id == "OSD-352"

    def test_rejects_bad_dataset_id(self):
        with pytest.raises(ValidationError):
            ProvenanceMetadata(
                ingest_date=date(2026, 3, 12),
                source_file="test.h5",
                dataset_id="INVALID",
                organism="Mus musculus",
                tissue="brain",
                technology="10X",
                genome_build="mm10",
                processing_pipeline="test",
            )

    def test_rejects_empty_source_file(self):
        with pytest.raises(ValidationError):
            ProvenanceMetadata(
                ingest_date=date(2026, 3, 12),
                source_file="",
                dataset_id="OSD-352",
                organism="Mus musculus",
                tissue="brain",
                technology="10X",
                genome_build="mm10",
                processing_pipeline="test",
            )
