import datetime
from typing import AsyncGenerator

from fastapi import Depends
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase, SQLAlchemyBaseUserTableUUID
from sqlalchemy import String, Column, Text, ForeignKey, LargeBinary, DateTime, ARRAY, Float, Integer
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
    result: Mapped["Result"] = relationship("Result", back_populates="Book")
    book = Column(LargeBinary)
    bookTitle = Column(String)
    author = Column(String)
    rating = Column(Float)
    rating_ammount = Column(Integer)



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
