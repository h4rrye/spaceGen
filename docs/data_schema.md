# spaceGen Data Schema

Documentation of data structures, column definitions, and schemas across medallion layers.

---

## Bronze Layer

### Structure
```
data/bronze/{dataset}_{tissue}/ingest_date={YYYY-MM-DD}/
  ├── obs.parquet          # Cell metadata + provenance
  ├── var.parquet          # Gene metadata
  └── X.h5                 # Sparse count matrix
```

### obs.parquet (Cell Metadata)

**Original columns from source data:**
- `sample_id` (str) - Cell barcode suffix (1-5)
- `sample_name` (str) - Sample identifier (e.g., "RR3_BRN_FLT_F1")
- `condition` (str) - Experimental condition ("Space Flight" or "Ground Control")
- `n_genes_by_counts` (int) - Number of genes detected per cell
- `total_counts` (int) - Total UMI counts per cell
- `pct_counts_mt` (float) - Percentage of mitochondrial gene counts

**Provenance columns (added during bronze ingestion):**
- `ingest_date` (str) - Date when data was ingested (YYYY-MM-DD format)
- `source_file` (str) - Original source filename
- `dataset_id` (str) - Dataset identifier (e.g., "OSD-352")
- `organism` (str) - Species name (e.g., "Mus musculus")
- `tissue` (str) - Tissue type (e.g., "brain")
- `technology` (str) - Sequencing technology (e.g., "10X Chromium snRNA-seq")
- `genome_build` (str) - Reference genome version (e.g., "mm10")
- `processing_pipeline` (str) - Data processing pipeline (e.g., "GeneLab scRNA-seq")

### var.parquet (Gene Metadata)

**Columns:**
- `gene_ids` (str) - Ensembl gene IDs
- `feature_types` (str) - Feature type (all "Gene Expression" for RNA)
- `genome` (str) - Genome build (e.g., "mm10")
- `interval` (str) - Genomic coordinates (chromosome:start-end:strand)
- `mt` (bool) - Mitochondrial gene flag (True if gene name starts with "mt-")

**Note:** Gene names (index) are made unique during bronze ingestion to resolve duplicates.

### X.h5 (Count Matrix)

**Format:** HDF5 sparse matrix stored in CSR (Compressed Sparse Row) format
- **Shape:** (n_cells, n_genes)
- **Type:** Sparse CSR matrix (scipy.sparse.csr_matrix)
- **Values:** Raw UMI counts (integers)
- **Storage:** Compressed HDF5 with gzip compression

**CSR Components:**
- `data` (array) - Non-zero values from the sparse matrix
- `indices` (array) - Column indices for each non-zero value
- `indptr` (array) - Index pointers marking row boundaries
- `shape` (tuple) - Matrix dimensions (n_cells, n_genes)

**Example for OSD-352:**
- Shape: (32,243 cells, 32,285 genes)
- Sparsity: ~97.5% zeros (typical for scRNA-seq)
- File size: ~50 MB compressed (vs ~8 GB if stored dense)

---

## Silver Layer

### Structure
```
data/silver/
  └── osd352_brain_v1_qc.h5ad    # Complete AnnData object
```

### Format: AnnData (.h5ad)

Single file containing all data and metadata in AnnData format.

**adata.X** — Normalized expression matrix (sparse CSR)
- Shape: (27,968 cells, 32,285 genes)
- Values: Total count normalized (10k per cell) + log1p transformed

**adata.raw** — Raw counts preserved for DE analysis
- Shape: (27,968 cells, 32,285 genes)
- Values: Original UMI counts (pre-normalization)

**adata.obs** — Cell metadata columns:
- `ingest_date` (str) — Bronze layer provenance
- `source_file` (str) — Original source filename
- `dataset_id` (str) — Dataset identifier (OSD-352)
- `organism` (str) — Mus musculus
- `tissue` (str) — brain
- `technology` (str) — 10X Chromium snRNA-seq
- `genome_build` (str) — mm10
- `processing_pipeline` (str) — GeneLab scRNA-seq
- `sample_id` (str) — Barcode suffix (1-5)
- `sample_name` (str) — Sample identifier (e.g., RR3_BRN_FLT_F1)
- `condition` (str) — Space Flight or Ground Control
- `n_genes_by_counts` (int) — Genes detected per cell
- `total_counts` (float) — Total UMI counts per cell
- `pct_counts_mt` (float) — Mitochondrial gene percentage

**adata.var** — Gene metadata columns:
- `gene_ids` (str) — Ensembl gene IDs
- `feature_types` (str) — Gene Expression
- `genome` (str) — mm10
- `interval` (str) — Genomic coordinates
- `mt` (bool) — Mitochondrial gene flag
- `highly_variable` (bool) — HVG flag (2,000 genes selected)

**adata.obsm** — Embeddings:
- `X_pca` — PCA coordinates (50 components, computed on HVGs)
- `X_umap` — UMAP coordinates (2D)

**adata.layers** — (empty after file size optimization; scaled data dropped, PCA/UMAP preserved in obsm)

### QC Thresholds Applied (Condition-Aware)

| Filter | Ground Control | Space Flight | Rationale |
|--------|---------------|--------------|-----------|
| Min genes | 200 | 200 | Removes empty/low-quality droplets |
| Min UMI | 500 | 500 | Removes debris (standard for snRNA-seq) |
| Max UMI | 50,000 | 50,000 | Removes likely doublets |
| Max mt% | 5% | 10% | Flight: preserves stressed cells (real biology) |

**Filtering result:** 32,243 → 27,968 cells (13.3% removed)

---

## Gold Layer

### Structure
```
data/gold/
  ├── osd352_brain_v1_annotated.h5ad    # Annotated AnnData object
  └── osd352_brain_v1_de_results.parquet # DE results table
```

### Format: AnnData (.h5ad) — osd352_brain_v1_annotated.h5ad

Extends silver layer with clustering, cell type annotations, and DE results.

**adata.X** — Normalized expression matrix (sparse CSR, same as silver)

**adata.obs** — Cell metadata (all silver columns plus):
- `leiden_0.5` (str) — Leiden cluster ID (22 clusters, resolution=0.5)
- `predicted_labels` (str) — CellTypist per-cell prediction
- `over_clustering` (str) — CellTypist over-clustering labels
- `majority_voting` (str) — CellTypist consensus label (cluster-level majority vote)
- `cell_type` (str) — Final cell type label (from majority_voting)

**adata.var** — Gene metadata (same as silver)

**adata.obsm** — Embeddings (same as silver: X_pca, X_umap)

**adata.uns** — Unstructured metadata:
- `de_spaceflight_vs_ground` — DE analysis metadata (method, comparison, cell types tested)

### Annotation Details
- **Model:** CellTypist Mouse_Whole_Brain.pkl
- **Method:** Automated prediction + majority voting (cluster-level consensus)
- **Cell types found:** 67
- **Validation:** Canonical brain markers (21/21 present, validated via dotplot)

### DE Results — osd352_brain_v1_de_results.parquet

**Columns:**
- `names` (str) — Gene name
- `scores` (float) — Wilcoxon test statistic
- `logfoldchanges` (float) — Log fold change (Space Flight vs Ground Control)
- `pvals` (float) — Raw p-value
- `pvals_adj` (float) — Adjusted p-value (Benjamini-Hochberg)
- `cell_type` (str) — Cell type tested

**Details:**
- Method: Wilcoxon rank-sum test
- Comparison: Space Flight vs Ground Control (within each cell type)
- Cell types tested: 11 (minimum 50 cells per condition)
- Total gene-celltype pairs: 355,135

### Key Findings

**Spaceflight-enriched cell populations:**
- Microglia: 4.4x enriched in spaceflight (neuroinflammation)
- OPCs: 4.1x enriched (myelin remodeling)
- VLMCs: 3.7x enriched (vascular response)

**Recurring DE signatures:**
- Malat1 upregulated across most cell types (stress-responsive lncRNA, known spaceflight biomarker)
- Gm42418 downregulated across types (ribosomal RNA processing, translational stress)

**Cell-type specific:**
- Microglia: C1qa, C1qb downregulated (complement pathway suppression)
- Oligodendrocytes: Heat shock proteins (Hsph1, Hsp90ab1, Cryab) downregulated
- CB Granule neurons: Pcp2 strongly downregulated (cerebellar function/motor coordination)
- Bergmann glia: Zbtb16, Sparc downregulated (neuronal differentiation, synaptic plasticity)
- Astrocytes: Aldoc, Atp1b2 downregulated (metabolic and ion transport disruption)

### ML Feature Matrix — osd352_brain_v1_features.parquet

Pseudobulk feature matrix for ML classifier training.

**Aggregation:** Per sample × cell type (avoids pseudoreplication)

**Metadata columns:**
- `sample_name` (str) — Sample identifier
- `cell_type` (str) — Cell type label
- `condition` (str) — Space Flight or Ground Control
- `n_cells` (int) — Number of cells in this pseudobulk profile
- `label` (int) — Binary label (1 = Space Flight, 0 = Ground Control)

**Feature columns (3,256 total):**
- `expr_{gene}` (float) — Mean expression of 3,240 significant DE genes per profile
- `prop_{cell_type}` (float) — 11 cell type proportion features per sample
- `qc_mean_genes` (float) — Mean genes detected per profile
- `qc_mean_counts` (float) — Mean UMI counts per profile
- `qc_mean_mt_pct` (float) — Mean mitochondrial % per profile
- `qc_median_genes` (float) — Median genes detected per profile
- `qc_median_counts` (float) — Median UMI counts per profile

**Details:**
- Rows: 54 pseudobulk profiles (32 Space Flight, 22 Ground Control)
- Minimum 5 cells per sample × cell type combination
- Cell types: 11 (same as DE analysis)
- File size: 2.5 MB

---

## Notes

- All date fields use ISO 8601 format (YYYY-MM-DD)
- Partitioning follows Hive-style conventions for compatibility with data lake tools
- Gene names are made unique in bronze layer (Scanpy requirement)
- Mitochondrial genes identified by "mt-" prefix (mouse genome convention)
