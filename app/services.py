import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models import Base, LabeledMessage, LabeledWord, Measure

load_dotenv()

db_url = os.getenv("NEON_POSTGRES_DATABASE_URL")
engine = create_engine(db_url or "")


class DatabaseService:
    def __init__(self):
        self.engine = engine
        self.create_session = sessionmaker(bind=self.engine)

    def create_tables(self):
        Base.metadata.create_all(self.engine)


class LabeledMessageService(DatabaseService):
    def create_labeled_messages(self, messages: list[LabeledMessage]):
        with self.create_session() as session:
            session.add_all(messages)
            session.commit()


class LabeledWordService(DatabaseService):
    def read_word(self, word: str, is_from_spam: bool):
        with self.create_session() as session:
            statement = select(LabeledWord).where(
                LabeledWord.word.ilike(word),
                LabeledWord.is_from_spam.__eq__(is_from_spam),
            )

            return [
                {"labeled_word": labeled_word.word, "count": labeled_word.occurrences}
                for labeled_word in list(session.scalars(statement).all())
            ]


class MeasureService(DatabaseService):
    def read_measures(self):
        with self.create_session() as session:
            statement = select(Measure)

            measures: dict[str, int] = {}

            for measure in session.scalars(statement).all():
                measures[measure.name] = measure.value

            return measures
