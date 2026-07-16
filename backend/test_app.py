from fastapi.testclient import TestClient

from backend.app import app


client = TestClient(app)


def test_health_and_prediction() -> None:
    health = client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["model_loaded"] is True

    prediction = client.get("/api/predict/MSFT")
    assert prediction.status_code == 200
    payload = prediction.json()
    assert payload["prediction"] in {"underperform", "neutral", "outperform"}
    assert abs(sum(payload["probabilities"].values()) - 1.0) < 1e-5
    assert payload["as_of_date"] == "2026-07-14"


def test_history_and_unknown_symbol() -> None:
    history = client.get("/api/history/MSFT?period=1y")
    assert history.status_code == 200
    assert history.json()["candles"]

    unknown = client.get("/api/predict/AAPL")
    assert unknown.status_code == 404
