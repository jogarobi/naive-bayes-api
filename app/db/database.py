import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.models import Base, LabeledMessage

load_dotenv()

db_url = os.getenv("NEON_POSTGRES_DATABASE_URL")

engine = create_engine(db_url if db_url is not None else "")


def create_tables():
    Base.metadata.create_all(engine)


def create_labeled_messages(messages: list[LabeledMessage]):
    with Session(engine) as session:
        session.add_all(messages)
        session.commit()
