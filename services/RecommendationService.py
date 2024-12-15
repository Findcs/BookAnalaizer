from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from repositories.FeedbackRepository import FeedbackRepository
from repositories.BibliographicReferenceRepository import BibliographicReferenceRepository
from math import sin, pi, exp
import datetime


class RecommendationService:
    """
    Сервис для реализации алгоритма рекомендаций.
    """

    def __init__(
        self,
        feedback_repository: FeedbackRepository = Depends(),
        bibliographic_repository: BibliographicReferenceRepository = Depends()
    ):
        self.feedback_repository = feedback_repository
        self.bibliographic_repository = bibliographic_repository

    async def get_recommendations(self, bibliographic_reference_id: int, top_n: int = 5):
        """
        Находит рекомендации для книги на основе тегов, рейтинга, популярности и актуальности.
        """
        # Шаг 1: Получить текущую библиографическую справку и связанные теги книги
        reference = await self.bibliographic_repository.get_by_id(bibliographic_reference_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Bibliographic reference not found")

        book = await self.bibliographic_repository.get_book_by_bibliographic_reference_id(bibliographic_reference_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        current_tags = book.tags

        # Шаг 2: Получить глобальный средний рейтинг и параметр сглаживания k
        global_avg_rating, k = await self.feedback_repository.calculate_global_average_and_k()

        # Шаг 3: Получить все библиографические справки и связанные книги
        all_references = await self.bibliographic_repository.get_all_with_books()

        recommendations = []

        # Шаг 4: Рассчитать веса для всех книг
        for ref, b in all_references:
            if ref.id == bibliographic_reference_id:
                continue  # Пропускаем текущую книгу

            # Схожесть тегов с синусным весом
            tag_weight = 0
            for tag in set(current_tags).intersection(set(b.tags)):
                if tag in current_tags:
                    index = current_tags.index(tag)
                    tag_weight += sin((pi / 2) * (len(current_tags) - index) / len(current_tags))

            # Популярность
            popularity_weight = ref.rating_count

            # Взвешенный рейтинг
            weighted_rating = (ref.rating_count / (ref.rating_count + k) * ref.average_rating) + (
                k / (ref.rating_count + k) * global_avg_rating
            )

            # Актуальность
            delta_days = (datetime.datetime.utcnow() - b.time).days
            alpha = 0.01
            time_weight = exp(-alpha * delta_days)

            # Итоговый вес
            final_weight = (
                tag_weight * 0.4 +
                popularity_weight * 0.2 +
                weighted_rating * 0.3 +
                time_weight * 0.1
            )

            recommendations.append((ref, final_weight))

        # Шаг 5: Сортировка по итоговому весу и возврат результата
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [r[0] for r in recommendations[:top_n]]
