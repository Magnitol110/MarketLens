"""Generate the Colab-ready data notebooks without external notebook packages."""

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"


def markdown(source: str) -> dict:
    return {"cell_type": "markdown", "metadata": {}, "source": source}


def code(source: str) -> dict:
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": source}


def save(name: str, cells: list[dict]) -> None:
    notebook = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3"},
            "colab": {"provenance": []},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (NOTEBOOKS / name).write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")


shared_setup = '''from pathlib import Path
import os
import subprocess
import sys

REPO_URL = "https://github.com/Magnitol110/MarketLens.git"
IN_COLAB = "google.colab" in sys.modules

if IN_COLAB:
    repo_path = Path("/content/MarketLens")
    if not repo_path.exists():
        subprocess.run(["git", "clone", REPO_URL, str(repo_path)], check=True)
    os.chdir(repo_path)

ROOT = Path.cwd()
if ROOT.name == "notebooks":
    ROOT = ROOT.parent
assert (ROOT / "README.md").exists(), f"Repository root not found: {ROOT}"
print("Repository:", ROOT)
print("Running in Colab:", IN_COLAB)'''


save("00_sources.ipynb", [
    markdown('''# 00 — Джерела та історичний знімок

## Мета

Завантажити всі кандидатні CSV із Kaggle, вибрати файл за **фактичним**, а не заявленим діапазоном дат, дозібрати MSFT і SPY з Nasdaq та зафіксувати незмінний знімок.

**Історичний знімок** — це копія даних на конкретний момент із URL, датою отримання, діапазоном і SHA-256. Завдяки цьому можна довести, на яких саме даних навчалася модель.

Джерела:

- Kaggle: https://www.kaggle.com/datasets/matiflatif/microsoft-complete-stocks-dataweekly-updated
- Nasdaq MSFT: https://www.nasdaq.com/market-activity/stocks/msft/historical
- Nasdaq SPY: https://www.nasdaq.com/market-activity/etf/spy/historical
'''),
    code(shared_setup),
    code('''from datetime import date, datetime, timedelta, timezone
import hashlib
import json
import shutil

import pandas as pd

RAW = ROOT / "data" / "raw"
DOCS = ROOT / "docs"
RAW.mkdir(parents=True, exist_ok=True)
REFRESH_FROM_WEB = IN_COLAB
print("Refresh from web:", REFRESH_FROM_WEB)'''),
    markdown('''## 1. Завантаження та порівняння Kaggle CSV

У Colab notebook автоматично встановлює `kagglehub` і завантажує публічний набір. Локально він використовує вже зафіксований raw-файл.
'''),
    code('''if REFRESH_FROM_WEB:
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", "kagglehub"], check=True)
    import kagglehub
    kaggle_dir = Path(kagglehub.dataset_download("matiflatif/microsoft-complete-stocks-dataweekly-updated"))
    candidate_files = sorted(kaggle_dir.glob("*.csv"))
else:
    candidate_files = sorted(RAW.glob("msft_kaggle_*.csv"))

assert candidate_files, "Kaggle CSV files were not found"

profiles = []
for path in candidate_files:
    frame = pd.read_csv(path)
    date_column = next(column for column in frame.columns if column.strip().lower() == "date")
    parsed_dates = pd.to_datetime(frame[date_column].astype(str).str[:10], errors="coerce")
    profiles.append({
        "path": path,
        "file": path.name,
        "rows": len(frame),
        "valid_rows": int(parsed_dates.notna().sum()),
        "bad_dates": int(parsed_dates.isna().sum()),
        "min_date": parsed_dates.min(),
        "max_date": parsed_dates.max(),
    })

profile = pd.DataFrame(profiles).sort_values(
    ["min_date", "max_date", "valid_rows"], ascending=[True, False, False]
).reset_index(drop=True)
display(profile.drop(columns="path"))

selected = profile.iloc[0]
selected_raw = RAW / "msft_kaggle_1986-03-13_2025-07-11.csv"
if Path(selected["path"]).resolve() != selected_raw.resolve():
    shutil.copy2(selected["path"], selected_raw)
print("Selected:", selected["file"], selected["min_date"].date(), selected["max_date"].date())'''),
    markdown('''## 2. Актуальне доповнення Nasdaq

API-запит використовує ISO-дати. Якщо Nasdaq тимчасово недоступний, повторіть цю комірку пізніше; старий raw-знімок не перезаписується помилковою відповіддю.
'''),
    code('''def download_nasdaq(symbol, asset_class, start_date, end_date, output_path):
    url = f"https://api.nasdaq.com/api/quote/{symbol}/historical"
    from urllib.parse import urlencode
    from urllib.request import Request, urlopen

    query = urlencode({
        "assetclass": asset_class,
        "fromdate": start_date.isoformat(),
        "todate": end_date.isoformat(),
        "limit": 10000,
    })
    request = Request(
        f"{url}?{query}",
        headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json, text/plain, */*"},
    )
    with urlopen(request, timeout=60) as response:
        payload = json.load(response)
    rows = ((payload.get("data") or {}).get("tradesTable") or {}).get("rows")
    if not rows:
        raise RuntimeError(f"Nasdaq returned no rows for {symbol}: {payload.get('status')}")
    output_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return len(rows)

today = date.today()
existing_msft = sorted(RAW.glob("msft_nasdaq_*.json"))
existing_spy = sorted(RAW.glob("spy_nasdaq_*.json"))
msft_json = RAW / f"msft_nasdaq_2025-07-12_{today.isoformat()}.json" if REFRESH_FROM_WEB else existing_msft[-1]
spy_json = RAW / f"spy_nasdaq_recent_{today.isoformat()}.json" if REFRESH_FROM_WEB else existing_spy[-1]

if REFRESH_FROM_WEB:
    msft_rows = download_nasdaq("MSFT", "stocks", date(2025, 7, 12), today, msft_json)
    spy_rows = download_nasdaq("SPY", "etf", today - timedelta(days=3653), today, spy_json)
    print("Downloaded Nasdaq rows:", {"MSFT": msft_rows, "SPY": spy_rows})
else:
    assert existing_msft and existing_spy, "Existing Nasdaq raw snapshots are missing"
    print("Using existing Nasdaq snapshots")'''),
    markdown('''## 3. Маніфест знімка

SHA-256 зміниться, якщо хоча б один байт сирого файлу буде змінено.
'''),
    code('''def file_sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()

snapshot_manifest = {
    "created_at_utc": datetime.now(timezone.utc).isoformat(),
    "sources": [
        {
            "name": "Kaggle Microsoft Complete Stocks Data",
            "url": "https://www.kaggle.com/datasets/matiflatif/microsoft-complete-stocks-dataweekly-updated",
            "raw_file": str(selected_raw.relative_to(ROOT)).replace("\\\\", "/"),
            "sha256": file_sha256(selected_raw),
            "actual_min_date": str(selected["min_date"].date()),
            "actual_max_date": str(selected["max_date"].date()),
        },
        {
            "name": "Nasdaq MSFT Historical",
            "url": "https://www.nasdaq.com/market-activity/stocks/msft/historical",
            "raw_file": str(msft_json.relative_to(ROOT)).replace("\\\\", "/"),
            "sha256": file_sha256(msft_json),
        },
        {
            "name": "Nasdaq SPY Historical",
            "url": "https://www.nasdaq.com/market-activity/etf/spy/historical",
            "raw_file": str(spy_json.relative_to(ROOT)).replace("\\\\", "/"),
            "sha256": file_sha256(spy_json),
        },
    ],
}
(DOCS / "data-snapshot.json").write_text(
    json.dumps(snapshot_manifest, ensure_ascii=False, indent=2), encoding="utf-8"
)
display(pd.DataFrame(snapshot_manifest["sources"]))'''),
    markdown('''## 4. Побудова чистих таблиць

Ця команда видаляє службовий рядок, нормалізує OHLCV, об'єднує історію та перевіряє ціни, обсяг і дублікати дат.
'''),
    code('''sys.path.insert(0, str(ROOT))
from scripts.build_market_dataset import main as build_market_dataset

build_market_dataset()'''),
    code('''for filename in ["msft_daily.csv", "spy_daily.csv", "msft_spy_daily.csv"]:
    frame = pd.read_csv(ROOT / "data" / "processed" / filename)
    print(filename, {
        "rows": len(frame),
        "first_date": frame["date"].min(),
        "last_date": frame["date"].max(),
        "missing": int(frame.isna().sum().sum()),
        "duplicate_dates": int(frame["date"].duplicated().sum()),
    })
'''),
    markdown('''## Результат

Після успішного виконання збережіть оновлений notebook назад у GitHub. Сирі файли залишаються локальними, а `docs/data-snapshot.json` і чисті CSV фіксують доказ використаного знімка.
'''),
])


save("01_cleaning_eda.ipynb", [
    markdown('''# 01 — Очищення та хронологічні ознаки

## Мета

Перетворити синхронізовані MSFT + SPY ціни на файл, готовий до тренування.

**Хронологічна ознака** використовує лише інформацію, доступну на момент прогнозу: поточний або попередні торгові дні. Наприклад, `msft_return_5d` використовує ціни від `t-5` до `t`, а не майбутні ціни.

Конвенція: прогноз створюється **після закриття дня t** на результат наступних 5 торгових днів.
'''),
    code(shared_setup),
    code('''import json
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(ROOT))
from scripts.build_market_dataset import main as build_market_dataset
from scripts.build_training_features import main as build_training_features

raw_dir = ROOT / "data" / "raw"
raw_ready = (
    (raw_dir / "msft_kaggle_1986-03-13_2025-07-11.csv").exists()
    and bool(list(raw_dir.glob("msft_nasdaq_*.json")))
    and bool(list(raw_dir.glob("spy_nasdaq_*.json")))
)
if raw_ready:
    build_market_dataset()
else:
    print("Raw snapshots are absent; using committed processed price table")
training = build_training_features()'''),
    markdown('''## Створені групи ознак

- дохідність за 1, 5, 10 і 20 торгових днів;
- відносна дохідність MSFT мінус SPY;
- положення ціни відносно ковзних середніх;
- волатильність за 5, 10 і 20 днів;
- відносний обсяг торгів;
- gap, внутрішньоденний рух і денний діапазон;
- циклічне кодування дня тижня та місяця.

Майбутня 5-денна дохідність використовується тільки для створення `target_class` і не потрапляє до ознак.
'''),
    code('''path = ROOT / "data" / "processed" / "training_features.csv"
training = pd.read_csv(path, parse_dates=["date"])
feature_columns = [column for column in training.columns if column not in {"date", "split", "target_class"}]

summary = training.groupby("split", sort=False).agg(
    rows=("date", "size"),
    first_date=("date", "min"),
    last_date=("date", "max"),
)
display(summary)
display(pd.crosstab(training["split"], training["target_class"]))
print("Features:", len(feature_columns))'''),
    markdown('''## Перевірки перед тренуванням

Поділ виконується хронологічно: приблизно 70% train, 15% validation, 15% test. П’ять рядків перед validation і test видаляються, бо їхня ціль використовувала б ціни з наступної частини.
'''),
    code('''assert training["date"].is_monotonic_increasing
assert not training["date"].duplicated().any()
assert training.isna().sum().sum() == 0
assert np.isfinite(training[feature_columns].to_numpy()).all()
assert set(training["split"]) == {"train", "validation", "test"}
assert set(training["target_class"]) == {"outperform", "neutral", "underperform"}

split_order = training.groupby("split")["date"].agg(["min", "max"])
assert split_order.loc["train", "max"] < split_order.loc["validation", "min"]
assert split_order.loc["validation", "max"] < split_order.loc["test", "min"]
print("QA passed: no nulls, duplicates, infinities, or chronological overlap")'''),
    code('''display(training.head(3))
display(training.tail(3))
print("Training-ready file:", path)
print("Rows:", len(training), "Features:", len(feature_columns))'''),
    markdown('''## Результат

`data/processed/training_features.csv` готовий до `02_baseline.ipynb`.

У baseline не можна перемішувати рядки або повторно робити випадковий split. Масштабування, якщо воно потрібне моделі, навчається тільки на `split == "train"`.
'''),
])

print("Generated:", NOTEBOOKS / "00_sources.ipynb", NOTEBOOKS / "01_cleaning_eda.ipynb")
