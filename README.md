# Spaceflight Gene Expression ML Pipeline  
**Cloud-native transcriptomics modeling for spaceflight and radiation biology (AWS + Databricks + MLflow)**  

---

## Overview
This project builds a reproducible, cloud-native machine learning pipeline to analyze spaceflight and radiation-related gene expression data. The system harmonizes multi-study transcriptomics datasets and trains models to predict biological exposure states while identifying conserved molecular signatures relevant to astronaut health.

**Objectives**
- Predict spaceflight or radiation exposure from gene expression  
- Identify conserved stress-response pathways across studies  
- Demonstrate production-grade bioinformatics MLOps on AWS  

**Scope**
- Organisms: _[mouse / human / cell lines]_  
- Studies: _[N]_  
- Samples: _[N]_  
- Task: _classification / regression_  

---

## Architecture

**Components**

- AWS S3 data lake (raw → bronze → silver → gold)
- Delta Lake tables for versioned lineage
- Databricks Jobs / Workflows orchestration
- MLflow Tracking + Model Registry
- Optional batch inference endpoint

---

## Datasets

| Study    | Organism    | Tissue     | Condition        | Samples | Source  |
| -------- | ----------- | ---------- | ---------------- | ------- | ------- |
| GLDS-XXX | Mouse       | Liver      | Flight vs Ground | 48      | GeneLab |
| GLDS-YYY | Human cells | Fibroblast | Radiation        | 36      | GeneLab |

**Data sources**
- NASA GeneLab (GLDS accessions)
- Ground radiation analog studies
- Public GEO datasets (if used)

---

## Problem Formulation

**Task**
- Classification: spaceflight vs ground  
or  
- Regression: radiation dose / exposure duration  

**Relevance**
Spaceflight and radiation induce immune dysregulation, DNA damage response, and mitochondrial stress. Predictive transcriptomic signatures support astronaut health risk assessment and countermeasure development.

---

## Pipeline Stages

### 1. Ingestion
- Download GeneLab datasets and metadata
- Standardize schema across studies  
**Output:** bronze Delta tables  

### 2. Preprocessing
- Gene filtering
- Normalization (e.g., CPM + log, VST)
- QC (library size, PCA, outliers)  
**Output:** study-level expression  

### 3. Harmonization
- Gene ID alignment
- Batch correction or study-aware modeling
- Study-wise splits  
**Output:** harmonized expression  

### 4. Feature Engineering
- Variable gene selection
- Pathway scores (ssGSEA / gene sets)
- Optional cell-type estimates  
**Output:** gold feature tables  

### 5. Modeling
- Elastic Net logistic regression
- Gradient boosting (XGBoost / LightGBM)
- Optional neural network  
**Output:** MLflow runs  

### 6. Evaluation
- Leave-one-study-out validation
- AUROC / AUPRC / calibration
- Cross-study generalization  
**Output:** metrics + plots  

### 7. Inference
- MLflow model registry
- Batch scoring job
- Predictions table  

---

## MLflow Experiment Design

**Tracked parameters**
- normalization method
- gene filter threshold
- feature set
- model type / hyperparameters  

**Metrics**
- AUROC
- AUPRC
- F1
- calibration error
- external study performance  

**Artifacts**
- PCA / UMAP plots
- QC reports
- SHAP importance
- pathway enrichment
- confusion matrices  

**Model lifecycle**
Staging → Production promotion based on held-out study performance.

---

## Results Summary

| Model       | AUROC (study-held-out) | AUPRC  |
| ----------- | ---------------------- | ------ |
| Elastic Net | _0.XX_                 | _0.XX_ |
| XGBoost     | _0.XX_                 | _0.XX_ |

**Key observations**
- Conserved DNA damage response activation  
- Mitochondrial pathway alteration  
- Cross-study predictive signal present  

---

## Biological Findings
- Upregulation of oxidative stress pathways  
- Immune signaling modulation  
- Mitochondrial dysfunction signature  

These signatures are consistent across independent spaceflight studies.

---

## Reproducibility & Lineage
- Delta Lake versioned tables
- MLflow run IDs for all experiments
- Config-driven pipeline
- Deterministic study splits
- Fully scripted ETL and modeling

---

## How to Run

### Databricks
1. Import repository
2. Configure cluster
3. Run workflow jobs in order:
   - `01_ingest`
   - `02_preprocess`
   - `03_harmonize`
   - `04_features`
   - `05_train`
   - `06_evaluate`

### Local (optional)
```bash
pip install -r requirements.txt
python pipelines/01_ingest.py
python pipelines/02_preprocess.py
python pipelines/03_harmonize.py
python pipelines/04_features.py
python pipelines/05_train.py
python pipelines/06_evaluate.py
```

## Repository Structure

pipelines/
configs/
notebooks/
tests/
docs/

## **Configuration**





Pipeline behavior is controlled via YAML configs:



- normalization method
- gene filtering thresholds
- feature selection
- model hyperparameters
- split strategy





------





## **Validation Strategy**





- Leave-one-study-out cross-validation
- No sample leakage across studies
- External dataset evaluation
- Optional cross-species testing

## **Limitations**





- Limited sample sizes
- Cross-study heterogeneity
- Species and tissue differences
- Variable sequencing protocols





------





## **Future Work**





- Multi-omics integration (proteomics / metabolomics)
- Radiation dose modeling
- Cross-species transfer learning
- Longitudinal exposure prediction





------





## **Citation**





NASA GeneLab datasets and associated publications.

Additional GEO studies where applicable.



------





## **Author**





Harpreet Singh

MSc Data Science, UBC

Computational Biology & Machine Learning



------





## **Positioning**





Cloud-native transcriptomics ML pipeline for spaceflight biology with cross-study generalization and MLflow-tracked reproducibility.

