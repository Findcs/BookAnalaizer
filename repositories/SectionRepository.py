from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from uuid import UUID

from sqlalchemy.orm import selectinload

from configs.Database import get_async_session, BibliographicReference, Section, Book


class FeedbackRepository:
    db: AsyncSession

    def __init__(self, db: AsyncSession = Depends(get_async_session)) -> None:
        self.db = db

    async def get_all(self) -> Section:
        """
        Возвращает все секции.
        """
        result = await self.db.execute(select(Section))
        return result.scalars().all()

    async def get_by_id(self, section_id: int) -> Section:
        """
        Возвращает секцию по ID.
        """
        result = await self.db.execute(select(Section).filter(Section.id == section_id))
        return result.scalar_one_or_none()


    async def add_section(self, name:str, description:str) -> Section:
        section = Section(name=name, description=description)
        self.db.add(section)
        self.db.add(section)
        await self.db.commit()
        await self.db.refresh(section)
        return section

    async def get_top_sections(self, limit: int = 6):
        result = await self.db.execute(
            select(Section, func.count(Book.id).label("book_count"))
            .join(Book, Book.section_id == Section.id)
            .group_by(Section.id)
            .order_by(desc("book_count"))
            .limit(limit)
        )
        return result.all()