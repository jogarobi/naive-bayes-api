import csv
from io import StringIO

from fastapi import FastAPI, HTTPException, UploadFile

from app.utils import increase_csv_field_size_limit

app = FastAPI()

increase_csv_field_size_limit()


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

    data = []

    for row in parser:
        data.append(row.copy())

    return {"file": {"name": file.filename, "size": file.size}, "data": data}
