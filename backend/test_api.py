
from fastapi.testclient import TestClient
from backend.api import app

client = TestClient(app)


def test_home_endpoint():
    response = client.get("/")
    assert response.status_code == 200


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200


def test_metrics_endpoint():
    response = client.get("/api/metrics")
    assert response.status_code == 200


def test_customers_endpoint():
    response = client.get("/api/customers?limit=10&offset=0")
    assert response.status_code == 200


def test_customers_reject_zero_limit():
    response = client.get("/api/customers?limit=0&offset=0")
    assert response.status_code == 422


def test_customers_reject_limit_above_maximum():
    response = client.get("/api/customers?limit=101&offset=0")
    assert response.status_code == 422


def test_customers_reject_negative_offset():
    response = client.get("/api/customers?limit=10&offset=-1")
    assert response.status_code == 422


def test_customers_accept_valid_pagination():
    response = client.get("/api/customers?limit=5&offset=0")
    assert response.status_code == 200

