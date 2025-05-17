import datetime
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from sqlalchemy import (
    String, Column, Text, ForeignKey, DateTime, ARRAY, Float, Integer, Boolean
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import (
    sessionmaker, declarative_base, relationship, mapped_column, Mapped
)

from configs.settings import get_settings

# Настройки подключения
settings = get_settings()
DATABASE_URL = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}/{settings.db_name}"

# Инициализация движка и сессии
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

EntityMeta = declarative_base()


# === МОДЕЛИ ===

class User(EntityMeta, SQLAlchemyBaseUserTableUUID):
    __tablename__ = 'users'

    books = relationship("Book", back_populates="user")
    feedbacks = relationship("BookFeedback", back_populates="user")
    reports = relationship("Report", back_populates="user")

    # Чётко указываем foreign_keys
    publication_requests = relationship(
        "PublicationRequest",
        back_populates="user",
        foreign_keys="PublicationRequest.user_id"
    )
    moderated_requests = relationship(
        "PublicationRequest",
        back_populates="moderator",
        foreign_keys="PublicationRequest.moderator_id"
    )

    moderated_sections = relationship("ModeratorSection", back_populates="user")


class Section(EntityMeta):
    __tablename__ = 'sections'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True)

    books = relationship("Book", back_populates="section")
    moderators = relationship("ModeratorSection", back_populates="section")


class Book(EntityMeta):
    __tablename__ = 'books'

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"))
    bookTitle: Mapped[str] = mapped_column(String, nullable=False)
    tags = Column(ARRAY(String))
    time: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    is_public: Mapped[bool] = mapped_column(default=False)

    user = relationship("User", back_populates="books")
    section = relationship("Section", back_populates="books")
    bibliographic_reference = relationship("BibliographicReference", back_populates="book", uselist=False)
    publication_request = relationship("PublicationRequest", back_populates="book", uselist=False)


class BibliographicReference(EntityMeta):
    __tablename__ = 'bibliographic_references'

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), unique=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str] = mapped_column(String, nullable=False)
    publisher: Mapped[str] = mapped_column(String, nullable=False)
    isbn : Mapped[str] = mapped_column(String, nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    city: Mapped[str] = mapped_column(String, nullable=False)
    pages: Mapped[int] = mapped_column(Integer, nullable=False)
    average_rating: Mapped[float] = mapped_column(Float, default=0.0)
    rating_count: Mapped[int] = mapped_column(Integer, default=0)
    book = relationship("Book", back_populates="bibliographic_reference")
    feedbacks = relationship("BookFeedback", back_populates="bibliographic_reference")


class BookFeedback(EntityMeta):
    __tablename__ = 'book_feedback'

    id: Mapped[int] = mapped_column(primary_key=True)
    bibliographic_reference_id: Mapped[int] = mapped_column(ForeignKey("bibliographic_references.id"))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    comment: Mapped[str] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)

    bibliographic_reference = relationship("BibliographicReference", back_populates="feedbacks")
    user = relationship("User", back_populates="feedbacks")


class Report(EntityMeta):
    __tablename__ = 'reports'

    id: Mapped[int] = mapped_column(primary_key=True)
    text = Column(Text)
    userId: Mapped[str] = mapped_column(ForeignKey("users.id"))
    user = relationship("User", back_populates="reports")




class PublicationRequest(EntityMeta):
    __tablename__ = 'publication_requests'

    id: Mapped[int] = mapped_column(primary_key=True)
    book_id: Mapped[int] = mapped_column(ForeignKey("books.id"), unique=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    moderator_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=True)

    status: Mapped[str] = mapped_column(String, default='pending')
    moderator_comment: Mapped[str] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(default=datetime.datetime.utcnow)
    reviewed_at: Mapped[datetime.datetime] = mapped_column(nullable=True)

    book = relationship("Book", back_populates="publication_request")
    user = relationship("User", back_populates="publication_requests", foreign_keys=[user_id])
    moderator = relationship("User", back_populates="moderated_requests", foreign_keys=[moderator_id])


class ModeratorSection(EntityMeta):
    __tablename__ = 'moderator_section'

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), primary_key=True)
    section_id: Mapped[int] = mapped_column(ForeignKey("sections.id"), primary_key=True)

    user = relationship("User", back_populates="moderated_sections")
    section = relationship("Section", back_populates="moderators")


# === ХЕЛПЕРЫ ===

async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(EntityMeta.metadata.create_all)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


async def get_user_db(session: AsyncSession = Depends(get_async_session)):
    yield SQLAlchemyUserDatabase(session, User)
