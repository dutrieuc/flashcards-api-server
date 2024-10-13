from fastapi.testclient import TestClient
import flashcards_core


def test_endpoints_are_protected(logged_out_client: TestClient):
    assert 401 == logged_out_client.get("/algorithms").status_code


def test_get_algorithms(monkeypatch, client: TestClient):
    fake_algorithms = {"test_alg_1": "testalg", "test_alg_2": "testalg"}
    monkeypatch.setattr(flashcards_core.schedulers, "SCHEDULERS", fake_algorithms)

    response = client.get("/algorithms")
    assert response.status_code == 200
    assert response.json() == list(fake_algorithms.keys())
