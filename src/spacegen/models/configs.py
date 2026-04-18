"""Pydantic configuration models for pipeline validation.

Each model validates inputs before they reach core functions.
Catches bad parameters early with clear error messages.
"""

from datetime import date
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


class QCConfig(BaseModel):
    """Configuration for condition-aware QC filtering.

    Validates that thresholds are biologically reasonable
    and column names exist before filtering begins.
    """

    min_genes: int = Field(default=200, ge=0, le=10000,
        description="Minimum genes detected per cell")
    min_counts: int = Field(default=500, ge=0, le=100000,
        description="Minimum UMI counts per cell")
    max_counts: int = Field(default=50000, ge=1000,
        description="Maximum UMI counts per cell (doublet filter)")
    mt_threshold_gc: float = Field(default=5.0, ge=0, le=100,
        description="Max mitochondrial % for ground control cells")
    mt_threshold_flight: float = Field(default=10.0, ge=0, le=100,
        description="Max mitochondrial % for spaceflight cells")
    mt_prefix: str = Field(default="mt-",
        description="Prefix for mitochondrial gene names")
    condition_col: str = Field(default="condition",
        description="Column name for condition labels in obs")
    gc_label: str = Field(default="Ground Control",
        description="Label for ground control condition")
    flight_label: str = Field(default="Space Flight",
        description="Label for spaceflight condition")

    @model_validator(mode="after")
    def validate_thresholds(self):
        """Ensure max_counts > min_counts and flight mt >= gc mt."""
        if self.max_counts <= self.min_counts:
            raise ValueError(
                f"max_counts ({self.max_counts}) must be greater than "
                f"min_counts ({self.min_counts})"
            )
        if self.mt_threshold_flight < self.mt_threshold_gc:
            raise ValueError(
                f"mt_threshold_flight ({self.mt_threshold_flight}) should be >= "
                f"mt_threshold_gc ({self.mt_threshold_gc}) to preserve stressed cells"
            )
        return self


class NormalizationConfig(BaseModel):
    """Configuration for normalization and HVG selection."""

    target_sum: float = Field(default=1e4, gt=0,
        description="Target total counts per cell for normalization")
    save_raw: bool = Field(default=True,
        description="Whether to preserve raw counts in adata.raw")
    n_top_genes: int = Field(default=2000, ge=100, le=10000,
        description="Number of highly variable genes to select")
    hvg_flavor: Literal["seurat_v3", "seurat", "cell_ranger"] = Field(
        default="seurat_v3",
        description="Method for HVG selection")


class FeatureConfig(BaseModel):
    """Configuration for pseudobulk feature engineering."""

    min_cells: int = Field(default=5, ge=1,
        description="Minimum cells per sample × cell type profile")
    sample_col: str = Field(default="sample_name",
        description="Column name for sample identifiers")
    cell_type_col: str = Field(default="cell_type",
        description="Column name for cell type labels")
    condition_col: str = Field(default="condition",
        description="Column name for condition labels")
    flight_label: str = Field(default="Space Flight",
        description="Label for spaceflight condition (becomes label=1)")
    gene_names: List[str] = Field(default_factory=list,
        description="Gene names to use as expression features")
    cell_types: List[str] = Field(default_factory=list,
        description="Cell types to include in pseudobulk")

    @field_validator("gene_names")
    @classmethod
    def validate_gene_names(cls, v):
        if len(v) > 0 and len(set(v)) != len(v):
            raise ValueError("gene_names contains duplicates")
        return v

    @field_validator("cell_types")
    @classmethod
    def validate_cell_types(cls, v):
        if len(v) > 0 and len(set(v)) != len(v):
            raise ValueError("cell_types contains duplicates")
        return v


class ProvenanceMetadata(BaseModel):
    """Provenance metadata for bronze layer ingestion.

    Ensures all required provenance fields are present
    and correctly formatted before writing to bronze.
    """

    ingest_date: date = Field(
        description="Date of data ingestion (YYYY-MM-DD)")
    source_file: str = Field(min_length=1,
        description="Original source filename")
    dataset_id: str = Field(pattern=r"^OSD-\d+$",
        description="Dataset identifier (e.g., OSD-352)")
    organism: str = Field(min_length=1,
        description="Species name (e.g., Mus musculus)")
    tissue: str = Field(min_length=1,
        description="Tissue type (e.g., brain)")
    technology: str = Field(min_length=1,
        description="Sequencing technology")
    genome_build: str = Field(min_length=1,
        description="Reference genome version (e.g., mm10)")
    processing_pipeline: str = Field(min_length=1,
        description="Data processing pipeline name")
