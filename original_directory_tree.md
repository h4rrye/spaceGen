# Original Directory Structure

This file preserves the original directory tree before cleanup (2026-02-24).

```
.
├── conf
│   └── .gitkeep
├── data
│   ├── .DS_Store
│   ├── bronze
│   │   ├── .DS_Store
│   │   └── osd-47_mouse_liver_spaceflight
│   │       └── ingest_date=2026-02-23
│   │           └── .gitkeep
│   ├── gold
│   │   ├── .DS_Store
│   │   └── osd-47_mouse_liver_spaceflight
│   │       ├── .DS_Store
│   │       └── v1
│   │           └── .gitkeep
│   └── silver
│       ├── .DS_Store
│       └── osd-47_mouse_liver_spaceflight
│           ├── .DS_Store
│           └── v1
│               └── .gitkeep
├── docs
│   └── spaceGen_notes.md
├── LICENSE
├── notebooks
│   └── .gitkeep
├── pyproject.toml
├── README.md
├── reports
│   └── .gitkeep
├── src
│   ├── .DS_Store
│   └── spacegen
│       ├── __init__.py
│       ├── adapters
│       │   ├── __init__.py
│       │   ├── local_io.py
│       │   └── mlflow_logger.py
│       ├── config.py
│       ├── core
│       │   ├── __init__.py
│       │   ├── features.py
│       │   └── models.py
│       └── ports
│           ├── __init__.py
│           └── interfaces.py
└── tests
    └── .gitkeep

22 directories, 31 files
```
