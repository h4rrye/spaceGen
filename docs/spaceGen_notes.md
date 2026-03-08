# spaceGen notes



`pyproject.toml` covers everything `environment.yml` does for dependency management. The only reason to keep `environment.yml` is if you're specifically using Conda (common in bioinformatics), but since your stack is all pip-installable (polars, mlflow, scikit-learn, xgboost) there's no reason to maintain both. One source of truth for dependencies is better than two that can drift apart.

____

Hexagonal architecture (also called "ports and adapters") is a design pattern where your core business logic sits in the center and knows nothing about the outside world. Everything external — databases, APIs, UIs, file systems — connects through defined interfaces.

Think of it as three layers. The **core** contains your pure logic (in your case, that would be things like "normalize gene expression counts" or "train a classifier"). It has no imports from external libraries for I/O. Then you have **ports**, which are just interfaces — abstract definitions of what the core needs. "I need to read expression data" is a port. "I need to save a model" is a port. Finally, **adapters** are the concrete implementations that plug into those ports. "Read a Parquet file from local disk" is one adapter. "Read from S3" is another adapter. "Read from a database" is yet another. The core doesn't care which one you use.

The name comes from the hexagon shape in the original diagrams, but the shape doesn't actually mean anything — it was just to break people out of thinking in the traditional top-down layered cake (UI → business logic → database).

The practical payoff is swappability. Your pipeline logic stays the same whether you're reading from local Parquet files on your laptop or from Delta Lake on Databricks. You just swap the adapter. It also makes testing easy — you can write a fake in-memory adapter and test your core logic without touching any real files or APIs.

____



### Datasets

**NASA Open Science Data Repository (OSDR)** — that's the official name of the platform.

The specific mission is **RRRM-1 / Rodent Research-8 (RR-8)**, and the datasets are from the GeneLab data processing pipeline within OSDR. For your logs, something like:

"Source: NASA OSDR (osdr.nasa.gov), RRRM-1/RR-8 mission, 10X Genomics scRNA-seq, datasets OSD-910 (spleen), OSD-905 (liver), OSD-918 (blood)"

1. **OSD-910 (Spleen)** — immune hub, richest cell type diversity, best for network analysis. Build with this first.
2. **OSD-905 (Liver)** — metabolic tissue, connects to your earlier OSD-47 bulk work, different biology from spleen.
3. **OSD-918 (Blood)** — circulating immune cells, bridges between spleen and liver, well-characterized cell markers for easy annotation.

Three tissues, three biological stories: immune response (spleen), metabolic disruption (liver), systemic circulation (blood). Together they paint a picture of how spaceflight affects the whole organism

