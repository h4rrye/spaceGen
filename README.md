# spaceGen

**Single-cell RNA-seq pipeline for spaceflight biology — hexagonal architecture, medallion data layers, MLflow tracking**

------

## Overview

spaceGen is an ML pipeline for analyzing NASA OSDR spaceflight single-cell transcriptomics data. It processes 10X Genomics scRNA-seq from the RRRM-1/Rodent Research-8 mission to identify how spaceflight alters gene expression at single-cell resolution across multiple tissues in the same cohort of mice.

The pipeline performs QC, normalization, clustering, cell type annotation, differential expression, and cell-cell communication network analysis using Scanpy. It classifies spaceflight vs ground control samples and identifies conserved stress-response signatures, immune dysregulation patterns, and tissue-specific molecular changes. Cross-tissue comparison reveals which spaceflight responses are systemic versus organ-specific.

The codebase uses hexagonal (ports and adapters) architecture to separate core bioinformatics and ML logic from I/O and infrastructure. The same pipeline runs locally against Parquet files during development and can be pointed at cloud storage by swapping adapters, with no changes to core logic. Data flows through a bronze/silver/gold medallion architecture, and all experiments are tracked with MLflow.

The development dataset (OSD-352) is a single-nucleus multiome study: each nucleus has both RNA-seq and ATAC-seq measured simultaneously. The current pipeline focuses on the RNA modality. The gold layer is built around MuData (Muon's multi-modal container) so that the ATAC modality can be added as a second phase without refactoring existing code. See the **Multiome Extension** section for details.

------

## Portfolio Context

This is the third project in a computational biology portfolio that follows data through chromosome structure → chromatin accessibility → gene expression:

- **[GenBrowser](https://h4rrye.github.io/genBrowser)** — 3D interactive chromosome visualization (Three.js/TypeScript). Maps biological metrics like GC content and surface distance onto chromosome backbone geometry.
- **[ChromApipe](https://github.com/h4rrye/chromApipe)** — Nextflow pipeline computing Chromosome Surface Accessible Area (CSAA) from PDB structures, with parallel API annotation from Ensembl, ENCODE, and GTEx. Dataflow architecture with Docker-containerized processes deployed to AWS Batch.
- **spaceGen** — scRNA-seq ML pipeline modeling single-cell gene expression responses to spaceflight. Hexagonal architecture with medallion data layers, network analysis, and MLflow experiment tracking.

Each project demonstrates a different architectural pattern (interactive frontend, dataflow pipeline, ports-and-adapters application) and a different layer of the biology (structure, accessibility, expression).

------

## Architecture

```mermaid
graph LR
    A[NASA OSDR] --> B[Bronze<br/>Raw count matrices]
    B --> C[Silver<br/>QC + normalized]
    C --> D[Gold<br/>Clusters + features]
    D --> E[Models<br/>Classification]
    D --> F[Networks<br/>Cell communication]
    E --> G[MLflow<br/>Tracking]
    F --> G
```

**Hexagonal design:** Core logic in `src/spacegen/core/` is pure — functions take AnnData objects and dataframes in and return them out, with no file I/O or MLflow calls. Ports (`ports/interfaces.py`) define abstract contracts for data reading, writing, and experiment logging. Adapters (`adapters/`) implement those contracts for local Parquet/h5ad and MLflow. Swapping to S3 or Databricks means adding a new adapter, not touching core code.

**Medallion layers:**

- **Bronze:** Raw gene-cell count matrices and sample metadata from NASA OSDR, partitioned by ingest date (Hive-style)
- **Silver:** QC-filtered cells, normalized counts, highly variable genes, doublet flags — versioned per tissue
- **Gold:** Clustered cells with type annotations, differential expression results, network features, study-aware splits — versioned
- **Models:** Trained classifiers and network artifacts logged to MLflow with full parameter and metric tracking

------

## Datasets

Data sourced from the **NASA Open Science Data Repository (OSDR)**. All datasets are Mus musculus, 10X Genomics scRNA-seq, spaceflight vs ground control. Using GeneLab-processed count matrices (post-alignment) as the starting point.

### Original Plan (RRRM-1/RR-8 Mission)

The original plan was to use RRRM-1/Rodent Research-8 datasets released February 2026:

| OSD     | Tissue | Factors          | Biology                                    | Status                          |
| ------- | ------ | ---------------- | ------------------------------------------ | ------------------------------- |
| OSD-910 | Spleen | Spaceflight, Age | Immune cell diversity, signaling networks  | Raw data only (no processed)    |
| OSD-905 | Liver  | Spaceflight, Age | Metabolic disruption, stress response      | Raw data only (no processed)    |
| OSD-918 | Blood  | Spaceflight, Age | Circulating immune cells, systemic markers | Raw data only (no processed)    |

**Issue:** GeneLab has not yet published processed scRNAseq count matrices for these datasets. Only raw FASTQs, metadata, and QC reports are available.

### Current Implementation (RR-3 Mission)

To build and test the pipeline architecture, we're starting with OSD-352 from the Rodent Research-3 mission, which has processed count matrices available:

| OSD     | Tissue | Data type               | Biology                                  | Status                   |
| ------- | ------ | ----------------------- | ---------------------------------------- | ------------------------ |
| OSD-352 | Brain  | snMultiome (RNA + ATAC) | Neural response, multi-omics integration | Processed data available |

OSD-352 is a single-nucleus multiome dataset: RNA-seq and ATAC-seq were captured from the same nucleus using 10X Genomics Single Cell Multiome ATAC + Gene Expression. Both modalities have processed matrices available via OSDR and the companion Mendeley Data deposit (DOI: 10.17632/fjxrcbh672.1). The study is published in Nature Communications (Masarapu et al., 2024).

**Rationale:** The current pipeline focuses on the RNA modality. The gold layer uses MuData (Muon) as its container so the ATAC modality can be added as a second phase without changing existing core logic. When RRRM-1 processed files become available, we swap the data source adapter without touching core code.

**Future Migration:** Once OSD-910, OSD-905, and OSD-918 processed data is released, we'll extend the pipeline to handle multi-tissue cross-comparison as originally planned.

------

## Multiome Extension (Phase Two)

OSD-352 contains both RNA and ATAC data from the same nuclei, which aligns directly with the portfolio's broader theme of connecting chromatin structure and accessibility to gene expression. The ATAC extension is a planned second phase after the RNA pipeline is complete.

**Why phase two and not now:** The ATAC modality requires a separate processing path (LSI dimensionality reduction, peak-barcode matrix ingestion, motif enrichment, peak-to-gene linkage). Adding both simultaneously would delay initial completion and mix concerns during early development.

**How the architecture supports it:** The gold layer stores data in a `MuData` object rather than a plain `AnnData`. RNA-only currently means `MuData` with one modality (`rna`) populated. Adding ATAC later means writing a new bronze adapter for the peak-barcode matrix, a new silver path for ATAC QC and LSI reduction, and populating the `atac` modality in the existing `MuData` at the gold layer. None of this touches RNA core logic. Ports stay the same. The extension is additive by design.

**Portfolio significance:** The completed multiome pipeline would connect chromatin accessibility (as in ChromApipe) to gene expression at single-cell resolution under spaceflight conditions, making spaceGen the synthesis point of the entire portfolio arc.

------

## Pipeline Design

The pipeline has four stages, each writing to a separate medallion layer.

The **bronze** stage ingests processed gene-cell count matrices and metadata from NASA OSDR, storing them with study provenance and Hive-style ingest date partitioning. Data integrity is verified via MD5 checksums.

The **silver** stage uses Scanpy for QC filtering (mitochondrial %, doublet removal, low-quality cells), normalization (library size correction, log transformation), highly variable gene selection, and dimensionality reduction (PCA). Batch effects are assessed and visualized.

The **gold** stage performs KNN graph construction, Leiden clustering, cell type annotation, and differential expression analysis (spaceflight vs ground within each cell type). Cross-tissue gene ID alignment and feature engineering for ML classification happen here. Cell-cell communication network analysis identifies how intercellular signaling changes under spaceflight conditions. Jaccard similarity quantifies transcriptional overlap between clusters across conditions and tissues.

The **modeling** stage trains classifiers (elastic net, XGBoost) to predict spaceflight exposure from single-cell features. All runs are logged to MLflow with parameters, metrics (AUROC, AUPRC, F1), and artifacts (UMAP plots, SHAP importance, confusion matrices, network visualizations).

------

## Analysis Highlights

- **Cell type resolution:** Identify which specific cell types (T cells, macrophages, hepatocytes, etc.) are most affected by spaceflight
- **KNN graphs + Leiden clustering:** Graph-based cell population identification at single-cell resolution
- **Cell-cell communication networks:** How intercellular signaling rewires under microgravity
- **Jaccard similarity:** Quantify transcriptional overlap between spaceflight and ground clusters to find conserved vs divergent responses
- **Cross-tissue comparison:** Systemic spaceflight signatures (shared across spleen, liver, blood) vs tissue-specific responses

------

## Current Status

Bronze, silver, and gold layers complete for OSD-352 brain tissue. Gold layer includes Leiden clustering (22 clusters), CellTypist annotation (67 cell types, validated with canonical markers), and differential expression analysis (spaceflight vs ground control per cell type). Key findings include Malat1 as a pan-cell-type spaceflight biomarker, complement pathway suppression in microglia, and 4.4x microglial enrichment in spaceflight samples. Moving to feature engineering and ML classifier.

See `docs/PROJECT_LOG.md` for detailed development history and decision tracking.

------

## Author

**Harpreet Singh** MSc Data Science, UBC Computational Biology & Machine Learning