from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID

from sqlalchemy.orm import selectinload

from configs.Database import get_async_session, BibliographicReference, BookFeedback, Book


class FeedbackRepository:
    db: AsyncSession

    def __init__(self, db: AsyncSession = Depends(get_async_session)) -> None:
        self.db = db

    async def get_by_id(self, feedback_id: int) -> BookFeedback:
        """
        Возвращает отзыв по его ID.
        """
        result = await self.db.execute(
            select(BookFeedback).filter(BookFeedback.id == feedback_id)
        )
        return result.scalar_one_or_none()

    async def get_by_bibliographic_reference_id(self, bibliographic_reference_id: int) -> list[BookFeedback]:
        """
        Возвращает отзывы по ID библиографической справки.
        """
        result = await self.db.execute(
            select(BookFeedback).filter(BookFeedback.bibliographic_reference_id == bibliographic_reference_id)
        )
        return result.scalars().all()

    async def add_feedback(self, user_id: UUID, bibliographic_reference_id: int, rating: float, comment: str = None) -> BookFeedback:
        """
        Добавляет новый отзыв.
        """
        feedback = BookFeedback(
            user_id=user_id,
            bibliographic_reference_id=bibliographic_reference_id,
            rating=rating,
            comment=comment
        )
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    async def update_bibliographic_rating(self, bibliographic_reference_id: int) -> dict:
        """
        Пересчет среднего рейтинга и количества оценок для библиографической справки.
        """
        result = await self.db.execute(
            select(
                func.avg(BookFeedback.rating).label("average"),
                func.count(BookFeedback.id).label("count")
            ).filter(BookFeedback.bibliographic_reference_id == bibliographic_reference_id)
        )
        avg_rating, count = result.one()

        bibliographic = await self.db.execute(
            select(BibliographicReference).filter(BibliographicReference.id == bibliographic_reference_id)
        )
        bibliographic = bibliographic.scalar_one_or_none()

        if bibliographic:
            bibliographic.average_rating = avg_rating or 0.0
            bibliographic.rating_count = count
            await self.db.commit()

        return {"average_rating": avg_rating or 0.0, "rating_count": count}


    async def calculate_global_average_and_k(self):
        """
        Вычисляет средний глобальный рейтинг и параметр сглаживания k.
        """
        # Вычисляем средний глобальный рейтинг
        global_avg_rating_query = await self.db.execute(
            select(func.avg(BookFeedback.rating))
        )
        global_avg_rating = global_avg_rating_query.scalar() or 0.0

        # Вычисляем параметр сглаживания k
        max_rating_count_query = await self.db.execute(
            select(func.max(BibliographicReference.rating_count))
        )
        max_rating_count = max_rating_count_query.scalar() or 0

        # Если в базе данных нет оценок, задаем k = 0
        k = max_rating_count / 10 if max_rating_count > 0 else 0

        return global_avg_rating, k

    async def get_feedbacks_by_book_id(self, book_id: int):
        """
        Возвращает все отзывы на книгу через библиографическую справку.
        """
        # Получаем библиографическую справку по book_id
        result = await self.db.execute(
            select(BookFeedback)
            .join(BibliographicReference)
            .options(selectinload(BookFeedback.user))
            .where(BibliographicReference.book_id == book_id)
        )
        feedbacks = result.scalars().all()

        # теперь добавим каждому пользователю поле `rating`
        for feedback in feedbacks:
            user_id = feedback.user.id
            rating_result = await self.db.execute(
                select(func.avg(BookFeedback.rating))
                .join(BibliographicReference, BookFeedback.bibliographic_reference_id == BibliographicReference.id)
                .join(Book, BibliographicReference.book_id == Book.id)
                .where(Book.user_id == user_id)
            )
            avg_rating = rating_result.scalar()
            feedback.user.rating = round(avg_rating, 2) if avg_rating else 0.0

        return feedbacks