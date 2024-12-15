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

    async def add_feedback(self, user_id: UUID, book_id: int, rating: float, comment: str = None) -> BookFeedback:
        feedback = BookFeedback(user_id=user_id, book_id=book_id, rating=rating, comment=comment)
        self.db.add(feedback)
        await self.db.commit()
        await self.db.refresh(feedback)
        return feedback

    async def update_book_rating(self, book_id: int) -> dict:
        result = await self.db.execute(
            select(
                func.avg(BookFeedback.rating).label("average"),
                func.count(BookFeedback.id).label("count")
            ).filter(BookFeedback.book_id == book_id)
        )
        avg_rating, count = result.one()

        bibliographic = await self.db.execute(
            select(BibliographicReference).filter(BibliographicReference.book_id == book_id)
        )
        bibliographic = bibliographic.scalar_one_or_none()

        if bibliographic:
            bibliographic.average_rating = avg_rating or 0.0
            bibliographic.rating_count = count
            await self.db.commit()

        return {"average_rating": avg_rating or 0.0, "rating_count": count}
