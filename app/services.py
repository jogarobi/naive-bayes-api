import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from app.models import Base, LabeledMessage, LabeledWord, Measure

load_dotenv()

db_url = os.getenv("NEON_POSTGRES_DATABASE_URL")
engine = create_engine(db_url or "")
create_session = sessionmaker(bind=engine)


def create_tables():
    Base.metadata.create_all(engine)


class LabeledMessageService:
    def create_labeled_messages(self, messages: list[LabeledMessage]):
        with create_session() as session:
            session.add_all(messages)
            session.commit()


class LabeledWordService:
    def read_words(self, words: list[str]) -> dict[tuple[str, bool], int]:
        with create_session() as session:
            statement = select(LabeledWord).where(LabeledWord.word.in_(words))

            return {
                (word.word, word.is_from_spam): word.occurrences
                for word in session.scalars(statement).all()
            }


class MeasureService:
    def read_measures(self) -> dict[str, int]:
        with create_session() as session:
            statement = select(Measure)

            return {
                measure.name: measure.value
                for measure in session.scalars(statement).all()
            }
