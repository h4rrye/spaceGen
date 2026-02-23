# spaceGen notes



`pyproject.toml` covers everything `environment.yml` does for dependency management. The only reason to keep `environment.yml` is if you're specifically using Conda (common in bioinformatics), but since your stack is all pip-installable (polars, mlflow, scikit-learn, xgboost) there's no reason to maintain both. One source of truth for dependencies is better than two that can drift apart.

____

Hexagonal architecture (also called "ports and adapters") is a design pattern where your core business logic sits in the center and knows nothing about the outside world. Everything external — databases, APIs, UIs, file systems — connects through defined interfaces.

Think of it as three layers. The **core** contains your pure logic (in your case, that would be things like "normalize gene expression counts" or "train a classifier"). It has no imports from external libraries for I/O. Then you have **ports**, which are just interfaces — abstract definitions of what the core needs. "I need to read expression data" is a port. "I need to save a model" is a port. Finally, **adapters** are the concrete implementations that plug into those ports. "Read a Parquet file from local disk" is one adapter. "Read from S3" is another adapter. "Read from a database" is yet another. The core doesn't care which one you use.

The name comes from the hexagon shape in the original diagrams, but the shape doesn't actually mean anything — it was just to break people out of thinking in the traditional top-down layered cake (UI → business logic → database).

The practical payoff is swappability. Your pipeline logic stays the same whether you're reading from local Parquet files on your laptop or from Delta Lake on Databricks. You just swap the adapter. It also makes testing easy — you can write a fake in-memory adapter and test your core logic without touching any real files or APIs.

____

