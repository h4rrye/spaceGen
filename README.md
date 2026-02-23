# spaceGen

**Gene expression ML pipeline for spaceflight biology — medallion architecture with MLflow tracking**

---

## Overview

spaceGen is an ML pipeline for analyzing NASA GeneLab spaceflight transcriptomics data using a medallion lakehouse pattern. The project builds on my computational biology portfolio by focusing on the expression layer: GenBrowser visualizes chromosome structure, ChromApipe computes chromatin accessibility features from ATAC-seq data, and spaceGen models gene expression from RNA-seq to predict biological exposure states and identify conserved molecular signatures.

The pipeline follows a bronze/silver/gold data architecture where raw NASA GeneLab datasets are progressively refined through QC, normalization, and feature engineering stages before ML modeling. All experiments are tracked with MLflow to maintain reproducibility and enable model versioning.

This project demonstrates production-oriented bioinformatics pipeline design with modern data engineering patterns. The medallion architecture provides clear data lineage and makes the pipeline modular and testable.

---

## Architecture

```mermaid
graph LR
    A[NASA GeneLab API] --> B[Bronze Layer<br/>Raw RNA-seq counts]
    B --> C[Silver Layer<br/>Normalized + QC'd]
    C --> D[Gold Layer<br/>ML features]
    D --> E[ML Models<br/>XGBoost, Elastic Net]
    E --> F[MLflow Registry<br/>Tracked experiments]
```

**Data Flow:**
- **Bronze:** Raw gene expression matrices and metadata from NASA GeneLab GLDS accessions
- **Silver:** Normalized counts (log-CPM or VST), filtered genes, QC metrics, outlier detection
- **Gold:** Feature-engineered tables with gene selection, pathway scores, and study-aware splits
- **Models:** Trained classifiers with hyperparameter tracking and cross-study validation
- **Registry:** MLflow experiment tracking with metrics, parameters, and model artifacts

---

## Datasets

Targeting NASA GeneLab mouse RNA-seq datasets from spaceflight versus ground control studies. The focus is on transcriptomic responses to microgravity and radiation exposure, with an emphasis on conserved stress-response pathways and immune dysregulation signatures. Dataset selection is in progress, prioritizing studies with sufficient sample sizes for cross-study validation and consistent tissue types (liver, spleen, or muscle).

---

## Pipeline Design

The pipeline consists of four stages, each writing to a separate data layer. The bronze stage ingests raw RNA-seq count matrices and metadata from GeneLab, storing them in a standardized schema with study provenance. The silver stage performs gene filtering (low-expression removal), normalization (CPM + log transformation or variance-stabilizing transformation), and quality control including library size checks, PCA-based outlier detection, and batch effect visualization. The gold stage combines harmonization and feature engineering: gene IDs are aligned across studies, batch correction is applied if needed, and features are derived through variable gene selection and optional pathway scoring (ssGSEA). The modeling stage trains elastic net logistic regression and XGBoost classifiers to predict spaceflight exposure, using leave-one-study-out cross-validation to assess generalization. All model runs are logged to MLflow with parameters (normalization method, gene filter thresholds, feature set, hyperparameters), metrics (AUROC, AUPRC, F1), and artifacts (PCA plots, SHAP importance, confusion matrices).

---

## MLflow Experiment Design

**Tracked parameters:**
- Normalization method (log-CPM, VST)
- Gene filter threshold (minimum expression, variance percentile)
- Feature selection approach (top-N variable genes, pathway-based)
- Model type and hyperparameters (regularization strength, tree depth, learning rate)

**Metrics:**
- AUROC (held-out study)
- AUPRC (held-out study)
- F1 score
- Cross-study generalization performance

**Artifacts:**
- PCA/UMAP plots for QC and batch effect visualization
- SHAP feature importance plots
- Confusion matrices
- Pathway enrichment results (if applicable)

All runs are logged to a local MLflow tracking server during development. Model artifacts and performance metrics are versioned to support reproducibility and enable comparison across feature engineering strategies.

---

## Current Status

Project is in the planning phase. Architecture and pipeline design are complete. Initial implementation will focus on data ingestion from NASA GeneLab API and bronze layer table creation. The medallion lakehouse structure is designed to support incremental development where each layer can be validated independently before moving downstream.

---

## Author

**Harpreet Singh**
MSc Data Science, UBC
Computational Biology & Machine Learning
