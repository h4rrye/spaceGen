# spaceGen Project Log

This log tracks all major decisions, changes, and development progress for the spaceGen project. Use this to maintain context across IDEs, LLMs, and development sessions.

---

## 2026-03-09: Project Initialization & Dataset Pivot

### Initial Setup
- Created project structure with hexagonal architecture design
- Identified RRRM-1/RR-8 mission datasets as primary targets:
  - OSD-910 (Spleen)
  - OSD-905 (Liver)
  - OSD-918 (Blood)
- All three tissues from same mission/cohort for clean cross-tissue comparison

### Dataset Availability Issue
**Problem:** Attempted to download processed scRNAseq count matrices from NASA OSDR AWS S3 bucket (`s3://nasa-osdr/`). Discovered that RRRM-1 datasets (released Feb 2026) only contain:
- Raw FASTQ files
- Metadata (ISA format)
- MD5 checksums
- MultiQC QC reports

**Missing:** GeneLab-processed count matrices (`.h5ad`, `filtered_feature_bc_matrix.h5`, or count matrix files). The "GeneLab Processed scRNAseq Files" sections on OSDR portal are empty for all three datasets.

### Decision: Pivot to OSD-352 for Development

**Rationale:**
1. Cannot proceed with RRRM-1 data without processed count matrices
2. Processing raw FASTQs with Cell Ranger would add significant compute/storage overhead
3. Hexagonal architecture allows data source swapping without core logic changes
4. Better to build working pipeline now, swap data later

**New Primary Dataset:**
- **OSD-352** — Brain tissue from Rodent Research-3 mission
- Has processed count matrix: `GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5`
- Spaceflight vs ground control comparison
- Mus musculus, 10X Genomics scRNA-seq

**Migration Path:**
1. Build pipeline against OSD-352 brain data
2. Validate hexagonal architecture with working implementation
3. When RRRM-1 processed data becomes available, create new adapter
4. Extend to multi-tissue analysis (spleen, liver, blood) as originally planned

### Files Downloaded
- `data/OSD-910/OSD 910 Metadata/` — metadata for future use
- `data/OSD-910/raw_multiqc_GLscRNAseq_report/` — QC report for reference

### Data Downloaded
**OSD-352 Files:**
- `GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5` (288 MB) — processed count matrix
- `OSD-352_metadata_OSD-352-ISA.zip` (107 KB) — ISA metadata
- Metadata extracted: investigation, study, assay files

**Download Method:** Direct HTTPS from OSDR portal (S3 paths didn't work, used web API instead)

### Next Steps
1. ✅ Download OSD-352 processed count matrix and metadata
2. Explore OSD-352 data structure (cell counts, genes, sample labels)
3. Implement bronze layer ingestion for `.h5` format
4. Begin silver layer QC and normalization with Scanpy

---

## Architecture Notes

### Hexagonal Design Benefits
- Core logic (QC, normalization, clustering) is pure — no I/O dependencies
- Ports define abstract interfaces for data reading/writing
- Adapters implement concrete I/O (local files, S3, Databricks)
- Swapping from OSD-352 to RRRM-1 data = new adapter, zero core changes

### Medallion Layers
- **Bronze:** Raw ingested data with provenance (ingest date, source metadata)
- **Silver:** QC-filtered, normalized, HVG-selected, versioned per dataset
- **Gold:** Clustered, annotated, DE results, network features, study-aware splits
- **Models:** Trained classifiers, MLflow tracking, artifacts

---

## Data Source Information

### NASA OSDR Access
- Portal: https://osdr.nasa.gov
- AWS S3 bucket: `s3://nasa-osdr/` (public, no auth required)
- API: https://visualization.osdr.nasa.gov/biodata/api/
- Use `--no-sign-request` flag with AWS CLI

### OSD-352 Details
- Mission: Rodent Research-3 (RR-3)
- Tissue: Brain
- Organism: Mus musculus
- Platform: 10X Genomics scRNA-seq (Illumina)
- Factors: Spaceflight vs Ground Control
- Processed file: `GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5`

### RRRM-1 Datasets (Future)
- OSD-910: Spleen (immune diversity, network analysis)
- OSD-905: Liver (metabolic disruption, stress response)
- OSD-918: Blood (circulating immune, systemic markers)
- Status: Raw data available, processed data pending GeneLab release

---

## Environment

### Dependencies
- Python 3.x
- Scanpy (scRNA-seq analysis)
- Polars (dataframes)
- MLflow (experiment tracking)
- XGBoost, scikit-learn (ML models)
- Conda environment created

### Repository Structure
```
spaceGen/
├── data/           # Raw and processed data (gitignored)
├── src/            # Source code
│   └── spacegen/
│       ├── core/       # Pure business logic
│       ├── ports/      # Abstract interfaces
│       └── adapters/   # Concrete implementations
├── notebooks/      # Exploration notebooks
├── conf/           # Configuration files
├── tests/          # Unit tests
├── docs/           # Documentation
└── reports/        # Analysis outputs
```

---

## References

- NASA OSDR: https://osdr.nasa.gov
- GeneLab Data Processing: https://www.nasa.gov/reference/osdr-data-processing-single-cell-rna-sequencing-scrna-seq/
- Scanpy Documentation: https://scanpy.readthedocs.io/
- 10X Genomics File Formats: https://support.10xgenomics.com/single-cell-gene-expression/software/pipelines/latest/output/matrices

---

*Log format: YYYY-MM-DD: Section Title — brief description of changes, decisions, and next steps*

---

## 2026-03-09: Multiome Dataset Discovery and Phase Two Decision

### OSD-352 is a Full Multiome Dataset
While reviewing the dataset, identified that OSD-352 is not RNA-only. The Masarapu et al. 2024 (Nature Communications) study used 10X Genomics Single Cell Multiome ATAC + Gene Expression, capturing RNA and ATAC from the same nuclei. Both modalities have processed matrices available:
- RNA: `GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5` (already downloaded, 288 MB)
- ATAC: peak-barcode matrix available via OSDR and Mendeley Data (DOI: 10.17632/fjxrcbh672.1)
- Analysis code: https://github.com/giacomellolab/NASA_RR3_Brain (Seurat/Signac in R)

### Decision: RNA-First, ATAC as Phase Two

**Rationale:**
1. Adding both modalities simultaneously would delay mid-March target and mix concerns during early architecture development
2. The hexagonal architecture supports additive extension: ATAC requires a new adapter and silver path, but zero changes to RNA core logic
3. Documenting the extension path explicitly in the README demonstrates architectural foresight

**Key design decision made now:** Gold layer will use `MuData` (Muon) as its container instead of plain `AnnData`. RNA-only means `MuData` with one modality (`rna`) populated. When ATAC is added, the `atac` modality slots in without refactoring.

### Portfolio Alignment
OSD-352 being multiome strengthens the portfolio arc: GenBrowser (structure) → ChromApipe (bulk chromatin accessibility) → spaceGen (single-cell RNA now, RNA+ATAC in phase two). The completed multiome version makes spaceGen the synthesis point connecting all three layers of the biology.

### Next Steps
1. Proceed with bronze layer ingestion for RNA `.h5` format
2. Keep `MuData` in mind when designing gold layer data structures
3. Document ATAC extension path in code comments as relevant sections are built

---

## 2026-03-10: OSD-352 Data Exploration Complete

### Sample Mapping Verified
Successfully mapped cell barcode suffixes to sample names using cell count matching between metadata and HDF5 file:

**Mapping (suffix → sample → condition):**
- Suffix 1 (1,140 cells) → RR3_BRN_FLT_F2 → Space Flight
- Suffix 2 (5,333 cells) → RR3_BRN_FLT_F7 → Space Flight
- Suffix 3 (5,960 cells) → RR3_BRN_GC_G8 → Ground Control
- Suffix 4 (4,622 cells) → RR3_BRN_GC_G9 → Ground Control
- Suffix 5 (15,188 cells) → RR3_BRN_FLT_F1 → Space Flight

**Total:** 32,243 cells across 5 samples (3 Flight, 2 Ground Control)

### Data Characteristics

**Gene Metadata:**
- 32,285 genes (mm10 genome)
- All features are "Gene Expression" type
- Ensembl gene IDs with genomic intervals
- Includes non-coding RNAs (5p/3p markers present)

**QC Metrics (Initial):**
- Median UMI counts: ~1,500-2,000 per cell
- Median genes detected: ~500-2,000 per cell
- Range: 31-9,553 genes, 33-74,170 UMI counts
- Some high-count outliers (potential doublets or high-quality cells)

**Key Observations:**
1. Similar QC distributions between Space Flight and Ground Control conditions
2. Significant sample imbalance: F1 has 15k cells (~47% of dataset), F2 has only 1k cells (~3.5%)
3. This is snRNA-seq (nuclear RNA), so lower counts than whole-cell RNA-seq is expected
4. No obvious batch effects visible in initial QC plots

### Sample Imbalance Considerations
The 13:1 ratio between largest (F1) and smallest (F2) samples could affect:
- Downstream clustering (F1 may dominate cluster composition)
- Differential expression power (unequal sample sizes)
- ML classifier training (need stratified sampling)

**Mitigation strategies to consider:**
- Downsample F1 for balanced analysis
- Use sample-aware normalization
- Stratify train/test splits by sample, not just condition
- Weight samples in classifier training

### Files Updated
- `notebooks/01_explore_osd352.ipynb` — completed initial exploration with condition mapping and QC visualization
- `docs/PROJECT_LOG.md` — this entry

### Mitochondrial Gene Analysis

**Key Finding:** Space Flight samples show elevated mitochondrial gene percentages compared to Ground Control:
- Both conditions: Median ~0.1-0.2% (healthy range)
- Space Flight: Notable tail extending to ~30% (stressed/dying cells)
- Ground Control: Tighter distribution, fewer high-mt cells
- Mean: 0.14% overall (within normal range for snRNA-seq)

**Biological Interpretation:**
- Elevated mitochondrial content indicates cellular stress
- Spaceflight appears to induce metabolic dysfunction in brain cells
- Some cells may be apoptotic or low-quality
- This is a real biological signal, not just technical artifact

**QC Implications for Silver Layer:**
- Standard threshold: Filter cells with >5% mitochondrial content
- May need condition-aware thresholds (more lenient for Flight samples to avoid losing real biology)
- Alternative: Keep all cells, add `high_mt` flag for downstream analysis
- Consider this as a feature for ML classifier (stress signature)

### Next Steps
1. ✅ Calculate mitochondrial gene percentage (additional QC metric)
2. ✅ Document QC thresholds for silver layer filtering (consider condition-aware approach)
3. ✅ Design bronze layer schema (provenance metadata structure)
4. ✅ Implement bronze layer ingestion notebook (`02_bronze_ingestion.ipynb`)
5. Begin silver layer QC and normalization

---

## 2026-03-12: Bronze Layer Ingestion Complete

### Bronze Layer Implementation
Created `notebooks/02_bronze_ingestion.ipynb` with step-by-step implementation following learning-focused approach. Notebook implements minimal transformations with provenance tracking.

**Transformations Applied:**
1. Made gene names unique (resolved Scanpy duplicate gene warning)
2. Added 8 provenance metadata fields to cell observations
3. Saved data in Parquet + HDF5 format with Hive-style partitioning

**Provenance Metadata Added:**
- `ingest_date`: 2026-03-12 (ingestion timestamp)
- `source_file`: Original HDF5 filename
- `dataset_id`: OSD-352
- `organism`: Mus musculus
- `tissue`: brain
- `technology`: 10X Chromium snRNA-seq
- `genome_build`: mm10
- `processing_pipeline`: GeneLab scRNA-seq

**Output Structure:**
```
data/bronze/osd352_brain/ingest_date=2026-03-12/
├── obs.parquet    # Cell metadata (32,243 cells, 14 columns)
├── var.parquet    # Gene metadata (32,285 genes, 5 columns)
└── X.h5           # Sparse count matrix (~50 MB, 97.5% sparse)
```

**Sparse Matrix Storage:**
- Format: CSR (Compressed Sparse Row) stored in HDF5
- Components: `data` (non-zero values), `indices` (column indices), `indptr` (row pointers), `shape` (dimensions)
- Compression: gzip for efficient storage
- Size: ~50 MB compressed vs ~8 GB if stored dense

### Code Style Improvements
Refactored complex one-liners to explicit multi-step code per project rules:
- Path operations broken into clear steps
- File size calculations using intermediate variables
- Sparse matrix saving with explicit component extraction
- Improved readability for learning-focused development

### Documentation Updates
- `docs/data_schema.md`: Added CSR format details and example statistics
- `docs/directory_structure.md`: Updated with actual bronze layer files and sizes
- `docs/PROJECT_LOG.md`: This entry

### Files Created/Modified
- `notebooks/02_bronze_ingestion.ipynb` — bronze layer ingestion implementation
- `data/bronze/osd352_brain/ingest_date=2026-03-12/` — bronze layer data files
- `.gitignore` — updated with Python package patterns

### Next Steps
1. Design silver layer schema (QC thresholds, normalization strategy)
2. Implement QC filtering (mitochondrial %, gene counts, UMI counts)
3. Apply normalization and HVG selection
4. Create silver layer ingestion notebook (`03_silver_qc.ipynb`)

---

## 2026-03-25: Silver Layer QC and Normalization Complete

### Condition-Aware QC Filtering
Implemented condition-aware mitochondrial thresholds to preserve biologically relevant stressed cells in Space Flight samples. A uniform 5% cutoff would remove stressed-but-real cells from Flight samples, losing biological signal.

**Thresholds:**
| Filter | Ground Control | Space Flight |
|--------|---------------|--------------|
| Min genes | 200 | 200 |
| Min UMI | 500 | 500 |
| Max UMI | 50,000 | 50,000 |
| Max mt% | 5% | 10% |

**Results:**
- Cells before QC: 32,243
- Cells after QC: 27,968 (13.3% removed)
- Space Flight: 21,661 → 17,972 (17% removed — higher due to stressed cells)
- Ground Control: 10,582 → 9,996 (5.5% removed — cleaner samples)

### Normalization Pipeline
1. Total count normalization (scale to 10,000 per cell)
2. Log1p transform (compress dynamic range)
3. HVG selection: 2,000 genes (seurat_v3 method via scikit-misc)
4. Scaling (zero mean, unit variance, clipped at 10)
5. PCA (50 components on HVGs)
6. UMAP (2D embedding)

Raw counts preserved in `adata.raw` for downstream DE analysis.

### Batch Effect Diagnostic
UMAP visualization colored by condition vs sample_id:
- Good sample mixing in main clusters → no batch correction needed
- Spaceflight-enriched clusters visible in bottom-right of UMAP → real biological signal
- Sample G9 (Ground Control) clusters somewhat separately but QC metrics are normal — biological, not technical

**Decision:** No batch correction applied. Samples mix well, separation is biological.

### Sample G9 Investigation
Sample RR3_BRN_GC_G9 clusters separately in UMAP. QC metrics compared:
- Median genes: 909 (vs 1,010-1,286 for others)
- Median UMI: 1,454 (vs 1,758-2,269 for others)
- Mt%: 0.08% (normal range)

Slightly lower counts but within acceptable range. Kept in dataset — likely biological variation between individual mice.

### File Size Issue
`sc.pp.scale()` converted sparse matrix to dense (~7 GB). Stored scaled data in `adata.layers['scaled']` and saved with gzip compression to reduce file size.

### Files Created/Modified
- `notebooks/03_silver_qc.ipynb` — silver layer QC and normalization
- `data/silver/osd352_brain_v1_qc.h5ad` — silver layer output
- `pyproject.toml` — added scikit-misc dependency
- `docs/data_schema.md` — silver layer schema documented
- `docs/directory_structure.md` — updated with silver layer
- `docs/spaceGen_notes.md` — condition-aware QC rationale
- `docs/PROJECT_LOG.md` — this entry

### Next Steps
1. ✅ Address silver layer file size (drop scaled layer, re-save — 654 MB)
2. ✅ Begin gold layer: Leiden clustering, cell type annotation
3. ✅ Differential expression analysis (spaceflight vs ground per cell type)
4. Feature engineering for ML classifier
5. Phase 3 (future): Autonomous optimization with GLM-5.1 — see `docs/spaceGen_notes.md`

---

## 2026-04-12: Gold Layer Complete — Clustering, Annotation & DE

### Leiden Clustering
- Resolution: 0.5
- Clusters found: 22
- Largest: Cluster 0 (11,890 cells), Smallest: Cluster 21 (51 cells)
- Spaceflight-dominant clusters: 7 (96%), 17 (95%), 13 (95%), 2 (95%), 8 (93%)
- Ground control-enriched: Cluster 4 (65% GC)

### CellTypist Automated Annotation
- Model: Mouse_Whole_Brain.pkl (CellTypist v1.7.1)
- Cell types identified: 67
- Method: Automated prediction + majority voting (cluster-level consensus)
- Dominant population: CB Granule Glut (13,305 cells — cerebellar granule neurons)
- Major glial types: Oligo NN (2,051), Bergmann NN, Astro-NT NN, OPC NN, Microglia NN

### Marker Gene Validation
All 21 canonical brain markers present and validated against CellTypist labels:
- Pan-neuronal (Rbfox3, Snap25, Syt1) → all neuron types
- Excitatory (Slc17a7, Neurod6) → Glut-labeled cells only
- Inhibitory (Gad1, Gad2, Slc32a1) → Gaba-labeled cells only
- Astrocytes (Gfap, Aqp4, Aldh1l1) → Astro subtypes + Bergmann
- Oligodendrocytes (Mbp, Plp1, Mog) → Oligo NN
- OPCs (Pdgfra, Cspg4) → OPC NN
- Microglia (Cx3cr1, P2ry12, Tmem119) → Microglia NN
- Endothelial (Cldn5, Pecam1) → ABC NN, VLMC NN

### Differential Expression Analysis
- Method: Wilcoxon rank-sum test (Space Flight vs Ground Control per cell type)
- Cell types tested: 11 (minimum 50 cells per condition)
- Total gene-celltype pairs: 355,135

**Spaceflight-enriched populations:**
- Microglia: 4.4x enriched (74 GC → 325 Flight)
- OPCs: 4.1x enriched (76 → 315)
- VLMCs: 3.7x enriched (51 → 191)

**Key DE findings:**
- Malat1 upregulated across most cell types — stress-responsive lncRNA, known spaceflight biomarker
- Microglia: C1qa, C1qb downregulated (complement pathway suppression)
- Oligodendrocytes: Heat shock proteins downregulated (Hsph1, Hsp90ab1, Cryab)
- CB Granule: Pcp2 strongly downregulated (logFC -3.3, cerebellar/motor coordination)
- Bergmann glia: Zbtb16, Sparc downregulated (neuronal differentiation)
- Astrocytes: Aldoc, Atp1b2 downregulated (metabolic disruption)

### Files Created/Modified
- `notebooks/04_gold_clustering.ipynb` — gold layer implementation
- `data/gold/osd352_brain_v1_annotated.h5ad` (654 MB) — annotated AnnData
- `data/gold/osd352_brain_v1_de_results.parquet` (3.2 MB) — DE results
- `pyproject.toml` — added celltypist dependency
- All docs updated

### Next Steps
1. ✅ Feature engineering for ML classifier (`05_gold_features.ipynb`)
2. Train spaceflight classifier (elastic net, XGBoost)
3. MLflow experiment tracking
4. Phase 2: ATAC-seq integration

---

## 2026-04-12: Feature Engineering Complete

### Pseudobulk Aggregation Strategy
Aggregated 27,968 cells into 54 pseudobulk profiles (sample × cell type).
This avoids pseudoreplication — cells from the same mouse are not independent observations.
A per-cell classifier would learn mouse-specific patterns, not spaceflight effects.

**Profiles:** 54 total (32 Space Flight, 22 Ground Control)
**Cell types used:** 11 (same as DE analysis, minimum 50 cells per condition)
**Minimum cells per profile:** 5

### Feature Composition (3,256 total)
1. **DE gene expression** (3,240): Mean expression of significant DE genes (adj p < 0.05, |logFC| > 0.5)
2. **Cell type proportions** (11): Fraction of each cell type per sample
3. **QC metrics** (5): Mean/median genes, UMI counts, mt% per profile

### Key Proportion Observations
- CB Granule Glut: 69-73% in GC vs 24-54% in Flight
- Microglia: 0.7-0.8% in GC vs 1.4-2.7% in Flight
- Oligo NN: Sample F2 has 16% vs 6-10% in others (sample variation)

### Files Created/Modified
- `notebooks/05_gold_features.ipynb` — feature engineering implementation
- `data/gold/osd352_brain_v1_features.parquet` (2.5 MB) — ML feature matrix
- All docs updated

### Next Steps
1. Model training with MLflow tracking (`06_model_training.ipynb`)
2. Elastic net + XGBoost classifiers
3. SHAP feature importance analysis
4. Optional: GSEA for biological interpretation

---

## 2026-04-13: Model Training Complete — MLflow Tracked

### Models Trained (LOSO-CV)
| Model | Accuracy | F1 | AUROC | Mean Fold Acc |
|-------|----------|-----|-------|---------------|
| Elastic Net | 0.574 | 0.646 | 0.757 | 0.582 ± 0.444 |
| Random Forest | 0.593 | 0.703 | 0.548 | 0.596 ± 0.294 |
| XGBoost | 0.593 | 0.744 | 0.440 | 0.600 ± 0.490 |

Best model: Elastic Net (AUROC 0.757)

### Why Performance is Limited
With only 5 biological samples (3 Flight, 2 GC), all models struggle to generalize across mice. This is a sample size limitation, not a methodology problem. LOSO-CV correctly exposes this — each fold holds out an entire mouse, and the models can't reliably predict unseen animals.

Tree-based models (RF, XGBoost) overfit and predict everything as the majority class (spaceflight). Elastic Net's L1+L2 regularization handles the high-dimensional feature space (3,256 features, ~43 training samples) most gracefully.

### Feature Importance (XGBoost)
Top features reveal biologically meaningful signals:
- Ypel3: Stress-responsive tumor suppressor (top feature)
- Cox8a, Ndufs5, Ndufb7: Mitochondrial complex genes (confirms mt stress)
- Rpl21, Rpl18: Ribosomal proteins (translational stress)
- 4 cell type proportions in top 20: CB Granule, Oligo, PGRN-PARN-MDRN, CBX MLI

### MLflow Tracking
All 3 models logged to MLflow with:
- Hyperparameters
- Metrics (accuracy, F1, AUROC)
- Confusion matrix artifacts
- Serialized models

### Files Created
- `notebooks/06_model_training.ipynb` — model training with MLflow
- `mlruns/` — MLflow experiment tracking data
- `reports/` — confusion matrix and feature importance plots

### Next Steps
1. Optional: GSEA for biological pathway interpretation
2. Phase 2: ATAC-seq integration
3. Phase 3: GLM-5.1 autonomous optimization (when more data available)

---

## 2026-04-13: Hexagonal Architecture Refactor Complete

### What Changed
Extracted reusable logic from notebooks into proper `src/spacegen/` package following hexagonal (ports & adapters) architecture.

### Package Structure
```
src/spacegen/
├── core/                    # Pure functions — no I/O
│   ├── qc.py               # condition-aware filtering, QC metrics
│   ├── normalization.py     # normalize, log1p, HVG selection
│   └── features.py          # pseudobulk aggregation, feature engineering
├── ports/
│   └── data_port.py         # DataReader, DataWriter ABCs (includes write_json for D3)
└── adapters/
    ├── h5_reader.py         # BronzeH5Reader: Parquet + HDF5 → AnnData
    ├── h5ad_reader.py       # H5adReader: .h5ad → AnnData
    └── local_writer.py      # LocalWriter: .h5ad, .parquet, .json output
```

### Test Suite
18 tests, all passing:
- `test_core_qc.py` (6 tests): QC metrics, condition-aware filtering, immutability
- `test_core_normalization.py` (6 tests): Normalization, raw preservation, HVG selection
- `test_core_features.py` (6 tests): Pseudobulk, proportions, feature merging

### Key Design Decisions
- Core functions are pure: take AnnData in, return AnnData out, no side effects
- All functions return copies — input data is never modified (verified by tests)
- DataWriter port includes `write_json` for future D3 visualization layer
- Notebooks remain as-is (narrative/documentation); `src/` is the production code
