# Decision log

| Date | Decision | Why | Owner |
| --- | --- | --- | --- |
| 2026-07-13 | Use a three-class, five-trading-day relative-to-SPY target. | Makes the model a research signal rather than a buy/sell recommendation. | Artem and Stepan |
| 2026-07-13 | Keep news as a model feature only if timestamped historical coverage is adequate. | Avoids inventing or leaking future information. | Artem and Stepan |
| 2026-07-14 | Limit the MVP to Microsoft (`MSFT`); retain SPY only as a market benchmark and feature. | A single ticker makes the four-day project smaller and easier to validate. | Artem and Stepan |
| 2026-07-14 | Use a static historical snapshot for training and a separate end-of-day collector for freshness. | Prevents a stale Kaggle dataset from being presented as current 2026 data. | Artem and Stepan |
| 2026-07-14 | Select `MSFT_1986-03-13_2025-07-14.csv` from the supplied archive and backfill with Nasdaq data. | It has the earliest valid MSFT start and the latest actual archive date; the file labelled 1973 actually begins in 1996. | Artem |
| 2026-07-14 | Keep only MSFT as the predicted company and SPY as a benchmark. | Ten years of aligned MSFT/SPY data are sufficient for the four-day baseline; more companies would expand scope without helping the stated MVP. | Artem and Stepan |
