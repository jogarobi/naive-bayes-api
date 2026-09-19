from __future__ import annotations

from typing import Optional

from sqlalchemy import DateTime, String, Text, UniqueConstraint, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LabeledMessage(Base):
    __tablename__ = "labeled_messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    message: Mapped[str] = mapped_column(Text())
    message_hash: Mapped[str] = mapped_column(String(32), unique=True)
    is_spam: Mapped[bool]
    created_at: Mapped[str] = mapped_column(
        DateTime(), server_default=text("TIMEZONE('utc', NOW())")
    )


class LabeledWord(Base):
    __tablename__ = "labeled_words"

    id: Mapped[int] = mapped_column(primary_key=True)
    word: Mapped[str] = mapped_column(String(45))
    occurrences: Mapped[int]
    is_from_spam: Mapped[bool]
    created_at: Mapped[str] = mapped_column(
        DateTime(), server_default=text("TIMEZONE('utc', NOW())")
    )

    __table_args__ = (
        UniqueConstraint("word", "is_from_spam", name="uq_classified_word"),
    )


class Measures(Base):
    __tablename__ = "measures"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(45), unique=True)
    value: Mapped[int]
    created_at: Mapped[str] = mapped_column(
        DateTime(), server_default=text("TIMEZONE('utc', NOW())")
    )
    updated_at: Mapped[Optional[str]] = mapped_column(DateTime())
