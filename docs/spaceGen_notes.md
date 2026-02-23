# spaceGen notes



`pyproject.toml` covers everything `environment.yml` does for dependency management. The only reason to keep `environment.yml` is if you're specifically using Conda (common in bioinformatics), but since your stack is all pip-installable (polars, mlflow, scikit-learn, xgboost) there's no reason to maintain both. One source of truth for dependencies is better than two that can drift apart.