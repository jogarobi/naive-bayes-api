import csv
import hashlib
from io import StringIO

from fastapi import FastAPI, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError

from app.db.database import (
    create_labeled_messages,
    create_tables,
    read_measures,
    read_word,
)
from app.db.models import LabeledMessage
from app.utils import increase_csv_field_size_limit, split_str

app = FastAPI()

increase_csv_field_size_limit()
create_tables()


@app.get("/message/{id}")
async def read_item(id):
    return {"message": f"Your message ID is {id}"}


@app.post("/dataset/ingest")
async def read_dataset(file: UploadFile):
    if file.content_type != "text/csv":
        raise HTTPException(status_code=400, detail="Only CSV files are supported.")

    contents = await file.read()

    try:
        buffer = StringIO(contents.decode("utf-8"))
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=400,
            detail="There was an error decoding your file, please check the format and encoding.",
        )

    parser = csv.DictReader(buffer)

    labeled_messages: list[LabeledMessage] = []

    for row in parser:
        message = row["message"].lower()
        is_spam = row["is_spam"]

        if len(message) > 0 and len(is_spam) > 0:
            try:
                labeled_messages.append(
                    LabeledMessage(
                        message=message,
                        message_hash=hashlib.md5(message.encode()).hexdigest(),
                        is_spam=int(is_spam),
                    )
                )
            except ValueError:
                raise HTTPException(
                    status_code=404, detail=f"ValueError: {row['is_spam']}"
                )

    try:
        create_labeled_messages(labeled_messages)
    except IntegrityError:
        raise HTTPException(
            status_code=400,
            detail="There is data that already exists in the database. Please remove duplicates or rows that were uploaded before.",
        )

    return {
        "file": {"name": file.filename, "size": file.size},
    }


@app.post("/message/predict")
async def classify_message(message: str):

    measures = read_measures()

    smoother = measures["unique_spam_words"] + measures["unique_non_spam_words"]

    def get_word_likelihood(word: str, is_spam: bool) -> float:
        count = 1
        prop = "total_spam_words" if is_spam else "total_non_spam_words"

        dataset_word = read_word(word, is_from_spam=is_spam)

        if len(dataset_word) > 0:
            count += dataset_word[0]["count"]

        return count / (measures[prop] + smoother)

    def get_message_prediction(message: str) -> tuple[float, float]:
        words = split_str(message)

        spam_prior_probability = measures["spam_messages"] / measures["total_messages"]
        not_spam_prior_probability = (
            measures["non_spam_messages"] / measures["total_messages"]
        )

        spam_probabilities: list[float] = []
        not_spam_probabilities: list[float] = []

        for word in words:
            normalized_word = word.lower()
            spam_probabilities.append(
                get_word_likelihood(normalized_word, is_spam=True)
            )
            not_spam_probabilities.append(
                get_word_likelihood(normalized_word, is_spam=False)
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

    prediction = get_message_prediction(message)
    spam_prediction = prediction[0] * 100
    not_spam_prediction = prediction[1] * 100

    return {
        "prediction": "spam" if spam_prediction > not_spam_prediction else "not spam",
        "details": {
            "spam": f"{(spam_prediction):.2f}%",
            "not_spam": f"{(not_spam_prediction):.2f}%",
        },
    }
