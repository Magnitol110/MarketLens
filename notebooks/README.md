# Colab notebook workflow

Open these notebooks from the GitHub repository in Google Colab. Run each one from a fresh runtime before marking its task done.

The repository is the source of truth for notebook code. Google Drive may hold working copies and local data snapshots, but it is not automatically synchronised with Git.

After a meaningful change: save the notebook in Colab, save a copy to GitHub, add the commit or Colab link to `docs/progress.md`, then pull the latest repository version before continuing locally.

## Notebook sequence for the MSFT MVP

| Notebook | Purpose | Output |
| --- | --- | --- |
| `00_sources.ipynb` | Compare Kaggle candidates by actual dates, download current Nasdaq MSFT/SPY data, calculate SHA-256 hashes, and rebuild clean prices. | Date-stamped raw files, `docs/data-snapshot.json`, and clean price tables. |
| `01_cleaning_eda.ipynb` | Create leakage-safe returns, moving-average, volatility, volume, relative-market, and calendar features; then create the 5-day target and purged chronological splits. | Training-ready `data/processed/training_features.csv` and `docs/training-dataset-manifest.json`. |
| `02_baseline.ipynb` | Train the simplest price-only baseline using chronological train/validation/test periods. | Baseline macro F1, accuracy, and confusion matrix. |
| `03_final_model.ipynb` | Train the selected model with only approved pre-prediction features; optionally add news only after its history is validated. | Versioned model artifact and experiment-log entry. |
| `04_evaluation.ipynb` | Compare final model with the baseline on the untouched test period and prepare presentation examples. | Final metrics, successful/failure cases, and limitations. |
| `05_project_worklog.ipynb` | Teacher-facing, end-to-end explanation of sources, cleaning, features, training, testing, API, and Vue integration. | Executed audit trail of the complete project. |

Do not use `04_evaluation.ipynb` to tune the model. If a daily collection produces new data, append it to a new dated raw snapshot and rerun the earlier notebooks deliberately.
