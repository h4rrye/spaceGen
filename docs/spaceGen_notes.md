# spaceGen notes



`pyproject.toml` covers everything `environment.yml` does for dependency management. The only reason to keep `environment.yml` is if you're specifically using Conda (common in bioinformatics), but since your stack is all pip-installable (polars, mlflow, scikit-learn, xgboost) there's no reason to maintain both. One source of truth for dependencies is better than two that can drift apart.

____

Hexagonal architecture (also called "ports and adapters") is a design pattern where your core business logic sits in the center and knows nothing about the outside world. Everything external — databases, APIs, UIs, file systems — connects through defined interfaces.

Think of it as three layers. The **core** contains your pure logic (in your case, that would be things like "normalize gene expression counts" or "train a classifier"). It has no imports from external libraries for I/O. Then you have **ports**, which are just interfaces — abstract definitions of what the core needs. "I need to read expression data" is a port. "I need to save a model" is a port. Finally, **adapters** are the concrete implementations that plug into those ports. "Read a Parquet file from local disk" is one adapter. "Read from S3" is another adapter. "Read from a database" is yet another. The core doesn't care which one you use.

The name comes from the hexagon shape in the original diagrams, but the shape doesn't actually mean anything — it was just to break people out of thinking in the traditional top-down layered cake (UI → business logic → database).

The practical payoff is swappability. Your pipeline logic stays the same whether you're reading from local Parquet files on your laptop or from Delta Lake on Databricks. You just swap the adapter. It also makes testing easy — you can write a fake in-memory adapter and test your core logic without touching any real files or APIs.

____



### Datasets

**NASA Open Science Data Repository (OSDR)** — that's the official name of the platform.

The specific mission is **RRRM-1 / Rodent Research-8 (RR-8)**, and the datasets are from the GeneLab data processing pipeline within OSDR. For your logs, something like:

"Source: NASA OSDR (osdr.nasa.gov), RRRM-1/RR-8 mission, 10X Genomics scRNA-seq, datasets OSD-910 (spleen), OSD-905 (liver), OSD-918 (blood)"

1. **OSD-910 (Spleen)** — immune hub, richest cell type diversity, best for network analysis. Build with this first.
2. **OSD-905 (Liver)** — metabolic tissue, connects to your earlier OSD-47 bulk work, different biology from spleen.
3. **OSD-918 (Blood)** — circulating immune cells, bridges between spleen and liver, well-characterized cell markers for easy annotation.

Three tissues, three biological stories: immune response (spleen), metabolic disruption (liver), systemic circulation (blood). Together they paint a picture of how spaceflight affects the whole organism


____

### Condition-Aware QC Filtering (Silver Layer Decision)

Standard scRNA-seq QC applies a uniform mitochondrial percentage threshold (typically 5%) across all cells. For spaceflight data, this is problematic.

**Why condition-aware:** Space Flight samples show elevated mitochondrial content (tails up to ~31%) due to cellular stress from microgravity. A uniform 5% cutoff removes these stressed-but-real cells, losing the biological signal we're trying to study. Ground Control cells above 5% mt are more likely technical artifacts (damaged during sample prep).

**Thresholds chosen:**
- Ground Control: <5% mt (standard)
- Space Flight: <10% mt (lenient — preserves stressed cells)
- Both conditions: min 200 genes, min 500 UMI, max 50,000 UMI

**Result:** 13.3% cells removed overall. Flight lost 17% (stressed cells filtered), GC lost 5.5% (cleaner samples). This asymmetry confirms the approach — if we'd used uniform 5%, Flight would have lost significantly more cells.

**Rationale for specific numbers:**
- Min 200 genes: Standard threshold, filters empty droplets and debris
- Min 500 UMI: Appropriate for snRNA-seq (lower counts than whole-cell RNA-seq)
- Max 50,000 UMI: Dataset max is ~74k, 50k catches likely doublets while keeping high-quality cells
- 10% mt for Flight: Captures the stress tail without including severely damaged cells (max was 31%)

____

## Phase 3: Autonomous Optimization with GLM-5.1

### Objective
After the core snRNA-seq and snATAC-seq pipeline is complete and producing results (bronze/silver/gold layers stable), implement an autonomous optimization loop using GLM-5.1 as the optimization agent.

### What GLM-5.1 will own
- Clustering parameter optimization (resolution, n_neighbors, n_pcs)
- Cell type classification accuracy improvement via CellTypist model selection
- Gene regulatory network analysis parameter tuning
- Differential expression threshold optimization

### How it works
1. Define an evaluation metric (silhouette score, classification accuracy, marker gene enrichment) as the optimization target
2. GLM-5.1 reads current pipeline outputs and MLflow experiment logs
3. Agent proposes parameter changes, runs pipeline, evaluates results
4. Iterates autonomously across hundreds of rounds without manual intervention
5. MLflow tracks every iteration for full reproducibility and auditability

### Implementation notes
- GLM-5.1 is open weight, MIT license, available via Z.AI API or local deployment via vLLM/SGLang
- Compatible with Claude Code scaffolding
- Define clear stopping criteria: performance plateau or maximum iterations
- All parameter changes logged to MLflow with full rollback capability
- Keep human checkpoints at key milestones, do not run fully blind

### Resume framing
"Implemented autonomous hyperparameter optimization using GLM-5.1 for long-horizon iterative refinement of clustering and classification models, enabling sustained optimization across hundreds of rounds without manual intervention"

### Dependencies
- Phase 1 (RNA gold layer) complete
- Phase 2 (ATAC integration) complete
- MLflow tracking active and logging all runs
- Evaluation metrics defined and reproducible

____

### Gold Layer: Key Biological Findings (OSD-352 Brain)

**Cell type composition:** 67 cell types identified via CellTypist (Mouse_Whole_Brain model), validated with 21 canonical brain markers. Dominant population is cerebellar granule neurons (13,305 cells).

**Spaceflight impact on cell populations:**
Microglia (brain immune cells) are 4.4x enriched in spaceflight samples — strong evidence of neuroinflammation. OPCs (oligodendrocyte precursors) 4.1x enriched suggests active myelin remodeling. VLMCs (vascular cells) 3.7x enriched indicates vascular response to microgravity.

**Malat1 as spaceflight biomarker:**
The long non-coding RNA Malat1 is upregulated in almost every cell type under spaceflight. This is a well-documented stress-responsive gene and a known spaceflight biomarker — its consistent appearance across cell types validates the experimental design and our analysis pipeline.

**Complement pathway suppression in microglia:**
C1qa and C1qb (complement cascade initiators) are downregulated in microglia. The complement system is critical for synaptic pruning and neuroinflammation. Suppression under spaceflight could indicate altered immune surveillance in the brain.

**Heat shock protein changes in oligodendrocytes:**
Hsph1, Hsp90ab1, and Cryab (heat shock / protein folding chaperones) are downregulated in oligodendrocytes. This suggests disrupted protein homeostasis in myelin-producing cells, potentially affecting myelin integrity.

**Cerebellar motor coordination:**
Pcp2 (Purkinje cell protein 2) is strongly downregulated (logFC -3.3) in cerebellar granule neurons. Pcp2 is critical for cerebellar function and motor coordination — this finding connects to known astronaut reports of balance and coordination issues post-spaceflight.
