# spaceGen Minutiae

Detailed reference information about the project — data files, formats, conventions, and technical details.

---

## Downloaded Data Files (OSD-352)

### Data File
**`GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5`** (288 MB)
- The main data file — processed single-nucleus RNA-seq count matrix
- 10X Genomics HDF5 format (genes × cells)
- Already QC-filtered by GeneLab (low-quality cells removed)
- Contains UMI counts for each gene in each cell
- This is what you'll load with Scanpy

### ISA Metadata Files (Investigation-Study-Assay format)

**`i_Investigation.txt`** (30 KB)
- Top-level study information
- Principal investigator, funding, publication details
- Overall experimental design and objectives

**`s_OSD-352.txt`** (26 KB)
- Study-level metadata
- Sample information: which mice, which conditions (spaceflight vs ground)
- Factor values: treatment groups, timepoints, biological replicates
- Links samples to their experimental conditions

**`a_OSD-352_transcription-profiling_single-cell-rna-sequencing_illumina.txt`** (4.8 KB)
- Assay-level metadata for the scRNA-seq experiment
- Sample-to-file mappings (which cells came from which sample)
- Sequencing protocol details
- This is the key file for linking cell barcodes to spaceflight/ground labels

**`a_OSD-352_transcription-profiling_rna-sequencing-(rna-seq)_illumina.txt`** (13 KB)
- Bulk RNA-seq assay metadata (not single-cell)
- Not needed for your pipeline

**`a_OSD-352_chromatin-accessibility_single-cell-atac-seq_illumina.txt`** (5.0 KB)
- ATAC-seq assay metadata (chromatin accessibility)
- Not needed for your pipeline (we're doing Option B — scRNA-seq only)

**`a_OSD-352_transcription-profiling_spatial-transcriptomics_illumina.txt`** (28 KB)
- Spatial transcriptomics assay metadata
- Not needed for your pipeline

**`OSD-352_metadata_OSD-352-ISA.zip`** (107 KB)
- The original zip file containing all the metadata above
- Can delete this after extraction

### Files You Need
For your pipeline, focus on:
1. `GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5` — the data
2. `s_OSD-352.txt` — sample conditions (spaceflight vs ground)
3. `a_OSD-352_transcription-profiling_single-cell-rna-sequencing_illumina.txt` — sample-to-cell mappings

---

## Data Formats

### 10X Genomics HDF5 Format
The `.h5` file contains:
- `matrix/` — sparse count matrix
  - `data` — non-zero UMI counts
  - `indices` — gene indices
  - `indptr` — cell pointers
  - `shape` — (genes, cells)
- `matrix/features/` — gene information
  - `id` — Ensembl gene IDs
  - `name` — gene symbols
  - `feature_type` — usually "Gene Expression"
- `matrix/barcodes/` — cell barcodes (unique identifiers)

Load with: `scanpy.read_10x_h5(filename)`

### ISA-Tab Format
Tab-separated text files following the ISA (Investigation-Study-Assay) standard:
- Investigation (i_*.txt) — overall study metadata
- Study (s_*.txt) — sample and factor information
- Assay (a_*.txt) — protocol and file mappings

---

## OSD-352 Dataset Details

**Mission:** Rodent Research-3 (RR-3)  
**Tissue:** Brain (whole brain, single-nucleus)  
**Organism:** Mus musculus (mouse)  
**Platform:** 10X Genomics single-nucleus RNA-seq (Illumina)  
**Comparison:** Spaceflight vs Ground Control  
**Release Date:** December 2024  

**Study Design:**
- Flight mice: exposed to microgravity on ISS
- Ground control mice: matched conditions on Earth
- Single-nucleus RNA-seq (snRNA-seq) — nuclei isolated from frozen brain tissue

---

## Pipeline Architecture

### Hexagonal (Ports & Adapters) Design

**Core** (`src/spacegen/core/`)
- Pure business logic
- Functions take AnnData/DataFrames in, return AnnData/DataFrames out
- No I/O, no MLflow calls, no file paths
- Examples: `normalize_counts()`, `cluster_cells()`, `find_markers()`

**Ports** (`src/spacegen/ports/`)
- Abstract interfaces defining contracts
- `DataReader` — read expression data
- `DataWriter` — write processed data
- `ExperimentLogger` — log to MLflow

**Adapters** (`src/spacegen/adapters/`)
- Concrete implementations of ports
- `LocalH5Reader` — read from local `.h5` files
- `ParquetWriter` — write to Parquet files
- `MLflowLogger` — log to MLflow tracking server

### Medallion Data Layers

**Bronze** (`data/bronze/`)
- Raw ingested data with provenance
- Partitioned by ingest date (Hive-style: `year=2026/month=03/day=09/`)
- Includes source metadata, checksums
- Format: Parquet or HDF5

**Silver** (`data/silver/`)
- QC-filtered cells
- Normalized counts (library size correction, log transformation)
- Highly variable genes selected
- Dimensionality reduction (PCA)
- Versioned per dataset
- Format: Parquet + AnnData `.h5ad`

**Gold** (`data/gold/`)
- Clustered cells with type annotations
- Differential expression results
- Network features (cell-cell communication)
- Study-aware train/test splits
- Versioned
- Format: Parquet + AnnData `.h5ad`

**Models** (`models/`)
- Trained classifiers (elastic net, XGBoost)
- MLflow artifacts (UMAP plots, SHAP importance, confusion matrices)
- Network visualizations

---

## Technology Stack

### Core Analysis
- **Scanpy** — scRNA-seq preprocessing, clustering, DE analysis
- **AnnData** — data structure (genes × cells + metadata)
- **NumPy/SciPy** — numerical operations
- **Pandas** — metadata manipulation

### Data Engineering
- **Polars** — fast dataframe operations for medallion layers
- **PyArrow** — Parquet I/O
- **h5py** — HDF5 file handling

### Machine Learning
- **scikit-learn** — preprocessing, elastic net, evaluation metrics
- **XGBoost** — gradient boosting classifier
- **SHAP** — model interpretability

### Network Analysis
- **CellPhoneDB / LIANA / Squidpy** — cell-cell communication (TBD which one)
- **NetworkX** — graph analysis and visualization

### Experiment Tracking
- **MLflow** — parameter logging, metric tracking, artifact storage

### Visualization
- **Matplotlib** — general plotting
- **Seaborn** — statistical visualizations
- **Scanpy plotting** — UMAP, violin plots, dotplots

---

## Naming Conventions

### Files
- Bronze: `{dataset}_{tissue}_{ingest_date}.parquet`
- Silver: `{dataset}_{tissue}_v{version}_qc.h5ad`
- Gold: `{dataset}_{tissue}_v{version}_annotated.h5ad`

### Variables
- Snake_case for Python functions and variables
- PascalCase for classes
- UPPER_CASE for constants

### Git Branches
- `main` — stable, working code
- `dev` — active development
- `feature/{name}` — new features
- `fix/{name}` — bug fixes

---

## Useful Commands

### Data Download
```bash
# Download from OSDR portal
curl -L "https://osdr.nasa.gov/geode-py/ws/studies/OSD-352/download?source=datamanager&file={filename}" -o {output_path}
```

### Scanpy Basics
```python
import scanpy as sc

# Load 10X HDF5
adata = sc.read_10x_h5('path/to/file.h5')

# Basic QC
sc.pp.calculate_qc_metrics(adata, inplace=True)

# Filter cells
sc.pp.filter_cells(adata, min_genes=200)
sc.pp.filter_genes(adata, min_cells=3)

# Normalize
sc.pp.normalize_total(adata, target_sum=1e4)
sc.pp.log1p(adata)

# HVG selection
sc.pp.highly_variable_genes(adata, n_top_genes=2000)

# PCA
sc.pp.pca(adata, n_comps=50)

# Clustering
sc.pp.neighbors(adata, n_neighbors=10, n_pcs=40)
sc.tl.leiden(adata, resolution=0.5)

# UMAP
sc.tl.umap(adata)

# Differential expression
sc.tl.rank_genes_groups(adata, groupby='leiden', method='wilcoxon')
```

---

## References

- NASA OSDR: https://osdr.nasa.gov
- Scanpy Documentation: https://scanpy.readthedocs.io/
- AnnData Documentation: https://anndata.readthedocs.io/
- 10X Genomics File Formats: https://support.10xgenomics.com/single-cell-gene-expression/software/pipelines/latest/output/matrices
- ISA-Tab Format: https://isa-tools.org/format/specification.html
- MLflow Documentation: https://mlflow.org/docs/latest/index.html

---

*Last updated: 2026-03-09*

______

- we look at the mitochondrial content (gene expression) because, high mitochondrial gene expression often indicates stressed or dying cells in single-cell data.
  - Healthy cells: typically <5-10% mitochondrial content
  - Dying/stressed cells: often >20% mitochondrial content
  - Helps identify low-quality cells to filter out in silver layer
