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
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))  # Кто добавил книгу
    bookTitle: Mapped[str] = mapped_column(String, nullable=False)  # Название книги (краткое)
    tags = Column(ARRAY(String))  # Теги книги
    time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow())  # Время добавления

    # Связь с BibliographicReference (1:1)
    bibliographic_reference: Mapped["BibliographicReference"] = relationship(
        "BibliographicReference", back_populates="book", uselist=False
    )

    # Связь с пользователем
    user: Mapped["User"] = relationship("User", back_populates="books")



class BookFeedback(EntityMeta):
    __tablename__ = 'book_feedback'

    id: Mapped[int] = mapped_column(primary_key=True)
    bibliographic_reference_id: Mapped[int] = mapped_column(ForeignKey("bibliographic_references.id"))  # Связь с BibliographicReference
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))  # Кто оставил отзыв
    rating: Mapped[float] = mapped_column(Float, nullable=False)  # Оценка
    comment: Mapped[str] = mapped_column(String, nullable=True)  # Комментарий
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow())  # Время добавления

    # Связь с BibliographicReference
    bibliographic_reference: Mapped["BibliographicReference"] = relationship("BibliographicReference", back_populates="feedbacks")

    # Связь с User
    user: Mapped["User"] = relationship("User")


class BibliographicReference(EntityMeta):
    __tablename__ = 'bibliographic_references'

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), unique=True)  # Связь с Book (1:1)
    title: Mapped[str] = mapped_column(String, nullable=False)  # Полное название
    author: Mapped[str] = mapped_column(String, nullable=False)  # Автор
    publisher: Mapped[str] = mapped_column(String, nullable=False)  # Издательство
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)  # Рейтинг книги
    rating_count: Mapped[int] = mapped_column(Integer, default=0)  # Количество оценок

    # Связь с Book
    book: Mapped["Book"] = relationship("Book", back_populates="bibliographic_reference")

    # Связь с Feedback (1:N)
    feedbacks: Mapped[list["BookFeedback"]] = relationship("BookFeedback", back_populates="bibliographic_reference")


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
