from fastapi import Depends, HTTPException
from repositories.SectionRepository import SectionRepository
from repositories.BibliographicReferenceRepository import BibliographicReferenceRepository
from uuid import UUID


class SectionService:
    def __init__(
        self,
        repository: SectionRepository = Depends(),
    ):
        self.repository = repository

    async def get_top_sections(self, limit: int = 6):
        """
        Возвращает топ секции.
        """
        return await self.repository.get_top_sections(limit)

    async def get_all(self) -> list[dict]:
        """
        Возвращает все секции.
        """
        return await self.repository.get_all()

    async def get_by_id(self, section_id: int) -> dict:
        """
        Возвращает секцию по ID.
        """
        return await self.repository.get_by_id(section_id)

    async def add_section(self, name: str, description: str) -> dict:
        """
        Добавляет секцию.
        """
        return await self.repository.add_section(name, description)
