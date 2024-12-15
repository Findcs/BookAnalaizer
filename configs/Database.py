import datetime
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from sqlalchemy import String, Column, Text, ForeignKey, LargeBinary, DateTime, ARRAY, Float, Integer, Boolean
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base, relationship, mapped_column, Mapped

from configs.settings import get_settings

settings = get_settings()
DATABASE_URL = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}/{settings.db_name}"

engine = create_async_engine(
    DATABASE_URL
)

async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

EntityMeta = declarative_base()


class User(EntityMeta, SQLAlchemyBaseUserTableUUID):
    __tablename__ = 'users'

    books = relationship("Book", back_populates="user")
    feedbacks: Mapped[list["BookFeedback"]] = relationship("BookFeedback", back_populates="user")
    reports = relationship("Report", back_populates="user")


class Report(EntityMeta):
    __tablename__ = 'reports'

    id: Mapped[int] = mapped_column(primary_key=True)
    text = Column(Text)
    userId: Mapped[str] = mapped_column(ForeignKey("users.id"))
    user = relationship("User", back_populates="reports")


class Book(EntityMeta):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True)
    time = Column(DateTime, default=datetime.datetime.utcnow())
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    user: Mapped["User"] = relationship("User", back_populates="books")
    tags = Column(ARRAY(String))
    book = Column(LargeBinary)
    bookTitle = Column(String)
    rating = Column(Float, default=0.0)
    rating_ammount = Column(Integer, default=0)

    # Новые связи
    bibliographic_reference: Mapped["BibliographicReference"] = relationship(
        "BibliographicReference", back_populates="book", uselist=False
    )
    feedbacks: Mapped[list["BookFeedback"]] = relationship("BookFeedback", back_populates="book")



class BookFeedback(EntityMeta):
    __tablename__ = 'book_feedback'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"))
    rating: Mapped[float] = mapped_column(Float)  # Оценка пользователя
    comment: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)

    # Связи
    user: Mapped["User"] = relationship("User", back_populates="feedbacks")
    book: Mapped["Book"] = relationship("Book", back_populates="feedbacks")


class BibliographicReference(EntityMeta):
    __tablename__ = 'bibliographic_references'

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), unique=True)  # Связь с книгой
    title: Mapped[str] = mapped_column(String)
    author: Mapped[str] = mapped_column(String)
    publisher: Mapped[str] = mapped_column(String)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    views: Mapped[int] = mapped_column(Integer, default=0)  # Количество просмотров книги

    # Связь с книгой
    book: Mapped["Book"] = relationship("Book", back_populates="bibliographic_reference")

class Result(EntityMeta):
    __tablename__ = 'results'

    id: Mapped[int] = mapped_column(primary_key=True)
    time = Column(DateTime, default=datetime.datetime.utcnow)
    BookId: Mapped[int] = mapped_column(ForeignKey("books.id"))
    Book = relationship("Book")
    tags = Column(ARRAY(String))
    bookTitle = Column(String)


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(EntityMeta.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
