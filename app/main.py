import csv
import hashlib
from io import StringIO

from fastapi import FastAPI, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError

from app.models import LabeledMessage
from app.services import (
    DatabaseService,
    LabeledMessageService,
)
from app.utils import Classifier, increase_csv_field_size_limit

app = FastAPI()

increase_csv_field_size_limit()

conn = DatabaseService()
conn.create_tables()


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
        service = LabeledMessageService()

        service.create_labeled_messages(labeled_messages)
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
    classifier = Classifier()

    prediction = classifier.get_message_prediction(message)
    spam_prediction = prediction[0] * 100
    not_spam_prediction = prediction[1] * 100

    return {
        "prediction": "spam" if spam_prediction > not_spam_prediction else "not spam",
        "details": {
            "spam": f"{(spam_prediction):.2f}%",
            "not_spam": f"{(not_spam_prediction):.2f}%",
        },
    }
