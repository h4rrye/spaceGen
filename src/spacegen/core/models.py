"""Pure ML logic.

All functions should:
- Take dataframes/arrays and return trained models, predictions, metric dicts
- Accept an ExperimentLogger port for logging (no direct MLflow calls)
- No file saving inside core - that happens through ports
"""

import polars as pl
from typing import Any
from ..ports.interfaces import ExperimentLogger


# Example placeholder functions - replace with actual ML logic
def train_model(
    df: pl.DataFrame,
    target_col: str,
    logger: ExperimentLogger | None = None
) -> Any:
    """Train a machine learning model.

    Args:
        df: Training data
        target_col: Name of target column
        logger: Optional experiment logger for tracking

    Returns:
        Trained model object
    """
    # Placeholder implementation
    if logger:
        logger.log_params({"target_col": target_col})

    # Your model training logic here
    model = None

    return model


def evaluate_model(
    model: Any,
    df: pl.DataFrame,
    target_col: str,
    logger: ExperimentLogger | None = None
) -> dict[str, float]:
    """Evaluate model performance.

    Args:
        model: Trained model
        df: Evaluation data
        target_col: Name of target column
        logger: Optional experiment logger for tracking

    Returns:
        Dictionary of metric names to values
    """
    # Placeholder implementation
    metrics = {
        "accuracy": 0.0,
        "f1_score": 0.0
    }

    if logger:
        logger.log_metrics(metrics)

    return metrics
