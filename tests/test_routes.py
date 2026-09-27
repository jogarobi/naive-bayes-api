import pytest
from sqlalchemy.exc import IntegrityError


def _csv(body: str):
    return {"file": ("data.csv", body, "text/csv")}


@pytest.fixture
def mock_create(monkeypatch):
    monkeypatch.setattr(
        "app.routes.LabeledMessageService.create_labeled_messages",
        lambda self, messages: None,
    )


class TestIngestDataset:
    def test_happy_path(self, client, mock_create):
        body = "message,is_spam\nwin free money,1\nsee you at lunch,0\n"
        resp = client.post("/dataset/ingest", files=_csv(body))
        assert resp.status_code == 200
        assert resp.json() == {"file": {"name": "data.csv", "size": len(body)}}

    def test_rejects_non_csv(self, client, mock_create):
        resp = client.post(
            "/dataset/ingest",
            files={"file": ("data.txt", "hi", "text/plain")},
        )
        assert resp.status_code == 400
        assert "CSV" in resp.json()["detail"]

    def test_rejects_bad_is_spam_value(self, client, mock_create):
        body = "message,is_spam\nhello,notanumber\n"
        resp = client.post("/dataset/ingest", files=_csv(body))
        assert resp.status_code == 400
        assert "ValueError" in resp.json()["detail"]

    def test_skips_blank_rows(self, client, mock_create):
        # Blank message and blank label rows are ignored, not errors.
        body = "message,is_spam\n,1\nhello,\nreal message,1\n"
        resp = client.post("/dataset/ingest", files=_csv(body))
        assert resp.status_code == 200

    def test_duplicate_data_returns_400(self, client, monkeypatch):
        def raise_integrity(self, messages):
            raise IntegrityError("stmt", {}, Exception("dup"))

        monkeypatch.setattr(
            "app.routes.LabeledMessageService.create_labeled_messages",
            raise_integrity,
        )
        body = "message,is_spam\nwin free money,1\n"
        resp = client.post("/dataset/ingest", files=_csv(body))
        assert resp.status_code == 400
        assert "already exists" in resp.json()["detail"]


class TestClassifyMessage:
    @pytest.fixture
    def fake_classifier(self, monkeypatch):
        def make(spam, not_spam):
            class FakeClassifier:
                def __init__(self):
                    pass

                def get_message_prediction(self, message):
                    return (spam, not_spam)

            monkeypatch.setattr("app.routes.Classifier", FakeClassifier)

        return make

    def test_predicts_spam(self, client, fake_classifier):
        fake_classifier(0.9, 0.1)
        resp = client.post("/message/predict", params={"message": "free money"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["prediction"] == "spam"
        assert body["details"] == {"spam": "90.00%", "not_spam": "10.00%"}

    def test_predicts_not_spam(self, client, fake_classifier):
        fake_classifier(0.2, 0.8)
        resp = client.post("/message/predict", params={"message": "lunch tomorrow"})
        assert resp.json()["prediction"] == "not spam"
