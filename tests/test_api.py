from fastapi.testclient import TestClient

from app.main import create_app
from triage.train import train


def test_health_lists_categories_and_articles(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["kb_articles"] == 2
    assert "password_reset" in body["categories"]


def test_classify_password_ticket(client):
    body = client.post("/classify", json={"text": "I forgot my password and cannot log in"}).json()
    assert body["category"] == "password_reset"
    assert 0 <= body["confidence"] <= 1
    assert len(body["scores"]) == 3


def test_classify_rejects_empty_text(client):
    assert client.post("/classify", json={"text": ""}).status_code == 422


def test_classify_rejects_missing_field(client):
    assert client.post("/classify", json={}).status_code == 422


def test_suggest_returns_matching_article(client):
    body = client.post("/suggest", json={"text": "forgot password, need my account unlocked"}).json()
    assert body["articles"][0]["file"] == "kb-a.md"


def test_suggest_returns_no_article_for_gibberish(client):
    body = client.post("/suggest", json={"text": "zzzz qqqq xxxx"}).json()
    assert body["articles"] == []


def test_suggest_works_with_empty_knowledge_base(trained, tmp_path):
    empty = tmp_path / "empty"
    empty.mkdir()
    with TestClient(create_app(model_dir=trained[0], kb_dir=empty)) as c:
        body = c.post("/suggest", json={"text": "my laptop will not turn on"}).json()
    assert body["articles"] == []
    assert body["category"] == "hardware_issue"


def test_handwritten_accuracy_does_not_regress(trained):
    # Regression guard. The value measured when the project was built was 0.875.
    assert trained[1]["handwritten_accuracy"] >= 0.8


def test_training_is_deterministic(tmp_path):
    first = train(output_dir=tmp_path / "a")
    second = train(output_dir=tmp_path / "b")
    assert first["confusion_matrix"] == second["confusion_matrix"]
    assert first["handwritten_accuracy"] == second["handwritten_accuracy"]
