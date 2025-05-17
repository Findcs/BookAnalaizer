from fastapi import Depends, HTTPException
from repositories.FeedbackRepository import FeedbackRepository
from repositories.BibliographicReferenceRepository import BibliographicReferenceRepository
from uuid import UUID


class FeedbackService:
    def __init__(
        self,
        repository: FeedbackRepository = Depends(),
        bibliographic_repository: BibliographicReferenceRepository = Depends()
    ):
        self.repository = repository
        self.bibliographic_repository = bibliographic_repository

    async def add_feedback(self, user_id: UUID, bibliographic_reference_id: int, rating: float, comment: str = None) -> dict:
        """
        Добавляет отзыв и обновляет рейтинг библиографической справки.
        """
        # Проверяем, существует ли BibliographicReference
        bibliographic = await self.bibliographic_repository.get_by_id(bibliographic_reference_id)
        if not bibliographic:
            raise HTTPException(status_code=404, detail="Bibliographic reference not found")

        # Добавляем отзыв
        feedback = await self.repository.add_feedback(user_id, bibliographic_reference_id, rating, comment)

        # Пересчитываем средний рейтинг библиографической справки
        bibliographic_rating = await self.repository.update_bibliographic_rating(bibliographic_reference_id)

        return {
            "message": "Feedback added successfully",
            "feedback_id": feedback.id,
            "average_rating": bibliographic_rating["average_rating"],
            "rating_count": bibliographic_rating["rating_count"]
        }

    async def get_by_bibliographic_reference_id(self, bibliographic_reference_id: int) -> list[dict]:
        """
        Возвращает отзывы по ID библиографической справки.
        """
        return await self.repository.get_by_bibliographic_reference_id(bibliographic_reference_id)


    async def get_feedbacks_for_book(self, book_id: int):
        feedbacks = await self.repository.get_feedbacks_by_book_id(book_id)
        if not feedbacks:
            raise HTTPException(status_code=404, detail="Feedback not found")
        return feedbacks
