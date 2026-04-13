"""Core business logic — pure functions, no I/O."""

from spacegen.core.qc import (
    calculate_qc_metrics,
    filter_cells_condition_aware,
)
from spacegen.core.normalization import (
    normalize_counts,
    select_hvgs,
)
from spacegen.core.features import (
    build_pseudobulk_expression,
    build_cell_type_proportions,
    build_qc_features,
    merge_features,
)
