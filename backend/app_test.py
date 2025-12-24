import pytest
from app import app, COUNTER_KEY


class FakeRedis:
    def __init__(self):
        self.storage = {}

    def get(self, key):
        return self.storage.get(key)

    def set(self, key, value):
        self.storage[key] = int(value)

    def incr(self, key):
        self.storage[key] = int(self.storage.get(key, 0)) + 1
        return self.storage[key]

    def decr(self, key):
        self.storage[key] = int(self.storage.get(key, 0)) - 1
        return self.storage[key]


@pytest.fixture
def client(monkeypatch):
    fake_redis = FakeRedis()
    fake_redis.set(COUNTER_KEY, 0)

    monkeypatch.setattr("app.r", fake_redis)
    with app.test_client() as client:
        yield client


def test_counter_initial_value(client):
    response = client.get("/api/counter")

    assert response.status_code == 200
    assert response.json == {"value": 0}


def test_counter_increment(client):
    response = client.post("/api/counter/increment")

    assert response.status_code == 200
    assert response.json == {"value": 1}

    response = client.get("/api/counter")
    assert response.json == {"value": 1}


def test_counter_cannot_be_negative(client):
    response = client.post("/api/counter/decrement")

    assert response.status_code == 400
    assert response.json == {"error": "Counter cannot be negative"}

    response = client.get("/api/counter")
    assert response.json == {"value": 0}
