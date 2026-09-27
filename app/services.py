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
    def read_words(self, words: list[tuple[str, bool]]) -> dict[tuple[str, bool], int]:
        with create_session() as session:
            spam_statement = select(LabeledWord).where(
                LabeledWord.word.in_(
                    word for word, is_from_spam in words if is_from_spam
                ),
                LabeledWord.is_from_spam.__eq__(True),
            )

            not_spam_statement = select(LabeledWord).where(
                LabeledWord.word.in_(
                    word for word, is_from_spam in words if not is_from_spam
                ),
                LabeledWord.is_from_spam.__eq__(False),
            )

            word_counts: dict[tuple[str, bool], int] = {}

            for labeled_word in list(session.scalars(spam_statement).all()):
                word_counts[(labeled_word.word, True)] = labeled_word.occurrences

            for labeled_word in list(session.scalars(not_spam_statement).all()):
                word_counts[(labeled_word.word, False)] = labeled_word.occurrences

            return word_counts


class MeasureService:
    def read_measures(self):
        with create_session() as session:
            statement = select(Measure)

            measures: dict[str, int] = {}

            for measure in session.scalars(statement).all():
                measures[measure.name] = measure.value

            return measures
