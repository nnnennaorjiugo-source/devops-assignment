import pytest
from app import app


@pytest.fixture
def client():
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json == {"status": "ok"}


def test_ready(client):
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json == {"status": "ready"}


def test_sergei(client):
    response = client.get("/sergei")
    assert response.status_code == 200
    assert b"Sergei Fixed It!" in response.data


def test_raditya(client):
    response = client.get("/raditya")
    assert response.status_code == 200
    assert b"Raditya Is Batman!" in response.data


def test_root_redirects(client):
    response = client.get("/")
    assert response.status_code == 302
    assert response.location in ["/sergei", "/raditya"]
