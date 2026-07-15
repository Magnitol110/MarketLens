# MarketLens progress board

Update this file at the end of every work block. A task is **Done** only when it has evidence: a Colab link, Git commit, screenshot, or recorded metric.

| ID | Task | Owner | Status | Evidence | Notes |
| --- | --- | --- | --- | --- | --- |
| SET-01 | Create tracking structure | Artem | Done | Initial repository structure | 2026-07-13 |
| DATA-01 | Approve data sources and licences | Artem | In review | `docs/sources.csv`, `notebooks/00_sources.ipynb` | Code is locally verified; run in Colab and confirm Kaggle licence |
| DATA-02 | Select and clean MSFT history | Artem | Done | `data/processed/msft_daily.csv` | 10,160 rows; 1986-03-13 to 2026-07-13 |
| DATA-03 | Add SPY benchmark and align dates | Artem | Done | `data/processed/msft_spy_daily.csv` | 2,512 aligned rows; no nulls or duplicate dates |
| DATA-04 | Create teacher-facing reproducibility log | Artem | Done | local `worklog/MarketLens_full_worklog.ipynb` | Ignored by Git; upload to Drive/Colab manually |
| ML-01 | Create chronological features and target | Artem | Done | `data/processed/training_features.csv`, `docs/training-dataset-manifest.json` | 2,477 rows, 36 features, purged chronological splits |
| WEB-01 | Create Vue UI shell and disclaimer | Stepan | To do |  |  |

## Daily check-in

- What was completed?
- What evidence was added?
- What is blocked?
- What is the next smallest task?
