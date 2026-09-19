import csv
import hashlib
from io import StringIO

from fastapi import FastAPI, HTTPException, UploadFile
from sqlalchemy.exc import IntegrityError

from app.db.database import create_labeled_messages, create_tables
from app.db.models import LabeledMessage
from app.utils import increase_csv_field_size_limit

app = FastAPI()

increase_csv_field_size_limit()
create_tables()


@app.get("/")
async def read_root():
    return {"message": "Hello World!"}


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

    errors: list[str] = []
    data: list[LabeledMessage] = []

    for row in parser:
        message = row["message"].lower()
        is_spam = row["is_spam"]

        if len(message) > 0 and len(is_spam) > 0:
            try:
                data.append(
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
            create_labeled_messages(data)
        except IntegrityError:
            raise HTTPException(
                status_code=400,
                detail="There is data that already exists in the database. Please remove duplicates or rows that were uploaded before.",
            )

    return {
        "file": {"name": file.filename, "size": file.size},
        "operation": {"errors": errors},
    }
