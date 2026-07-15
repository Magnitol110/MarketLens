# Дані MarketLens

## Фінальні файли

- `processed/msft_daily.csv` — очищені щоденні OHLCV-дані Microsoft від 1986 року до останнього завершеного торгового дня.
- `processed/spy_daily.csv` — очищений ринковий еталон SPY за доступний через Nasdaq період.
- `processed/msft_spy_daily.csv` — внутрішнє об'єднання MSFT і SPY за датою; основний файл для моделі відносної дохідності.
- `processed/training_features.csv` — 36 хронологічних ознак, цільовий клас і готові `train`/`validation`/`test` періоди без випадкового перемішування.

Сирі файли в `raw/` не комітяться. Вони відтворюються у `00_sources.ipynb`, а очищені файли — у `01_cleaning_eda.ipynb` або командою `python scripts/build_market_dataset.py`.

`Adj Close` свідомо не використовується: архівний файл і Nasdaq мають різні правила коригування. Для всього набору збережено узгоджені `open`, `high`, `low`, `close`, `volume`.

Тренувальна ціль порівнює 5-денну дохідність MSFT із 5-денною дохідністю SPY. Межі класів: понад `+1%` — `outperform`, нижче `-1%` — `underperform`, решта — `neutral`. Перед validation і test видалено по 5 рядків, щоб ціль не використовувала ціни з наступного періоду.

## Джерела

- Історичний MSFT: Kaggle `matiflatif/microsoft-complete-stocks-dataweekly-updated`.
- Актуальне доповнення MSFT і SPY: Nasdaq Historical API.

Перед публічним поширенням архівного Kaggle-файлу окремо перевірте ліцензію на сторінці набору.
