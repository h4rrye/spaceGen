# spaceGen — Technical Notes & Decisions

Reference document covering key decisions, biological findings, and future plans.

---

## Dataset

**Source:** NASA Open Science Data Repository (OSDR), dataset OSD-352
**Mission:** Rodent Research-3 (RR-3)
**Tissue:** Brain (whole brain, single-nucleus)
**Organism:** Mus musculus
**Platform:** 10X Genomics snRNA-seq (Illumina)
**Comparison:** Spaceflight vs Ground Control
**Reference:** Masarapu et al., Nature Communications (2024)

OSD-352 is a multiome dataset (RNA + ATAC from same nuclei). Current pipeline uses RNA only. ATAC integration planned as Phase 2.

**Original plan:** RRRM-1/RR-8 datasets (OSD-910 spleen, OSD-905 liver, OSD-918 blood). Pivoted to OSD-352 because RRRM-1 only has raw FASTQs, no processed count matrices. Hexagonal architecture allows swapping data sources without changing core logic.

---

## Architecture

**Hexagonal (ports & adapters):** Core logic is pure — takes AnnData in, returns AnnData out, no I/O. Ports define abstract interfaces. Adapters implement concrete I/O (local files, S3, etc.). Swapping data sources = new adapter, zero core changes.

**Medallion layers:**

- Bronze: Raw counts + provenance metadata, Hive-style partitioned
- Silver: QC-filtered, normalized, HVGs, PCA/UMAP
- Gold: Clustered, annotated, DE results, ML features
- Models: MLflow-tracked classifiers

---

## Key Decisions

### Condition-Aware QC (Silver Layer)

Standard scRNA-seq QC uses uniform 5% mitochondrial threshold. For spaceflight data, this removes stressed-but-real cells from Flight samples.

**Thresholds:**

- Ground Control: <5% mt (standard)
- Space Flight: <10% mt (preserves stressed cells)
- Both: min 200 genes, min 500 UMI, max 50,000 UMI

**Result:** 13.3% cells removed. Flight lost 17%, GC lost 5.5%. The asymmetry confirms the approach.

### Pseudobulk for ML (Gold Layer)

With 27,968 cells from only 5 mice, per-cell classification would be pseudoreplication. Aggregated to sample × cell type (54 profiles). LOSO-CV holds out entire mice to prevent data leakage.

### Why Elastic Net > XGBoost

With 3,256 features and ~43 training samples per fold, tree-based models overfit and predict everything as majority class. Elastic Net's L1+L2 regularization handles high-p, low-n best. AUROC 0.757 shows features carry signal despite limited sample size.

---

## Biological Findings

### Cell Type Composition

67 cell types identified via CellTypist (Mouse_Whole_Brain model), validated with 21/21 canonical brain markers. Dominant population: cerebellar granule neurons (13,305 cells).

**Spaceflight-enriched populations:**

- Microglia: 4.4x enriched (neuroinflammation)
- OPCs: 4.1x enriched (myelin remodeling)
- VLMCs: 3.7x enriched (vascular response)

### Differential Expression

- Malat1 upregulated across most cell types (known spaceflight biomarker)
- Microglia: C1qa, C1qb downregulated (complement pathway suppression)
- Oligodendrocytes: Hsph1, Hsp90ab1, Cryab downregulated (heat shock proteins)
- CB Granule: Pcp2 strongly downregulated (logFC -3.3, motor coordination)
- Bergmann glia: Zbtb16, Sparc downregulated (neuronal differentiation)
- Astrocytes: Aldoc, Atp1b2 downregulated (metabolic disruption)

### GSEA — Neurodegenerative Pathway Enrichment

KEGG analysis of brainstem neurons: top pathways are ALL neurodegenerative diseases — ALS (p=1e-12), Parkinson's (p=6e-10), Huntington's (p=1e-7), Alzheimer's (p=3e-7). Spaceflight activates the same molecular machinery as neurodegeneration.

GO analysis of oligodendrocytes: translation, mitochondrial ATP synthesis, and cellular respiration ALL downregulated — severe metabolic stress and protein synthesis shutdown.

### Convergent Evidence

The biological story is consistent across independent methods:

1. Mitochondrial dysfunction (DE genes + GO pathways + KEGG + ML feature importance)
2. Protein homeostasis disruption (DE + GO + KEGG)
3. Neuroinflammation (DE + cell type enrichment + GO)
4. BBB compromise (GO)
5. Cell death activation (GO + KEGG)

---

## Future Plans

### Roadmap

1. ✅ Clean README, make repo public
2. Write and submit Phase 1 paper to bioRxiv
3. Build D3 interactive dashboard as companion visualization
4. Update resume and LinkedIn with preprint + live visualization
5. Phase 2: ATAC-seq integration
6. Write Phase 2 paper

### Phase 2 — ATAC Integration

New bronze adapter for peak-barcode matrix, silver path for ATAC QC + LSI reduction, MuData gold layer (RNA + ATAC combined). Connects to ChromApipe in portfolio arc.

### Phase 3 — GLM-5.1 Autonomous Optimization

After Phases 1+2 complete: autonomous hyperparameter tuning (clustering resolution, CellTypist model selection, DE thresholds) using GLM-5.1 with MLflow tracking. Requires more biological replicates for meaningful optimization.

### D3 Visualization Layer

Interactive D3.js visualizations: cell networks, UMAP clusters, pathway enrichment, feature importance. DataWriter port includes `write_json` for D3 consumption.

### Publication Strategy

Phase 1 paper (RNA-only) to bioRxiv as short communication (2,500-4,000 words). Phase 2 paper (ATAC follow-up) cites Phase 1. Two papers from one project.

Before submission: formal literature search, pseudobulk DE with DESeq2, clean figure panels.
