from fastapi import Depends, HTTPException
from repositories.BibliographicReferenceRepository import BibliographicReferenceRepository
from repositories.RequestRepository import RequestRepository


class BibliographicReferenceService:
    """
    Сервис для работы с библиографическими справками.
    """
    def __init__(self, repository: BibliographicReferenceRepository = Depends()):
        self.repository = repository

    async def create_reference(self, book_id: int, title: str, author: str, publisher: str,isbn: str,year: int, city:str, pages:int):
        """
        Создает новую библиографическую справку для книги.
        """
        # Проверяем, существует ли справка для этой книги
        existing_reference = await self.repository.get_by_book_id(book_id)
        if existing_reference:
            raise HTTPException(status_code=400, detail="Bibliographic reference already exists for this book")

        # Создаем новую справку
        return await self.repository.create_bibliographic_reference(book_id, title, author, publisher,isbn,year, city, pages)

    async def get_all_references(self):
        """
        Возвращает все библиографические справки.
        """
        references = await self.repository.get_all()
        return references


    async def get_reference_by_id(self, bibliographic_reference_id: int):
        """
        Возвращает библиографическую справку по ID.
        """
        reference = await self.repository.get_by_id(bibliographic_reference_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Bibliographic reference not found")
        return reference

    async def get_reference_by_book_id(self, book_id: int):
        """
        Возвращает библиографическую справку по ID книги.
        """
        reference = await self.repository.get_by_book_id(book_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Bibliographic reference not found for this book")
        return reference

    async def update_reference_rating(self, bibliographic_reference_id: int, average_rating: float, rating_count: int):
        """
        Обновляет средний рейтинг и количество оценок для библиографической справки.
        """
        await self.repository.update_rating(bibliographic_reference_id, average_rating, rating_count)

    async def delete_reference(self, bibliographic_reference_id: int):
        """
        Удаляет библиографическую справку по ID.
        """
        reference = await self.repository.get_by_id(bibliographic_reference_id)
        if not reference:
            raise HTTPException(status_code=404, detail="Bibliographic reference not found")
        await self.repository.delete_by_id(bibliographic_reference_id)

    async def get_all_references_with_books(self):
        """
        Возвращает список всех библиографических справок с книгами.
        """
        return await self.repository.get_all_with_books()

    async def get_all_references_with_tags(self):
        """
        Возвращает список всех библиографических справок с тегами.
        """
        return await self.repository.get_all_with_tags()

    async def get_references_by_section(self, section_id: int):
        return await self.repository.get_all_with_tags_by_section(section_id)