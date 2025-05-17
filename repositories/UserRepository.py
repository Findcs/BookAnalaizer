from fastapi import Depends
from sqlalchemy import select, func
from sqlalchemy.orm import Session

from configs.Database import User, get_async_session, BookFeedback, BibliographicReference, Book


class UserRepository:
    db: Session

    def __init__(
            self, db: Session = Depends(get_async_session)
    ) -> None:
        self.db = db

    def create(self, user: User) -> User:
        self.db.add(user)
        return user

    async def get_user_rating(self, user_id: str) -> float:
        """
        Возвращает рейтинг пользователя как среднюю оценку всех его публикаций.
        Если публикаций или оценок нет — возвращает 0.0.
        """
        result = await self.db.execute(
            select(func.avg(BookFeedback.rating))
            .join(BibliographicReference, BookFeedback.bibliographic_reference_id == BibliographicReference.id)
            .join(Book, BibliographicReference.book_id == Book.id)
            .where(Book.user_id == user_id)
        )
        average = result.scalar()
        return round(average, 2) if average is not None else 0.0