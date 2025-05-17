from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from math import sin, pi, exp
import datetime
from repositories.FeedbackRepository import FeedbackRepository
from repositories.BibliographicReferenceRepository import BibliographicReferenceRepository
from repositories.RequestRepository import RequestRepository


class RecommendationService:
    """
    Сервис для реализации алгоритма рекомендаций на основе гибридного подхода.

    Алгоритм учитывает следующие факторы:
    1. Схожесть тегов между книгами (с использованием синусного веса).
    2. Популярность книги (количество оценок).
    3. Взвешенный рейтинг книги (с учетом количества оценок и глобального среднего рейтинга).
    4. Актуальность книги (снижение веса старых книг с использованием временного коэффициента).

    Итоговая оценка формируется на основе взвешенной суммы нормализованных факторов.
    """

    # Весовые коэффициенты для факторов
    TAG_WEIGHT_COEFFICIENT = 0.4  # Вес схожести тегов
    POPULARITY_COEFFICIENT = 0.2  # Вес популярности книги
    RATING_COEFFICIENT = 0.3  # Вес взвешенного рейтинга
    TIME_WEIGHT_COEFFICIENT = 0.1  # Вес актуальности книги

    # Параметр для временного убывания актуальности книги
    TIME_DECAY_ALPHA = 0.01

    def __init__(
        self,
        feedback_repository: FeedbackRepository = Depends(),
        bibliographic_repository: BibliographicReferenceRepository = Depends(),
        request_repository: RequestRepository = Depends()
    ):
        """
        Инициализация сервисов для работы с отзывами и библиографическими справками.
        """
        self.feedback_repository = feedback_repository
        self.bibliographic_repository = bibliographic_repository
        self.request_repository = request_repository

    async def get_recommendations(self, bibliographic_reference_id: int, top_n: int = 5):
        """
        Находит рекомендации для книги на основе тегов, рейтинга, популярности и актуальности.

        :param bibliographic_reference_id: ID библиографической справки для текущей книги.
        :param top_n: Количество рекомендаций для возврата.
        :return: Список рекомендованных книг с их итоговыми весами.
        """

        #book = await self.bibliographic_repository.get_book_by_bibliographic_reference_id(bibliographic_reference_id)

        book = await self.request_repository.get_by_id(bibliographic_reference_id)
        if not book:
            raise HTTPException(status_code=404, detail="Book not found")

        current_tags = book.tags

        # Шаг 2: Получить глобальный средний рейтинг и параметр сглаживания k
        global_avg_rating, k = await self.feedback_repository.calculate_global_average_and_k()

        # Шаг 3: Получить все библиографические справки и связанные книги
        all_references = await self.bibliographic_repository.get_all_with_books()

        # Определение максимальных значений для нормализации
        max_popularity = max(ref.rating_count for ref, _ in all_references)

        recommendations = []

        # Шаг 4: Рассчитать веса для всех книг
        for ref, b in all_references:
            if ref.id == bibliographic_reference_id:
                continue  # Пропускаем текущую книгу

            # Схожесть тегов с синусным весом
            tag_weight = 0
            max_possible_tag_weight = len(current_tags) * sin(pi / 2)
            for tag in set(current_tags).intersection(set(b.tags)):
                if tag in current_tags:
                    index = current_tags.index(tag)
                    tag_weight += sin((pi / 2) * (len(current_tags) - index) / len(current_tags))
            normalized_tag_weight = (tag_weight / max_possible_tag_weight) * 5

            # Популярность
            popularity_weight = ref.rating_count
            normalized_popularity_weight = (popularity_weight / max_popularity) * 5 if max_popularity > 0 else 0

            # Взвешенный рейтинг
            weighted_rating = (ref.rating_count / (ref.rating_count + k) * ref.average_rating) + (
                k / (ref.rating_count + k) * global_avg_rating
            )
            normalized_weighted_rating = weighted_rating

            # Актуальность
            delta_days = (datetime.datetime.utcnow() - b.time).days
            time_weight = exp(-self.TIME_DECAY_ALPHA * delta_days)
            normalized_time_weight = time_weight * 5
            # Итоговый вес
            final_weight = (
                normalized_tag_weight * self.TAG_WEIGHT_COEFFICIENT +
                normalized_popularity_weight * self.POPULARITY_COEFFICIENT +
                normalized_weighted_rating * self.RATING_COEFFICIENT +
                normalized_time_weight * self.TIME_WEIGHT_COEFFICIENT
            )

            recommendations.append((ref, final_weight, f"{ref.author}. {ref.title}. – {ref.city}: {ref.publisher}, {ref.year}. – {ref.pages} с."))

        # Шаг 5: Сортировка по итоговому весу и возврат результата
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return [r for r in recommendations[:top_n]]
