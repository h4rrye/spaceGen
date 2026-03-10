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

**Format:** HDF5 sparse matrix
- **Shape:** (n_cells, n_genes)
- **Type:** Sparse CSR matrix (scipy.sparse.csr_matrix)
- **Values:** Raw UMI counts (integers)
- **Storage:** Compressed HDF5 for efficient sparse data storage

---

## Silver Layer

*To be documented after implementation*

---

## Gold Layer

*To be documented after implementation*

---

## Notes

- All date fields use ISO 8601 format (YYYY-MM-DD)
- Partitioning follows Hive-style conventions for compatibility with data lake tools
- Gene names are made unique in bronze layer (Scanpy requirement)
- Mitochondrial genes identified by "mt-" prefix (mouse genome convention)
