import csv
import math
import sys

from app.services import LabeledWordService, MeasureService


def increase_csv_field_size_limit():
    max_int = sys.maxsize
    while True:
        try:
            csv.field_size_limit(max_int)
            break
        except OverflowError:
            max_int = int(max_int / 10)


class Classifier:
    def __init__(self):
        self.labeled_word_service = LabeledWordService()
        self.measure_service = MeasureService()
        self.measures = self.measure_service.read_measures()
        self.smoother = (
            self.measures["unique_spam_words"] + self.measures["unique_not_spam_words"]
        )

    def get_word_likelihoods(
        self, words: list[tuple[str, bool]]
    ) -> dict[tuple[str, bool], float]:
        words_from_dataset: dict[tuple[str, bool], int] = (
            self.labeled_word_service.read_words(words)
        )

        likelihoods: dict[tuple[str, bool], float] = {}

        for word, is_spam in words:
            count = 1
            label = "total_spam_words" if is_spam else "total_not_spam_words"

            if (word, is_spam) in words_from_dataset:
                count += words_from_dataset[(word, is_spam)]

            likelihoods[(word, is_spam)] = count / (
                self.measures[label] + self.smoother
            )

        return likelihoods

    def get_message_prediction(self, message: str) -> tuple[float, float]:
        words = message.lower().split()

        scores = {}

        for label in ("spam", "not_spam"):
            is_spam = label == "spam"

            prior_probability = (
                self.measures[f"{'spam' if is_spam else 'not_spam'}_messages"]
                / self.measures["total_messages"]
            )

            likelihoods = self.get_word_likelihoods([(word, is_spam) for word in words])

            scores[label] = math.log(prior_probability) + sum(
                math.log(likelihood) for likelihood in likelihoods.values()
            )

        highest_score = max(scores.values())
        final_probabilities = {
            label: math.exp(score - highest_score) for label, score in scores.items()
        }
        total_probability = sum(final_probabilities.values())

        return (
            final_probabilities["spam"] / total_probability,
            final_probabilities["not_spam"] / total_probability,
        )
