import os
from enum import Enum

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.db.models import Base, LabeledMessage, LabeledWord, Measure

load_dotenv()

db_url = os.getenv("NEON_POSTGRES_DATABASE_URL")

engine = create_engine(db_url if db_url is not None else "")


class DATASET_MEASURES(Enum):
    TOTAL_MESSAGES = "total_messages"
    TOTAL_SPAM_MESSAGES = "spam_messages"
    TOTAL_NON_SPAM_MESSAGES = "non_spam_messages"
    TOTAL_NON_SPAM_WORDS = "total_non_spam_words"
    TOTAL_SPAM_WORDS = "total_spam_words"
    TOTAL_UNIQUE_SPAM_WORDS = "unique_spam_words"
    TOTAL_UNIQUE_NON_SPAM_WORDS = "unique_non_spam_words"


def create_tables():
    Base.metadata.create_all(engine)


def create_labeled_messages(messages: list[LabeledMessage]):
    with Session(engine) as session:
        session.add_all(messages)
        session.commit()


def read_measures() -> dict[str, int]:
    session = Session(engine)

    statement = select(Measure)

    measures: dict[str, int] = {}

    for measure in session.scalars(statement).all():
        measures[measure.name] = measure.value

    return measures


def read_word(word: str, is_from_spam: bool):
    session = Session(engine)

    statement = select(LabeledWord).where(
        LabeledWord.word.ilike(word), LabeledWord.is_from_spam.__eq__(is_from_spam)
    )

    return [
        {"labeled_word": labeled_word.word, "count": labeled_word.occurrences}
        for labeled_word in list(session.scalars(statement).all())
    ]
