"""Generate the English, teacher-facing MarketLens project worklog notebook."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "notebooks" / "05_project_worklog.ipynb"

def md(text):
    return {"cell_type": "markdown", "metadata": {}, "source": text.strip() + "\n"}

def code(text):
    return {"cell_type": "code", "execution_count": None, "metadata": {}, "outputs": [], "source": text.strip() + "\n"}

cells = [
md("""
# MarketLens — End-to-End AI Project Worklog

This notebook is the teacher-facing audit trail of our project: **source research → cleaning → features → model → held-out evaluation → API → Vue website**.

## TL;DR

- Task: classify MSFT performance relative to SPY over the next five trading days.
- Data: 2,477 modelling rows, 36 features, 2016–2026.
- Model: GPU-trained MLP `36 → 128 → 64 → 3`.
- Held-out test: macro-F1 **0.339**, tree baseline **0.281**, dummy **0.169**.
- Product: Vue 3 → FastAPI → portable NumPy model.

> MarketLens is an educational experiment, not investment advice.
"""),
md("""
## 1. Reproducible setup

The notebook expects the MarketLens repository structure. In a blank Colab runtime, clone the repository first:

```python
!git clone https://github.com/Magnitol110/MarketLens.git
%cd MarketLens
```

The next cell locates the project and checks the required versioned artifacts.
"""),
code("""
from pathlib import Path
import csv, json, sys

def find_root():
    for candidate in [Path.cwd(), Path.cwd().parent, Path('/content/MarketLens')]:
        if (candidate / 'docs' / 'training-dataset-manifest.json').exists():
            return candidate.resolve()
    raise FileNotFoundError('Open this notebook from MarketLens or clone the repository to /content/MarketLens')

ROOT = find_root()
required = [
    'data/processed/msft_daily.csv', 'data/processed/spy_daily.csv',
    'data/processed/training_features.csv', 'data/processed/latest_features.csv',
    'backend/marketlens_model.npz', 'docs/final-test-metrics.json'
]
missing = [name for name in required if not (ROOT / name).exists()]
assert not missing, f'Missing artifacts: {missing}'
print('Project root:', ROOT)
print('Required artifacts checked:', len(required))
"""),
md("""
## 2. Data source research and snapshot

We compared Kaggle datasets, Nasdaq, Financial Modeling Prep, Alpha Vantage, and Microsoft's official stock lookup. We selected Kaggle for a reproducible long-term MSFT snapshot and Nasdaq for the recent MSFT extension and SPY market benchmark.

Every candidate has a URL, retrieval date, decision, purpose, and owner in `docs/sources.csv`. Raw files are not committed; their SHA-256 hashes are recorded in `docs/data-snapshot.json`.
"""),
code("""
def csv_rows(relative_path):
    with (ROOT / relative_path).open(encoding='utf-8-sig', newline='') as stream:
        return list(csv.DictReader(stream))

sources = csv_rows('docs/sources.csv')
approved = [row for row in sources if row['decision'].startswith('approved')]
print('Candidate sources reviewed:', len(sources))
for row in approved:
    print(f"- {row['name']} | {row['decision']}\\n  {row['url']}")

snapshot = json.loads((ROOT / 'docs/data-snapshot.json').read_text(encoding='utf-8'))
print('\\nFrozen raw snapshots:', len(snapshot['sources']))
for item in snapshot['sources']:
    print('-', item['name'], '| SHA-256:', item['sha256'][:12] + '...')
"""),
md("""
## 3. Cleaning and automated quality checks

We standardized column names and dates, converted OHLCV fields to numbers, removed non-data rows and duplicate dates, sorted chronologically, and merged MSFT with SPY only on common trading dates. We then checked missing values, duplicate dates, and the OHLC rule `low ≤ open/close ≤ high`.
"""),
code("""
def quality_report(relative_path):
    rows = csv_rows(relative_path)
    dates = [row['date'] for row in rows]
    numeric = ['open', 'high', 'low', 'close', 'volume']
    missing = sum(not row.get(column, '').strip() for row in rows for column in numeric)
    bad_ohlc = 0
    for row in rows:
        o, h, l, c = map(float, [row['open'], row['high'], row['low'], row['close']])
        bad_ohlc += not (l <= o <= h and l <= c <= h)
    return {'file': relative_path, 'rows': len(rows), 'first': min(dates), 'last': max(dates),
            'duplicate_dates': len(dates)-len(set(dates)), 'missing_numeric': missing, 'bad_ohlc': bad_ohlc}

reports = [quality_report('data/processed/msft_daily.csv'), quality_report('data/processed/spy_daily.csv')]
for report in reports: print(report)
assert all(r['duplicate_dates'] == r['missing_numeric'] == r['bad_ohlc'] == 0 for r in reports)
print('DATA QUALITY CHECK: PASSED')
"""),
md("""
## 4. Leakage-safe features, target, and chronological split

Target: `MSFT future 5-day return − SPY future 5-day return`.

- above `+1%` → `outperform`;
- between `−1%` and `+1%` → `neutral`;
- below `−1%` → `underperform`.

The 36 inputs cover returns, gaps, intraday ranges, moving-average ratios, volatility, relative volume, MSFT–SPY excess returns, and cyclical calendar values. Every rolling feature uses only current and past observations.
"""),
code("""
manifest = json.loads((ROOT / 'docs/training-dataset-manifest.json').read_text(encoding='utf-8'))
print('Rows:', manifest['rows'], '| Features:', manifest['feature_count'])
print('Period:', manifest['first_date'], 'to', manifest['last_date'])
print('Target:', manifest['target'])
print('Split method:', manifest['split_method'])
for name, info in manifest['splits'].items():
    print(f"{name:10} {info['rows']:4} rows | {info['first_date']} to {info['last_date']} | {info['class_counts']}")
assert manifest['feature_count'] == len(manifest['feature_columns']) == 36
assert manifest['splits']['train']['last_date'] < manifest['splits']['validation']['first_date']
assert manifest['splits']['validation']['last_date'] < manifest['splits']['test']['first_date']
print('CHRONOLOGICAL SPLIT CHECK: PASSED')
"""),
md("""
## 5. Baseline selection without opening the test set

Notebook 02 compared Dummy, Logistic Regression, Random Forest, and Histogram Gradient Boosting on validation data only. We selected by macro-F1 because it gives equal importance to all three classes despite class imbalance.
"""),
code("""
baseline = json.loads((ROOT / 'docs/baseline-metrics.json').read_text(encoding='utf-8'))
for result in sorted(baseline['results'], key=lambda x: x['macro_f1'], reverse=True):
    print(f"{result['model']:28} macro-F1={result['macro_f1']:.3f} accuracy={result['accuracy']:.3f}")
print('Selected baseline:', baseline['selected_model'])
print('Untouched test rows at selection time:', baseline['test_rows_untouched'])
"""),
md("""
## 6. Final neural network trained on GPU

The final model is an MLP `36 → 128 → 64 → 3` with Batch Normalization, ReLU, and 0.25 dropout. It was trained in Google Colab on a Tesla T4. The best checkpoint was selected using validation macro-F1; test data was not used to choose parameters or epochs.
"""),
code("""
model = json.loads((ROOT / 'docs/final-model-metrics.json').read_text(encoding='utf-8'))
print('Experiment:', model['experiment_id'])
print('Device:', model['device'], '| GPU:', model['gpu_name'])
print('Architecture:', model['architecture'])
print('Epochs trained:', model['epochs_trained'], '| best epoch:', model['best_epoch'])
print('Validation macro-F1:', round(model['validation']['macro_f1'], 3))
assert model['device'] == 'cuda'
"""),
md("""
## 7. One-time held-out test

Notebook 04 opened the chronological test only after freezing the MLP. The baseline was retrained on training data and all models were evaluated on the same 374 rows. Uncertainty was measured with 2,000 paired bootstrap samples.

![Model comparison](../docs/figures/test-model-comparison.png)

![Confusion matrix](../docs/figures/test-confusion-matrix.png)
"""),
code("""
test = json.loads((ROOT / 'docs/final-test-metrics.json').read_text(encoding='utf-8'))
print('Test period:', test['test_period'])
for result in test['comparison']:
    print(f"{result['model']:28} macro-F1={result['macro_f1']:.3f} accuracy={result['accuracy']:.3f} balanced={result['balanced_accuracy']:.3f}")
print('MLP macro-F1 95% CI:', [round(x,3) for x in test['mlp_macro_f1_bootstrap_95_ci']])
print('MLP minus baseline 95% CI:', [round(x,3) for x in test['mlp_minus_baseline_macro_f1_bootstrap_95_ci']])
for label in test['labels']:
    row = test['classification_report'][label]
    print(f"{label:12} F1={row['f1-score']:.3f} recall={row['recall']:.3f} support={int(row['support'])}")
"""),
md("""
## 8. Turning the model into a web product

The frozen weights were exported to a portable NumPy artifact of about 55 KiB and verified against PyTorch on every test row.

`Vue 3 → FastAPI /api/predict/{symbol} → NumPy MLP → signal + probabilities`

The API also provides OHLCV candle history, snapshot date, model version, and a disclaimer. Production inference therefore needs neither a GPU nor PyTorch.
"""),
code("""
sys.path.insert(0, str(ROOT))
from backend.inference import PortableMarketLensModel
portable = PortableMarketLensModel(ROOT / 'backend/marketlens_model.npz')
latest = csv_rows('data/processed/latest_features.csv')[-1]
features = {column: float(latest[column]) for column in portable.feature_columns}
prediction = portable.predict_mapping(features)
print('Snapshot:', latest['date'])
print('Signal:', prediction['label'], '| Confidence:', f"{prediction['confidence']:.1%}")
print('Probabilities:', {k: round(v,4) for k,v in prediction['probabilities'].items()})
print('Portable model size:', round((ROOT/'backend/marketlens_model.npz').stat().st_size/1024,1), 'KiB')
"""),
md("""
## 9. Conclusions and limitations

### What we completed

- traceable sources and hashed snapshots;
- reproducible cleaning and feature engineering;
- a chronological split with an untouched test period;
- a GPU-trained MLP that beats the selected baseline in test macro-F1;
- matching PyTorch and NumPy inference;
- one integrated Vue + FastAPI MVP.

### What we do not claim

- macro-F1 0.339 is modest, not production-grade accuracy;
- the model does not predict an exact price and is not trading advice;
- current trained coverage is MSFT only;
- news was excluded because historical timestamp coverage was not sufficiently validated;
- real deployment needs more tickers, daily refreshes, and ongoing out-of-sample monitoring.

**Final result:** a reproducible path from data to an evaluated AI model and a working web product—not a promise to predict markets without error.
"""),
]

notebook = {"cells": cells, "metadata": {"colab": {"name": "05_project_worklog.ipynb", "provenance": []}, "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"}, "language_info": {"name": "python", "version": "3"}}, "nbformat": 4, "nbformat_minor": 5}
OUTPUT.write_text(json.dumps(notebook, ensure_ascii=False, indent=1), encoding="utf-8")
print('Generated', OUTPUT)
