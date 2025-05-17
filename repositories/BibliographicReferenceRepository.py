from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import Depends
from sqlalchemy.orm import selectinload

from configs.Database import get_async_session, BibliographicReference, Book


class BibliographicReferenceRepository:
    """
    Репозиторий для работы с таблицей BibliographicReference.
    """
    db: AsyncSession

    def __init__(self, db: AsyncSession = Depends(get_async_session)):
        self.db = db

    async def create_bibliographic_reference(self, book_id: int, title: str, author: str, publisher: str,isbn: str, year: int, city:str, pages:int) -> BibliographicReference:
        """
        Создает новую библиографическую справку.
        """
        bibliographic = BibliographicReference(
            book_id=book_id,
            title=title,
            author=author,
            publisher=publisher,
            isbn=isbn,
            city=city,
            year=year,
            pages=pages
        )
        self.db.add(bibliographic)
        await self.db.commit()
        await self.db.refresh(bibliographic)
        return bibliographic

    async def get_all(self) -> list[BibliographicReference]:
        """
        Возвращает все библиографические справки.
        """
        result = await self.db.execute(select(BibliographicReference))
        return result.scalars().all()


    async def get_by_id(self, bibliographic_reference_id: int) -> BibliographicReference:
        """
        Возвращает библиографическую справку по ее ID.
        """
        result = await self.db.execute(
            select(BibliographicReference).filter(BibliographicReference.id == bibliographic_reference_id)
        )
        return result.scalar_one_or_none()

    async def get_by_book_id(self, book_id: int) -> BibliographicReference:
        """
        Возвращает библиографическую справку по ID книги.
        """
        result = await self.db.execute(
            select(BibliographicReference).filter(BibliographicReference.book_id == book_id)
        )
        return result.scalar_one_or_none()

    async def update_rating(self, bibliographic_reference_id: int, average_rating: float, rating_count: int) -> None:
        """
        Обновляет средний рейтинг и количество оценок для библиографической справки.
        """
        bibliographic = await self.get_by_id(bibliographic_reference_id)
        if bibliographic:
            bibliographic.average_rating = average_rating
            bibliographic.rating_count = rating_count
            await self.db.commit()

    async def delete_by_id(self, bibliographic_reference_id: int) -> None:
        """
        Удаляет библиографическую справку по ее ID.
        """
        bibliographic = await self.get_by_id(bibliographic_reference_id)
        if bibliographic:
            await self.db.delete(bibliographic)
            await self.db.commit()

    async def get_book_by_bibliographic_reference_id(self, bibliographic_reference_id: int) -> Book:
        """
        Возвращает книгу, связанную с библиографической справкой.
        """
        result = await self.db.execute(
            select(Book).join(BibliographicReference).filter(BibliographicReference.id == bibliographic_reference_id)
        )
        return result.scalar_one_or_none()

    async def get_all_with_books(self):
        """
        Возвращает все библиографические справки и связанные с ними книги.
        """
        result = await self.db.execute(
            select(BibliographicReference, Book).join(Book, BibliographicReference.book_id == Book.id)
        )
        return result.all()

    async def get_all_with_tags(self):
        """
        Возвращает все библиографические справки и связанные с ними теги.
        """
        result = await self.db.execute(
            select(BibliographicReference).options(selectinload(BibliographicReference.book))
        )
        return result.scalars().all()

    async def get_all_with_tags_by_section(self, section_id: int):
        """
        Возвращает все библиографические справки, у которых книга привязана к определённому разделу.
        """
        result = await self.db.execute(
            select(BibliographicReference)
            .join(BibliographicReference.book)  # JOIN book
            .options(selectinload(BibliographicReference.book))  # для сериализации
            .where(Book.section_id == section_id)  # фильтрация по разделу
        )
        return result.scalars().all()

    async def get_all_with_sections(self):
        """
        Возвращает все библиографические справки с их секциями.
        """
        result = await self.db.execute(
            select(BibliographicReference)
            .join(BibliographicReference.book)  # JOIN book
            .options(selectinload(BibliographicReference.book))  # для сериализации
        )
        return result.scalars().all()
