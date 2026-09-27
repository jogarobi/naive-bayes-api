from fastapi import FastAPI

from app.routes import router
from app.services import (
    DatabaseService,
)
from app.utils import increase_csv_field_size_limit

conn = DatabaseService()
conn.create_tables()

increase_csv_field_size_limit()

app = FastAPI()

app.include_router(router)
