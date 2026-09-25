import csv
import sys

from app.services import LabeledWordService, MeasureService


class Utils:
    @staticmethod
    def increase_csv_field_size_limit():
        max_int = sys.maxsize
        while True:
            try:
                csv.field_size_limit(max_int)
                break
            except OverflowError:
                max_int = int(max_int / 10)

    @staticmethod
    def split_str(text: str, delimiter: str = " ") -> list[str]:
        current_word = ""
        split_output = []

        for character in text.lstrip() + delimiter:
            if character != delimiter:
                current_word += character
            else:
                split_output.append(current_word)
                current_word = ""

        return split_output


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
        prop = "total_spam_words" if is_spam else "total_non_spam_words"

        dataset_word = self.labeled_word_service.read_word(word, is_from_spam=is_spam)

        if len(dataset_word) > 0:
            count += dataset_word[0]["count"]

        return count / (self.measures[prop] + self.smoother)

    def get_message_prediction(self, message: str) -> tuple[float, float]:
        words = Utils.split_str(message)

        spam_prior_probability = self.measures["spam_messages"] / self.measures["total_messages"]
        not_spam_prior_probability = (
            self.measures["non_spam_messages"] / self.measures["total_messages"]
        )

        spam_probabilities: list[float] = []
        not_spam_probabilities: list[float] = []

        for word in words:
            normalized_word = word.lower()
            spam_probabilities.append(
                self.get_word_likelihood(normalized_word, is_spam=True)
            )
            not_spam_probabilities.append(
                self.get_word_likelihood(normalized_word, is_spam=False)
            )

        total_not_spam_likelihood = not_spam_probabilities[0]
        total_spam_likelihood = spam_probabilities[0]

        for index, current_probability in enumerate(spam_probabilities):
            if index == 0:
                continue

            total_spam_likelihood *= current_probability

        for index, current_probability in enumerate(not_spam_probabilities):
            if index == 0:
                continue

            total_not_spam_likelihood *= current_probability

        total_spam_likelihood *= spam_prior_probability
        total_not_spam_likelihood *= not_spam_prior_probability

        spam_probability = total_spam_likelihood / (
            total_spam_likelihood + total_not_spam_likelihood
        )

        not_spam_probability = total_not_spam_likelihood / (
            total_spam_likelihood + total_not_spam_likelihood
        )

        return (spam_probability, not_spam_probability)
