import csv
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
            self.measures["unique_spam_words"] + self.measures["unique_non_spam_words"]
        )

    def get_word_likelihood(self, word: str, is_spam: bool) -> float:
        count = 1
        word_type = "total_spam_words" if is_spam else "total_non_spam_words"

        word_from_dataset = self.labeled_word_service.read_word(
            word, is_from_spam=is_spam
        )

        if len(word_from_dataset) > 0:
            count += word_from_dataset[0]["count"]

        return count / (self.measures[word_type] + self.smoother)

    def get_message_prediction(self, message: str) -> tuple[float, float]:
        words = message.lower().split()

        prior_probabilities: dict[str, float] = {
            "spam": self.measures["spam_messages"] / self.measures["total_messages"],
            "not_spam": self.measures["non_spam_messages"]
            / self.measures["total_messages"],
        }

        likelihoods: dict[str, list[float]] = {"spam": [], "not_spam": []}

        for word in words:
            normalized_word = word.lower()
            likelihoods["spam"].append(
                self.get_word_likelihood(normalized_word, is_spam=True)
            )
            likelihoods["not_spam"].append(
                self.get_word_likelihood(normalized_word, is_spam=False)
            )

        total_not_spam_likelihood = likelihoods["not_spam"][0]
        total_spam_likelihood = likelihoods["spam"][0]

        for index, current_probability in enumerate(likelihoods["spam"]):
            if index == 0:
                continue

            total_spam_likelihood *= current_probability

        for index, current_probability in enumerate(likelihoods["not_spam"]):
            if index == 0:
                continue

            total_not_spam_likelihood *= current_probability

        total_spam_likelihood *= prior_probabilities["spam"]
        total_not_spam_likelihood *= prior_probabilities["not_spam"]

        spam_probability = total_spam_likelihood / (
            total_spam_likelihood + total_not_spam_likelihood
        )

        not_spam_probability = total_not_spam_likelihood / (
            total_spam_likelihood + total_not_spam_likelihood
        )

        return (spam_probability, not_spam_probability)
