# spaceGen Project Log

Development history and decision tracking.

---

## 2026-03-09: Project Initialization

- Created project structure with hexagonal architecture
- Identified RRRM-1/RR-8 datasets (OSD-910 spleen, OSD-905 liver, OSD-918 blood)
- Discovered RRRM-1 only has raw FASTQs — no processed count matrices
- Pivoted to OSD-352 (RR-3 brain) which has processed snRNA-seq data
- Downloaded `GLDS-352_snRNA-Seq_filtered_feature_bc_matrix.h5` (288 MB) and ISA metadata
- Discovered OSD-352 is multiome (RNA + ATAC) — planned RNA-first, ATAC as Phase 2

---

## 2026-03-10: Data Exploration (Notebook 01)

- Loaded HDF5: 32,285 genes × 32,243 cells
- Mapped barcode suffixes to samples via cell count matching:
  - Suffix 1 (1,140) → RR3_BRN_FLT_F2 (Flight)
  - Suffix 2 (5,333) → RR3_BRN_FLT_F7 (Flight)
  - Suffix 3 (5,960) → RR3_BRN_GC_G8 (Ground Control)
  - Suffix 4 (4,622) → RR3_BRN_GC_G9 (Ground Control)
  - Suffix 5 (15,188) → RR3_BRN_FLT_F1 (Flight)
- Key finding: Space Flight samples show elevated mitochondrial % (tails to ~31%)
- Sample imbalance: F1 has 15k cells (47%), F2 has 1k cells (3.5%)

---

## 2026-03-12: Bronze Layer (Notebook 02)

- Saved as Parquet (obs, var) + HDF5 (sparse CSR matrix) with Hive partitioning
- Added 8 provenance metadata fields
- Output: `data/bronze/osd352_brain/ingest_date=2026-03-12/` (~50 MB)

---

## 2026-03-25: Silver Layer (Notebook 03)

- Condition-aware QC: GC <5% mt, Flight <10% mt
- 32,243 → 27,968 cells (13.3% removed)
- Normalization: total count (10k) + log1p
- 2,000 HVGs (seurat_v3), PCA (50 components), UMAP
- No batch correction needed (UMAP shows good sample mixing)
- Sample G9 clusters separately but QC metrics normal — biological, not technical
- Output: `data/silver/osd352_brain_v1_qc.h5ad` (654 MB)

---

## 2026-04-12: Gold Layer — Clustering & DE (Notebook 04)

- Leiden clustering: 22 clusters (resolution 0.5)
- CellTypist annotation: 67 cell types (Mouse_Whole_Brain model)
- Marker validation: 21/21 canonical brain markers confirmed
- Spaceflight-enriched: Microglia 4.4x, OPCs 4.1x, VLMCs 3.7x
- DE (Wilcoxon, 11 cell types): Malat1 up across types, C1qa/C1qb down in microglia, Pcp2 down in CB Granule (logFC -3.3)
- Output: `data/gold/osd352_brain_v1_annotated.h5ad` (654 MB), `de_results.parquet` (3.2 MB)

---

## 2026-04-12: Feature Engineering (Notebook 05)

- Pseudobulk aggregation: 54 profiles (32 Flight, 22 GC) × 3,256 features
- Features: DE gene expression (3,240) + cell type proportions (11) + QC metrics (5)
- Output: `data/gold/osd352_brain_v1_features.parquet` (2.5 MB)

---

## 2026-04-13: ML Classifiers with MLflow (Notebook 06)

- LOSO-CV (5 folds, hold out entire mice)
- Elastic Net: AUROC 0.757 (best), Random Forest: 0.548, XGBoost: 0.440
- Limited accuracy (~59%) expected with n=5 biological samples
- Feature importance: Ypel3, Cox8a, Ndufs5, Ndufb7 (mitochondrial stress genes)
- All experiments tracked in MLflow

---

## 2026-04-13: GSEA (Notebook 07)

- KEGG (brainstem neurons): ALS (p=1e-12), Parkinson's, Huntington's, Alzheimer's — neurodegenerative pathway enrichment
- GO (oligodendrocytes): Translation, mitochondrial ATP synthesis, cellular respiration ALL downregulated
- GO (CB Granule): Glucose homeostasis down, calcineurin-NFAT signaling up, response to radiation up
- Convergent evidence across DE, ML, GO, KEGG strengthens biological conclusions

---

## 2026-04-13: Hexagonal Architecture Refactor

- Extracted core logic into `src/spacegen/` (core/ports/adapters)
- 18 pytest tests, all passing
- Core functions are pure and immutable (verified by tests)
- DataWriter port includes `write_json` for future D3 visualization
