from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from uuid import UUID
from configs.Database import get_async_session , BibliographicReference, BookFeedback


class FeedbackRepository:
    db: AsyncSession

    def __init__(self, db: AsyncSession = Depends(get_async_session)) -> None:
        self.db = db

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