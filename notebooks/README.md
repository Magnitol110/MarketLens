# Colab notebook workflow

Open these notebooks from the GitHub repository in Google Colab. Run each one from a fresh runtime before marking its task done.

The repository is the source of truth for notebook code. Google Drive may hold working copies and local data snapshots, but it is not automatically synchronised with Git.

After a meaningful change: save the notebook in Colab, save a copy to GitHub, add the commit or Colab link to `docs/progress.md`, then pull the latest repository version before continuing locally.

## Notebook sequence for the MSFT MVP

| Notebook | Purpose | Output |
| --- | --- | --- |
| `00_sources.ipynb` | Record sources, download the historical MSFT/SPY snapshot, and run the daily collector manually while it is being tested. | Untouched date-stamped raw files and updated `docs/sources.csv`. |
| `01_cleaning_eda.ipynb` | Validate OHLCV columns, remove duplicates, sort dates, check gaps, and create lagged features. | Clean chronological table in `data/processed/` and EDA charts. |
| `02_baseline.ipynb` | Train the simplest price-only baseline using chronological train/validation/test periods. | Baseline macro F1, accuracy, and confusion matrix. |
| `03_final_model.ipynb` | Train the selected model with only approved pre-prediction features; optionally add news only after its history is validated. | Versioned model artifact and experiment-log entry. |
| `04_evaluation.ipynb` | Compare final model with the baseline on the untouched test period and prepare presentation examples. | Final metrics, successful/failure cases, and limitations. |

Do not use `04_evaluation.ipynb` to tune the model. If a daily collection produces new data, append it to a new dated raw snapshot and rerun the earlier notebooks deliberately.
