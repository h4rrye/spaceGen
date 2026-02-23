import polars as pl
from pathlib import Path
from ..ports.interfaces import ExpressionReader, DataWriter

DATA_ROOT = Path("data")


class LocalParquetReader(ExpressionReader):
    def read(self, dataset: str, layer: str) -> pl.DataFrame:
        path = DATA_ROOT / layer / dataset
        return pl.read_parquet(path)


class LocalParquetWriter(DataWriter):
    def write(self, df: pl.DataFrame, dataset: str, layer: str, version: str | None = None) -> Path:
        path = DATA_ROOT / layer / dataset
        if version:
            path = path / version
        path.mkdir(parents=True, exist_ok=True)
        out = path / "data.parquet"
        df.write_parquet(out)
        return out
