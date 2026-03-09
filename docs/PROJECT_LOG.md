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
