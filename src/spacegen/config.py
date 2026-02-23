"""Configuration module for wiring adapters to ports.

This is where you decide which implementations to use
(local vs cloud, etc.) and configure pipeline settings.
"""

from .adapters.local_io import LocalParquetReader, LocalParquetWriter
from .adapters.mlflow_logger import MLflowLogger


def get_reader():
    """Get the configured expression data reader."""
    return LocalParquetReader()


def get_writer():
    """Get the configured data writer."""
    return LocalParquetWriter()


def get_logger():
    """Get the configured experiment logger."""
    return MLflowLogger()
