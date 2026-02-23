# spaceGen

**Gene expression ML pipeline for spaceflight biology — hexagonal architecture, medallion data layers, MLflow tracking**

---

## Overview

spaceGen is an ML pipeline for analyzing NASA GeneLab spaceflight transcriptomics data. It predicts biological exposure states from RNA-seq gene expression and identifies conserved molecular signatures relevant to astronaut health — stress-response pathways, immune dysregulation, and mitochondrial dysfunction.

The pipeline follows a bronze/silver/gold medallion data architecture where raw NASA GeneLab datasets are progressively refined through QC, normalization, and feature engineering before ML modeling. All experiments are tracked with MLflow for reproducibility and model versioning.

The codebase uses hexagonal (ports and adapters) architecture to separate core ML and bioinformatics logic from I/O and infrastructure. This means the same pipeline runs locally against Parquet files during development and can be pointed at cloud storage or Databricks by swapping adapters — no changes to core logic required.

---

## Portfolio Context

This is the third project in a computational biology portfolio that follows data through chromosome structure → chromatin accessibility → gene expression:

- **[GenBrowser](https://h4rrye.github.io/genBrowser)** — 3D interactive chromosome visualization (Three.js/TypeScript). Maps biological metrics like GC content and surface distance onto chromosome backbone geometry.
- **[ChromApipe](https://github.com/h4rrye/chromApipe)** — Nextflow pipeline computing Chromosome Surface Accessible Area (CSAA) from PDB structures, with parallel API annotation from Ensembl, ENCODE, and GTEx. Dataflow architecture with Docker-containerized processes.
- **spaceGen** — ML pipeline modeling gene expression responses to spaceflight. Hexagonal architecture with medallion data layers and MLflow experiment tracking.

Each project demonstrates a different architectural pattern (interactive frontend, dataflow pipeline, ports-and-adapters application) and a different layer of the biology (structure, accessibility, expression).

---

## Architecture

```mermaid
graph LR
    A[NASA GeneLab API] --> B[Bronze<br/>Raw counts]
    B --> C[Silver<br/>Normalized + QC'd]
    C --> D[Gold<br/>ML features]
    D --> E[Models<br/>XGBoost · Elastic Net]
    E --> F[MLflow<br/>Tracking + Registry]
```

**Hexagonal design:** Core logic in `src/spacegen/core/` is pure — functions take dataframes in and return dataframes out, with no file I/O or MLflow calls. Ports (`ports/interfaces.py`) define abstract contracts for data reading, writing, and experiment logging. Adapters (`adapters/`) implement those contracts for local Parquet and MLflow. Swapping to S3 or Databricks means adding a new adapter, not touching core code.

**Medallion layers:**
- **Bronze:** Raw gene expression matrices and metadata ingested from NASA GeneLab GLDS accessions, partitioned by ingest date
- **Silver:** Normalized counts (log-CPM or VST), filtered genes, QC metrics, outlier flags — versioned
- **Gold:** Feature-engineered tables with variable gene selection, pathway scores, and study-aware splits — versioned
- **Models:** Trained classifiers logged to MLflow with full parameter and metric tracking

---

## Datasets

Targeting NASA GeneLab mouse RNA-seq datasets from spaceflight versus ground control studies, starting with OSD-47 (mouse liver, spaceflight vs ground). The focus is on transcriptomic responses to microgravity and radiation exposure, prioritizing studies with sufficient sample sizes for cross-study validation and consistent tissue types.

---

## Pipeline Design

The pipeline has four stages, each writing to a separate medallion layer. The bronze stage ingests raw RNA-seq count matrices and metadata from GeneLab, storing them with study provenance and Hive-style ingest date partitioning. The silver stage performs gene filtering, normalization (CPM + log or VST), and quality control including library size checks, PCA-based outlier detection, and batch effect visualization. The gold stage handles harmonization and feature engineering together: gene ID alignment across studies, batch correction where needed, variable gene selection, and optional pathway scoring via ssGSEA. The modeling stage trains elastic net logistic regression and XGBoost classifiers to predict spaceflight exposure, validated with leave-one-study-out cross-validation. All runs are logged to MLflow with parameters, metrics (AUROC, AUPRC, F1), and artifacts (PCA plots, SHAP importance, confusion matrices).

---

## Current Status

Architecture and pipeline design are complete. The hexagonal code structure is in place with ports, adapters, and core modules. Initial medallion directory structure is set up with OSD-47 as the first dataset. Implementation is starting with data ingestion from the NASA GeneLab API and bronze layer table creation.

---

## Author

**Harpreet Singh**
MSc Data Science, UBC
Computational Biology & Machine Learning