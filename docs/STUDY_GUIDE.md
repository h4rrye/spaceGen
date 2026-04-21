# spaceGen — Complete Project Study Guide

A detailed walkthrough of every decision, method, and finding in the spaceGen project.
Use this to prepare for technical interviews about single-cell genomics, ML pipelines,
and software architecture.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Dataset Selection & Pivot](#2-dataset-selection--pivot)
3. [Architecture Design](#3-architecture-design)
4. [Data Exploration](#4-data-exploration)
5. [Bronze Layer](#5-bronze-layer)
6. [Silver Layer — QC & Normalization](#6-silver-layer--qc--normalization)
7. [Gold Layer — Clustering & Annotation](#7-gold-layer--clustering--annotation)
8. [Gold Layer — Differential Expression](#8-gold-layer--differential-expression)
9. [Feature Engineering](#9-feature-engineering)
10. [ML Classification](#10-ml-classification)
11. [GSEA — Pathway Enrichment](#11-gsea--pathway-enrichment)
12. [Hexagonal Architecture & Testing](#12-hexagonal-architecture--testing)
13. [D3 Visualization](#13-d3-visualization)
14. [Key Biological Findings](#14-key-biological-findings)
15. [Future Work](#15-future-work)
16. [Interview Talking Points](#16-interview-talking-points)

---

## 1. Project Overview

### What is spaceGen?

spaceGen is an end-to-end single-cell RNA-seq analysis pipeline that identifies how
spaceflight alters gene expression in mouse brain tissue at single-cell resolution.

### The Scientific Question

"Does spaceflight induce cell-type-specific molecular changes in the brain, and do
these changes overlap with known disease pathways?"

### The Answer We Found

Yes. Spaceflight activates neurodegenerative disease pathways (ALS, Parkinson's,
Huntington's, Alzheimer's) in brainstem neurons, causes metabolic collapse in
oligodendrocytes, and triggers neuroinflammation via microglial expansion.

### Pipeline Flow

```
NASA OSDR (OSD-352)
    │
    ▼
┌───────── ┐    ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌──────┐
│Bronze    │───▶│ Silver  │───▶│  Gold   │───▶│ Models  │───▶│ GSEA │
│Raw +     │    │ QC +    │    │ Clusters│    │ Elastic │    │ GO + │
│Provenance│    │Normalize│    │+ DE     │    │ Net +   │    │ KEGG │
└ ─────────┘    └─────────┘    └─────────┘    │ XGBoost │    └──────┘
                                              └─────────┘
                                                  │
                                              ┌───▼───┐
                                              │MLflow │
                                              └───────┘
```

### Tech Stack

| Category | Tools |
|----------|-------|
| scRNA-seq | Scanpy, AnnData, CellTypist |
| Data | Parquet, HDF5, h5ad |
| ML | scikit-learn, XGBoost, MLflow |
| Pathway | GSEApy (GO, KEGG) |
| Validation | Pydantic, pytest |
| Visualization | D3.js, Matplotlib |
| Architecture | Hexagonal (ports & adapters), Medallion layers |

---

## 2. Dataset Selection & Pivot

### Original Plan

We originally targeted RRRM-1/RR-8 mission datasets from NASA OSDR:
- OSD-910 (Spleen) — immune cell diversity
- OSD-905 (Liver) — metabolic disruption
- OSD-918 (Blood) — circulating immune markers

These would have enabled cross-tissue comparison of spaceflight effects.

### Why We Pivoted

GeneLab had not yet published processed count matrices for RRRM-1. Only raw FASTQs
were available. Processing raw FASTQs with Cell Ranger would require significant
compute and was outside the project scope.

### What We Used Instead

**OSD-352** — Rodent Research-3 mission, mouse brain tissue.
- 32,243 cells (single-nucleus RNA-seq)
- 32,285 genes (mm10 genome)
- 5 samples: 3 Space Flight, 2 Ground Control
- Published: Masarapu et al., Nature Communications (2024)
- Bonus: It's a multiome dataset (RNA + ATAC from same nuclei)

### Why This Decision Matters

**Interview answer:** "The hexagonal architecture made the pivot painless. Core logic
doesn't know where data comes from — it takes AnnData in and returns AnnData out.
When RRRM-1 processed data becomes available, we write a new adapter and the entire
pipeline works without changing a single core function."

---

## 3. Architecture Design

### Hexagonal Architecture (Ports & Adapters)

```
                    ┌─────────────────────┐
                    │                     │
    ┌───────┐       │   CORE (Pure)       │       ┌───────────┐
    │Bronze │       │                     │       │  MLflow   │
    │H5     │──▶ Port ──▶ qc.py           │       │  Logger   │
    │Reader │       │      normalization  │       └───────────┘
    └───────┘       │      features       │            ▲
                    │                     │            │
    ┌───────┐       │                     │       ┌────┴──────┐
    │ h5ad  │──▶ Port ──▶ (same core)  Port ──▶   │  Local    │
    │Reader │       │                     │       │  Writer   │
    └───────┘       │                     │       └───────────┘
                    │   Pydantic Models   │
                    │   (validation)      │
                    └─────────────────────┘
```

### Why Hexagonal?

1. **Testability:** Core functions are pure — no mocking needed. Pass in test data, assert output.
2. **Swappability:** Same pipeline runs on local files or cloud storage. Change adapter, not logic.
3. **Separation of concerns:** QC logic doesn't know about file formats. Normalization doesn't know about MLflow.

### Medallion Data Layers

```
┌────────── ┐    ┌──────────┐     ┌──────────┐     ┌────────── ┐
│  Bronze   │───▶│  Silver  │────▶│   Gold   │────▶│  Models   │
│           │    │          │     │          │     │           │
│ Raw +     │    │ QC +     │     │Clusters  │     │Classifiers│
│ Provenance│    │ Normalize│     │+ Cell    │     │+ MLflow   │
│           │    │ + HVGs   │     │  Types   │     │           │
│ Parquet   │    │          │     │+ DE      │     │           │
│ + HDF5    │    │  .h5ad   │     │+ Features│     │  .pkl     │
└────────── ┘    └──────────┘     └──────────┘     └────────── ┘
```

### Why Medallion?

Each layer has a clear contract:
- **Bronze:** Immutable raw data. If something goes wrong downstream, you can always rebuild from bronze.
- **Silver:** Cleaned data. QC decisions are documented and reproducible.
- **Gold:** Analysis-ready. Multiple consumers (ML, GSEA, visualization) read from the same gold layer.

**Interview answer:** "Medallion architecture gives us lineage and reproducibility.
Every transformation is versioned. If a reviewer questions our QC thresholds, we
re-run silver from bronze with different parameters — gold and models rebuild automatically."

---

## 4. Data Exploration

### What We Learned (Notebook 01)

**Cell barcode mapping:** 10X Genomics appends a suffix (1-5) to cell barcodes to
distinguish samples multiplexed in the same run. We matched suffix → sample name
by comparing cell counts between the HDF5 file and the ISA metadata.

| Suffix | Cells | Sample | Condition |
|--------|-------|--------|-----------|
| 1 | 1,140 | RR3_BRN_FLT_F2 | Space Flight |
| 2 | 5,333 | RR3_BRN_FLT_F7 | Space Flight |
| 3 | 5,960 | RR3_BRN_GC_G8 | Ground Control |
| 4 | 4,622 | RR3_BRN_GC_G9 | Ground Control |
| 5 | 15,188 | RR3_BRN_FLT_F1 | Space Flight |

**Key observation:** Sample F1 has 47% of all cells. This imbalance matters for ML
(need stratified sampling) and clustering (F1 could dominate cluster composition).

**Mitochondrial finding:** Space Flight samples show elevated mt% (tails to ~31%).
This is cellular stress from microgravity — not a technical artifact. This observation
directly informed our condition-aware QC strategy.

---

## 5. Bronze Layer

### What It Does

Ingests the raw 10X HDF5 file and saves it in a structured format with provenance metadata.

### Format

```
data/bronze/osd352_brain/ingest_date=2026-03-12/
├── obs.parquet    # Cell metadata (32,243 rows)
├── var.parquet    # Gene metadata (32,285 rows)
└── X.h5           # Sparse count matrix (CSR format, ~50 MB)
```

### Why CSR Format?

scRNA-seq data is ~97.5% zeros. Storing as dense matrix = ~8 GB. CSR (Compressed
Sparse Row) stores only non-zero values + their positions = ~50 MB.

CSR has three arrays:
- `data`: non-zero values
- `indices`: column index for each non-zero value
- `indptr`: pointer to where each row starts in `data`

### Why Hive-Style Partitioning?

`ingest_date=2026-03-12/` follows Hive convention. This means:
- Multiple ingestion runs can coexist
- Data lake tools (Spark, Polars) can read partitions natively
- You can always trace which raw data produced which downstream results

### Provenance Metadata

8 fields added to every cell: ingest_date, source_file, dataset_id, organism,
tissue, technology, genome_build, processing_pipeline. This is data lineage —
you can always answer "where did this cell come from?"

---

## 6. Silver Layer — QC & Normalization

### Condition-Aware QC (The Key Decision)

Standard scRNA-seq QC applies a uniform 5% mitochondrial threshold. We used
different thresholds per condition:

| Filter | Ground Control | Space Flight | Why |
|--------|---------------|--------------|-----|
| Min genes | 200 | 200 | Removes empty droplets |
| Min UMI | 500 | 500 | Removes debris (snRNA-seq has lower counts) |
| Max UMI | 50,000 | 50,000 | Removes doublets (max was ~74k) |
| Max mt% | 5% | 10% | Flight: preserves stressed cells |

**Why condition-aware?** A uniform 5% cutoff would remove stressed-but-real cells
from Flight samples. These cells ARE the biology we're studying. Ground Control
cells above 5% are more likely technical artifacts.

**Result:** 32,243 → 27,968 cells (13.3% removed). Flight lost 17%, GC lost 5.5%.
The asymmetry confirms the approach was correct.

### Normalization Pipeline

```
Raw counts → Total count normalization (10k per cell) → log1p transform
```

**Why normalize?** Cells are sequenced to different depths (library size variation).
Without normalization, a gene appears "more expressed" in deeply-sequenced cells
even if the biological expression is identical.

**Why log1p?** Gene expression follows a power law — a few genes are very highly
expressed, most are low. Log transform compresses this range so highly expressed
genes don't dominate PCA and clustering.

### HVG Selection

Selected 2,000 most variable genes using Seurat v3 method. These are genes that
actually differ between cells — the biological signal. The other ~30k genes are
housekeeping or noise.

### Batch Effect Assessment

UMAP colored by sample_id vs condition showed good mixing across samples in most
clusters. No batch correction needed. Sample G9 clustered somewhat separately but
QC metrics were normal — biological variation between individual mice.

**Interview answer:** "I assessed batch effects visually via UMAP and quantitatively
by checking QC metrics per sample. The samples mixed well, so I didn't apply batch
correction. Applying it unnecessarily can remove real biological signal."

---

## 7. Gold Layer — Clustering & Annotation

### Leiden Clustering

- Algorithm: Leiden (improvement over Louvain — guarantees connected communities)
- Resolution: 0.5 (moderate — gives 10-20 clusters for brain tissue)
- Result: 22 clusters

### CellTypist Annotation

- Model: Mouse_Whole_Brain.pkl (pre-trained on mouse brain atlas)
- Method: Automated prediction + majority voting
- Majority voting: Cells in the same Leiden cluster get the most common label,
  reducing noise from per-cell predictions
- Result: 67 cell types identified

### Marker Gene Validation

We validated CellTypist labels against 21 canonical brain markers:

| Cell Type | Markers | Confirmed? |
|-----------|---------|------------|
| Pan-neuronal | Rbfox3, Snap25, Syt1 | ✅ All neuron types |
| Excitatory | Slc17a7, Neurod6 | ✅ Glut cells only |
| Inhibitory | Gad1, Gad2, Slc32a1 | ✅ Gaba cells only |
| Astrocytes | Gfap, Aqp4, Aldh1l1 | ✅ Astro subtypes |
| Oligodendrocytes | Mbp, Plp1, Mog | ✅ Oligo NN |
| OPCs | Pdgfra, Cspg4 | ✅ OPC NN |
| Microglia | Cx3cr1, P2ry12, Tmem119 | ✅ Microglia NN |
| Endothelial | Cldn5, Pecam1 | ✅ ABC/VLMC NN |

21/21 markers confirmed. This is critical for credibility — it shows we don't
blindly trust automated tools.

**Interview answer:** "I used CellTypist for initial annotation and validated
against canonical markers via dotplot. Automated tools are efficient but not
infallible — the validation step is what gives confidence in the labels."

### Spaceflight-Enriched Cell Populations

| Cell Type | GC Cells | Flight Cells | Enrichment |
|-----------|----------|-------------|------------|
| Microglia | 74 | 325 | 4.4× |
| OPCs | 76 | 315 | 4.1× |
| VLMCs | 51 | 191 | 3.7× |
| Astro-NT | 149 | 315 | 2.1× |

Microglia are the brain's immune cells. 4.4× enrichment = neuroinflammation.

---

## 8. Gold Layer — Differential Expression

### Method

Wilcoxon rank-sum test, spaceflight vs ground control, within each cell type.
11 cell types had ≥50 cells in both conditions.

### Key DE Findings

| Gene | Cell Type | logFC | Significance |
|------|-----------|-------|-------------|
| Malat1 | Most types | +0.3 to +1.1 | Pan-cell-type spaceflight biomarker |
| C1qa | Microglia | -2.5 | Complement pathway suppression |
| C1qb | Microglia | -2.1 | Complement pathway suppression |
| Pcp2 | CB Granule | -3.3 | Cerebellar motor coordination |
| Hsph1 | Oligo NN | -2.1 | Heat shock protein (protein folding) |
| Hsp90ab1 | Oligo NN | -1.8 | Heat shock protein |
| Cryab | Oligo NN | -1.9 | Heat shock protein |
| Aldoc | Astro-NT | -2.7 | Metabolic enzyme |

### Why Malat1 Matters

Malat1 is a long non-coding RNA that's upregulated under cellular stress. It's a
known spaceflight biomarker — its appearance across nearly all cell types validates
our analysis pipeline and confirms the cells are genuinely responding to spaceflight.

### Why Complement Suppression Matters

C1qa and C1qb initiate the complement cascade — part of the innate immune system.
In the brain, complement is critical for synaptic pruning. Suppression under
spaceflight suggests altered immune surveillance, potentially allowing damaged
synapses to persist.

---

## 9. Feature Engineering

### The Pseudoreplication Problem

We have 27,968 cells but only 5 biological samples (mice). If we train a classifier
on individual cells, cells from the same mouse are not independent — the model
learns mouse-specific patterns, not spaceflight effects.

```
WRONG: 27,968 "samples" → model learns mouse identity
RIGHT: 54 pseudobulk profiles → model learns spaceflight biology
```

### Pseudobulk Aggregation

For each sample × cell type combination, compute mean expression:
- 5 samples × 11 cell types = ~55 profiles (54 after filtering)
- Each profile is a biologically meaningful unit

### Feature Types

| Type | Count | What It Captures |
|------|-------|-----------------|
| DE gene expression | 3,240 | Transcriptional differences |
| Cell type proportions | 11 | Compositional changes (e.g., 4.4× microglia) |
| QC metrics | 5 | Transcriptional activity, cell health |
| **Total** | **3,256** | |

### Why These Features?

- **DE genes:** Biologically motivated — these are the genes that actually differ
  between conditions. Not random features.
- **Proportions:** Spaceflight changes cell composition. The 4.4× microglia
  enrichment is itself a strong classifier feature.
- **QC metrics:** Mean genes/UMI/mt% capture overall transcriptional activity
  differences between conditions.

---

## 10. ML Classification

### LOSO-CV (Leave-One-Sample-Out Cross-Validation)

With 5 samples, standard k-fold CV would leak information — profiles from the
same mouse could appear in both train and test. LOSO-CV holds out ALL profiles
from one mouse at a time.

```
Fold 1: Train on S2,S3,S4,S5 → Test on S1 (all 11 profiles from mouse F1)
Fold 2: Train on S1,S3,S4,S5 → Test on S2 (all 10 profiles from mouse F2)
...
Fold 5: Train on S1,S2,S3,S4 → Test on S5 (all 11 profiles from mouse G9)
```

### Results

| Model | Accuracy | F1 | AUROC | Why This Performance |
|-------|----------|-----|-------|---------------------|
| Elastic Net | 0.574 | 0.646 | **0.757** | L1+L2 handles high-p, low-n best |
| Random Forest | 0.593 | 0.703 | 0.548 | Overfits, predicts majority class |
| XGBoost | 0.593 | 0.744 | 0.440 | Memorizes training, fails on held-out |

### Why Elastic Net Wins

Counter-intuitive but expected. With 3,256 features and ~43 training samples per
fold, tree-based models overfit. Elastic Net's L1 regularization zeros out
irrelevant features (automatic feature selection). Its simplicity is its strength.

### Why Performance Is Limited

**n=5 biological samples.** This is the fundamental limitation — not methodology.
LOSO-CV correctly exposes this. The AUROC of 0.757 shows the features carry signal,
but robust classification needs more biological replicates.

### Feature Importance

Top XGBoost features validate the biology:
- **Ypel3:** Stress-responsive tumor suppressor
- **Cox8a, Ndufs5, Ndufb7:** Mitochondrial complex genes
- **Rpl21, Rpl18:** Ribosomal proteins (translational stress)
- **4 cell type proportions** in top 20

**Interview answer:** "The classifier demonstrated the expected sample size limitation.
The value is in proper methodology — LOSO-CV, pseudobulk, no pseudoreplication — and
in feature importance validating the biological findings from independent DE analysis."

---

## 11. GSEA — Pathway Enrichment

### What Is GSEA?

Gene Set Enrichment Analysis tests whether genes in known biological pathways
cluster at the top or bottom of a ranked gene list. We ranked ALL genes by their
spaceflight logFC, then tested if pathway genes are enriched at the extremes.

### KEGG Results — Brainstem Neurons

| Pathway | Adjusted P-value | Interpretation |
|---------|-----------------|----------------|
| ALS | 1.04 × 10⁻¹² | Motor neuron disease |
| Parkinson's | 5.75 × 10⁻¹⁰ | Dopaminergic neurodegeneration |
| Oxidative phosphorylation | 3.24 × 10⁻⁹ | Mitochondrial energy disruption |
| Ubiquitin proteolysis | 2.05 × 10⁻⁸ | Protein degradation activated |
| Huntington's | 1.22 × 10⁻⁷ | Polyglutamine repeat disorder |
| Alzheimer's | 2.67 × 10⁻⁷ | Amyloid/tau pathology |

**The headline finding:** Spaceflight DE genes overlap with ALL major
neurodegenerative disease pathways. This doesn't mean spaceflight causes these
diseases — it means the molecular stress response shares common machinery.

### GO Results — Oligodendrocytes

ALL top pathways have negative NES (downregulated in spaceflight):
- Translation → protein synthesis shutdown
- Mitochondrial ATP synthesis → energy production disrupted
- Cellular respiration → metabolic collapse

Pattern: oligodendrocytes are under severe metabolic stress.

### GO Results — CB Granule Neurons

- Glucose homeostasis ↓ (metabolic disruption)
- Potassium ion transport ↓ (electrophysiological disruption)
- Calcineurin-NFAT signaling ↑ (calcium stress response)
- Response to radiation ↑ (cosmic radiation on ISS)

### Convergent Evidence

The biological story is consistent across independent methods:

```
                    DE Analysis
                        │
                        ▼
              ┌─────────────────┐
              │  Mitochondrial  │◀── ML Feature Importance
              │  Dysfunction    │
              └────────┬────────┘
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
      ┌──────────┐ ┌────────┐ ┌──────────┐
      │ Protein  │ │ Neuro- │ │   BBB    │
      │ Homeo-   │ │ inflam-│ │ Compro-  │
      │ stasis   │ │ mation │ │ mise     │
      └──────────┘ └────────┘ └──────────┘
            │          │          │
            └──────────┼──────────┘
                       ▼
              ┌───────────────── ┐
              │ Neurodegenerative│◀── KEGG Pathways
              │ Signature        │
              └───────────────── ┘
```

---

## 12. Hexagonal Architecture & Testing

### Package Structure

```
src/spacegen/
├── core/                    # Pure functions — no I/O
│   ├── qc.py               # calculate_qc_metrics, filter_cells_condition_aware
│   ├── normalization.py     # normalize_counts, select_hvgs
│   └── features.py          # pseudobulk, proportions, QC features, merge
├── models/                  # Pydantic validation
│   └── configs.py           # QCConfig, NormalizationConfig, FeatureConfig, ProvenanceMetadata
├── ports/                   # Abstract interfaces
│   └── data_port.py         # DataReader, DataWriter ABCs
└── adapters/                # Concrete I/O
    ├── h5_reader.py         # BronzeH5Reader
    ├── h5ad_reader.py       # H5adReader
    └── local_writer.py      # LocalWriter (.h5ad, .parquet, .json)
```

### Why Pure Functions Matter

Every core function:
1. Takes AnnData/DataFrame as input
2. Returns AnnData/DataFrame as output
3. Never modifies the input (returns a copy)
4. Has no side effects (no file I/O, no logging, no state)

This makes them trivially testable and composable.

### Pydantic Validation

Pydantic models sit between adapters and core. They validate inputs before
processing begins:

```python
config = QCConfig(min_counts=5000, max_counts=1000)
# → ValidationError: max_counts must be greater than min_counts

config = QCConfig(mt_threshold_gc=10.0, mt_threshold_flight=3.0)
# → ValidationError: flight threshold should be >= gc threshold

meta = ProvenanceMetadata(dataset_id="INVALID")
# → ValidationError: dataset_id must match pattern ^OSD-\d+$
```

### Test Suite

30 tests covering:
- Core QC functions (7 tests)
- Core normalization (6 tests)
- Core features (6 tests)
- Pydantic validation (11 tests)

Key test patterns:
- **Immutability:** Input data is never modified
- **Contract:** Output has expected columns/shape
- **Edge cases:** Empty data, minimum thresholds, duplicate detection
- **Validation:** Bad inputs are rejected with clear errors

---

## 13. D3 Visualization

### Design

Force-directed network graph showing GSEA pathway findings:
- Central hub: "Spaceflight Neurodegenerative Signature"
- Cell type nodes (green): Brainstem, Oligodendrocytes, CB Granule
- Pathway nodes: Red (upregulated), Blue (downregulated)
- Edge thickness proportional to -log10(p-value)

### Why Force-Directed?

The GSEA data is fundamentally a network — cell types connect to pathways with
varying significance. Force-directed layout lets convergent biology emerge visually
(multiple cell types pointing to the same pathways).

### GraphKB Connection

Inspired by GraphKB (Reisle et al., Nature Communications 2022) — a knowledge
graph visualization for clinical genomics at BC Cancer's GSC. Same conceptual
model: biological entities as nodes, relationships as edges, significance as
visual weight.

---

## 14. Key Biological Findings

### The Neurodegenerative Signature

Spaceflight induces a molecular signature in mouse brain that overlaps with
neurodegenerative diseases. This is supported by convergent evidence:

1. **DE analysis:** Mitochondrial genes (Cox8a, Ndufs5), heat shock proteins
   (Hsph1, Cryab), complement genes (C1qa, C1qb) all dysregulated
2. **ML feature importance:** Same mitochondrial genes are top classifiers
3. **GO enrichment:** Translation, oxidative phosphorylation, cellular respiration
   downregulated in oligodendrocytes
4. **KEGG enrichment:** ALS (p=10⁻¹²), Parkinson's, Huntington's, Alzheimer's
   pathways enriched in brainstem neurons

### Five Pillars of the Spaceflight Brain Response

1. **Mitochondrial dysfunction** — energy production disrupted across cell types
2. **Protein homeostasis collapse** — translation shutdown + ubiquitin proteolysis
3. **Neuroinflammation** — 4.4× microglial enrichment + complement suppression
4. **BBB compromise** — blood-brain barrier maintenance downregulated
5. **Cell death activation** — apoptotic pathways upregulated

---

## 15. Future Work

### Phase 2: ATAC-seq Integration

OSD-352 is multiome — RNA + ATAC from the same nuclei. Adding chromatin
accessibility would show whether the transcriptional changes we found are
driven by changes in chromatin openness.

**What it adds:**
- Peak-barcode matrix ingestion (new bronze adapter)
- LSI dimensionality reduction (ATAC equivalent of PCA)
- MuData gold layer (RNA + ATAC in one container)
- Peak-to-gene linkage (which open chromatin regions drive which genes)

**Why it matters:** Connects to ChromApipe (bulk chromatin accessibility) in the
portfolio arc. Goes from "genes are differentially expressed" to "the chromatin
is physically opening/closing at these loci."

### Phase 3: GLM-5.1 Autonomous Optimization

After more biological replicates are available, use GLM-5.1 (open-weight LLM)
as an autonomous optimization agent:
- Reads MLflow experiment logs
- Proposes parameter changes (clustering resolution, DE thresholds)
- Runs pipeline, evaluates results
- Iterates across hundreds of rounds without manual intervention

### Publication

Phase 1 paper to bioRxiv as short communication (2,500-4,000 words).
Phase 2 paper as follow-up citing Phase 1.

---

## 16. Interview Talking Points

### On Architecture
"I used hexagonal architecture because bioinformatics pipelines need to be
swappable — same core logic, different data sources. When RRRM-1 processed
data becomes available, I write one new adapter. Zero core changes."

### On QC
"I used condition-aware mitochondrial thresholds because uniform filtering
would remove the stressed cells that ARE the biology we're studying. The
asymmetric removal rate (17% Flight vs 5.5% GC) confirmed the approach."

### On ML
"With n=5 biological replicates, the classifier showed expected limitations.
I used LOSO-CV to prevent data leakage and pseudobulk to avoid pseudoreplication.
The AUROC of 0.757 shows the features carry signal — robust classification
needs more samples, not better models."

### On GSEA
"The neurodegenerative pathway enrichment is the headline finding. ALS at
p=10⁻¹² validated across three independent methods — DE, ML feature importance,
and GSEA. The convergence across methods strengthens confidence that this is
real biology, not a statistical artifact."

### On Testing
"Every core function is pure and tested for immutability. Pydantic validates
inputs before they reach core logic. 30 tests, all passing. The architecture
makes testing trivial — no mocking needed for pure functions."

### On the Biological Story
"Spaceflight induces a neurodegenerative-like molecular signature in mouse brain:
mitochondrial dysfunction, protein synthesis collapse, neuroinflammation, BBB
disruption, and cell death activation. These findings are consistent with
existing spaceflight neuroscience literature and add single-cell resolution
that bulk studies couldn't provide."
