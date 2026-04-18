"""Pydantic models for input validation.

These sit between adapters and core — ensuring data contracts
are enforced before any processing begins.
"""

from spacegen.models.configs import (
    QCConfig,
    NormalizationConfig,
    FeatureConfig,
    ProvenanceMetadata,
)
