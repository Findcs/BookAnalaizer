from fastapi import Depends
from repositories.FeedbackRepository import FeedbackRepository
from uuid import UUID


class FeedbackService:
    """
    Сервис для работы с отзывами о книгах и обновления их рейтинга.
    """

    def __init__(self, repository: FeedbackRepository = Depends()):
        self.repository = repository

    async def add_feedback(self, user_id: UUID, book_id: int, rating: float, comment: str = None) -> dict:
        """
        Добавляет отзыв и обновляет рейтинг книги.
        """
        # Добавляем отзыв в базу данных
        feedback = await self.repository.add_feedback(user_id, book_id, rating, comment)

        # Пересчитываем средний рейтинг книги
        book_rating = await self.repository.update_book_rating(book_id)

        # Возвращаем результат
        return {
            "message": "Feedback added successfully",
            "feedback_id": feedback.id,
            "average_rating": book_rating["average_rating"],
            "rating_count": book_rating["rating_count"]
        }
