import pytest

from app.utils import Classifier

MEASURES = {
    "total_messages": 100,
    "spam_messages": 40,
    "not_spam_messages": 60,
    "total_spam_words": 200,
    "total_not_spam_words": 300,
    "unique_spam_words": 50,
    "unique_not_spam_words": 80,
}


WORD_COUNTS = {
    ("free", True): 30,
    ("free", False): 1,
    ("meeting", True): 1,
    ("meeting", False): 40,
}


@pytest.fixture
def classifier(monkeypatch):
    monkeypatch.setattr(
        "app.utils.MeasureService.read_measures",
        lambda self: dict(MEASURES),
    )
    monkeypatch.setattr(
        "app.utils.LabeledWordService.read_words",
        lambda self, words: {
            label: occurrences
            for label, occurrences in WORD_COUNTS.items()
            if label[0] in words
        },
    )
    return Classifier()


def test_probabilities_sum_to_one(classifier):
    spam, not_spam = classifier.get_message_prediction("free free free")
    assert spam + not_spam == pytest.approx(1.0)


def test_spam_words_predict_spam(classifier):
    spam, not_spam = classifier.get_message_prediction("free free")
    assert spam > not_spam


def test_ham_words_predict_not_spam(classifier):
    spam, not_spam = classifier.get_message_prediction("meeting meeting")
    assert not_spam > spam


def test_unknown_words_give_valid_probabilities(classifier):
    spam, not_spam = classifier.get_message_prediction("zzz qqq")
    assert 0.0 < spam < 1.0
    assert spam + not_spam == pytest.approx(1.0)
    assert spam > not_spam


def test_smoother_is_total_unique_words(classifier):
    assert classifier.smoother == (
        MEASURES["unique_spam_words"] + MEASURES["unique_not_spam_words"]
    )
