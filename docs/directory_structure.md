# spaceGen Directory Structure

Living document tracking the project's directory structure as it evolves.

**Last Updated:** 2026-04-12

---

## Current Structure

```
spaceGen/
├── .git/                           # Git repository
├── .gitignore                      # Git ignore rules
├── .kiro/                          # Kiro IDE configuration (gitignored)
│   └── steering/
│       ├── project-context.md      # Auto-loaded project context
│       └── project-rules.md        # Coding conventions and AI preferences
├── LICENSE                         # Project license
├── README.md                       # Project overview and documentation
├── pyproject.toml                  # Python project configuration and dependencies
│
├── data/                           # Data storage (gitignored)
│   ├── OSD-352/                    # Raw source data
│   │   ├── GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5
│   │   ├── OSD-352_metadata_OSD-352-ISA.zip
│   │   ├── i_Investigation.txt
│   │   ├── s_OSD-352.txt
│   │   └── a_OSD-352_transcription-profiling_single-cell-rna-sequencing_illumina.txt
│   │
│   └── bronze/                     # Bronze layer (raw + provenance)
│       └── osd352_brain/
│           ├── ingest_date=2026-03-10/  # Initial ingestion (empty)
│           └── ingest_date=2026-03-12/  # Current bronze data
│               ├── obs.parquet     # Cell metadata (32,243 cells)
│               ├── var.parquet     # Gene metadata (32,285 genes)
│               └── X.h5            # Sparse count matrix (~50 MB)
│
│   └── silver/                     # Silver layer (QC + normalized)
│       └── osd352_brain_v1_qc.h5ad # AnnData: 27,968 cells, normalized
│
│   └── gold/                       # Gold layer (annotated + DE)
│       ├── osd352_brain_v1_annotated.h5ad  # 67 cell types, 22 clusters (654 MB)
│       └── osd352_brain_v1_de_results.parquet  # DE results (3.2 MB)
│       └── osd352_brain_v1_features.parquet    # ML features (2.5 MB, 54×3261)
│
├── docs/                           # Documentation
│   ├── PROJECT_LOG.md              # Development log and decisions
│   ├── NOTES.md                    # Technical notes, findings, future plans
│   ├── data_schema.md              # Data structure documentation
│   └── directory_structure.md      # This file
│
├── notebooks/                      # Jupyter notebooks
│   ├── .gitkeep
│   ├── 01_explore_osd352.ipynb     # Initial data exploration
│   ├── 02_bronze_ingestion.ipynb   # Bronze layer ingestion
│   └── 03_silver_qc.ipynb          # Silver layer QC and normalization
│   └── 04_gold_clustering.ipynb    # Gold layer clustering, annotation, DE
│   └── 05_gold_features.ipynb     # Feature engineering for ML classifier
│   └── 06_model_training.ipynb    # ML classifiers with MLflow tracking
│   └── 07_gsea.ipynb              # Gene set enrichment analysis
│
├── reports/                        # Analysis outputs and reports
│   └── .gitkeep
│
├── src/                            # Source code
│   ├── .gitkeep
│   ├── spacegen/                   # Main package (hexagonal architecture)
│   │   ├── __init__.py
│   │   ├── core/                   # Pure business logic (no I/O)
│   │   │   ├── __init__.py
│   │   │   ├── qc.py              # Condition-aware QC filtering
│   │   │   ├── normalization.py   # Normalize, log1p, HVG selection
│   │   │   └── features.py        # Pseudobulk aggregation, feature engineering
│   │   ├── ports/                  # Abstract interfaces
│   │   │   ├── __init__.py
│   │   │   └── data_port.py       # DataReader, DataWriter ABCs
│   │   └── adapters/              # Concrete I/O implementations
│   │       ├── __init__.py
│   │       ├── h5_reader.py       # BronzeH5Reader
│   │       ├── h5ad_reader.py     # H5adReader
│   │       └── local_writer.py    # LocalWriter (.h5ad, .parquet, .json)
│   └── spacegen.egg-info/          # Package metadata (auto-generated)
│
└── tests/                          # Unit and integration tests
    ├── __init__.py
    ├── test_core_qc.py             # QC function tests (6 tests)
    ├── test_core_normalization.py  # Normalization tests (6 tests)
    └── test_core_features.py       # Feature engineering tests (6 tests)
```

---

## Planned Structure (Not Yet Created)

```
src/spacegen/
├── __init__.py
├── core/                           # Pure business logic (no I/O)
│   ├── __init__.py
│   ├── qc.py                       # Quality control functions
│   ├── normalization.py            # Normalization methods
│   ├── clustering.py               # Clustering algorithms
│   └── network.py                  # Network analysis
│
├── ports/                          # Abstract interfaces
│   ├── __init__.py
│   ├── data_reader.py              # Abstract data reader
│   └── data_writer.py              # Abstract data writer
│
└── adapters/                       # Concrete implementations
    ├── __init__.py
    ├── local_h5_reader.py          # Read 10X HDF5 files
    ├── parquet_reader.py           # Read Parquet files
    └── mlflow_logger.py            # MLflow experiment tracking
```

---

## Data Layer Conventions

### Bronze Layer
- **Path:** `data/bronze/{dataset}_{tissue}/ingest_date={YYYY-MM-DD}/`
- **Files:** `obs.parquet`, `var.parquet`, `X.h5`
- **Purpose:** Raw data + provenance metadata

### Silver Layer (Planned)
- **Path:** `data/silver/`
- **Files:** `{dataset}_{tissue}_v{version}_qc.h5ad`
- **Purpose:** QC-filtered, normalized, HVGs flagged, PCA/UMAP embeddings

### Gold Layer
- **Path:** `data/gold/`
- **Files:** `{dataset}_{tissue}_v{version}_annotated.h5ad`, `{dataset}_{tissue}_v{version}_de_results.parquet`
- **Purpose:** Clustered, cell type annotated, DE results, analysis-ready

### Models (Planned)
- **Path:** MLflow artifact store
- **Purpose:** Trained classifiers and model artifacts

---

## Notes

- All data files are gitignored except `.gitkeep` placeholders
- Hive-style partitioning used for bronze layer (e.g., `ingest_date=2026-03-10/`)
- Version numbers in silver/gold follow semantic versioning
- Source code follows hexagonal architecture (core/ports/adapters)
