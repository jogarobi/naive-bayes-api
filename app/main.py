from fastapi import FastAPI

from app.routes import router
from app.services import (
    DatabaseService,
)
from app.utils import increase_csv_field_size_limit

increase_csv_field_size_limit()

conn = DatabaseService()
conn.create_tables()

app = FastAPI()

app.include_router(router)
