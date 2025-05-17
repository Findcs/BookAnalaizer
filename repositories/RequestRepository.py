from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from configs.Database import get_async_session, Book


class RequestRepository:
    db: AsyncSession

    def __init__(
            self, db: AsyncSession = Depends(get_async_session)
    ) -> None:
        self.db = db

    async def create(self, request: Book) -> Book:
        self.db.add(request)
        await self.db.commit()
        return request

    async def get_all_user_books(self, user_id) -> list[Book]:
        result = await self.db.execute(
            select(Book).where(Book.user_id == user_id)
        )
        return result.scalars().all()

    async def get_by_id(self, request_id: int) -> Book:
        result = await self.db.execute(select(Book).filter(Book.id == request_id))
        return result.scalar_one_or_none()