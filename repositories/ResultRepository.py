from fastapi import Depends
from sqlalchemy import select, desc, UUID, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session
from sqlalchemy.sql.operators import ilike_op

from configs.Database import get_async_session, Book, Result
from schemas.ResultSchema import GetResultsResponse


class ResultRepository:
    db: AsyncSession

    def __init__(
            self, db: AsyncSession = Depends(get_async_session)
    ) -> None:
        self.db = db

    async def create(self, result: Result) -> Book:
        self.db.add(result)
        await self.db.commit()
        return result

    def get_count(self, q):
        count_q = q.statement.with_only_columns([func.count()]).order_by(None)
        count = q.session.execute(count_q).scalar()
        return count

    async def get_result_count_for_user(self, user_id: UUID, searchText: str = None) -> int:
        query = (
            select(func.count())
            .select_from(Result)
            .join(Book, Result.BookId == Book.id)
            .filter(Book.user_id == user_id)
        )

        if searchText and len(searchText) > 0:
            query = query.filter(ilike_op(Result.bookTitle, f"%{searchText}%"))

        count = await self.db.execute(query)
        return count.scalar()

    async def get_latest_results_for_user(
            self, user_id: UUID, n: int = 10, order: str = "newest", searchText: str = None, page: int = 1
    ) -> GetResultsResponse:
        res = GetResultsResponse()
        # Определение базового запроса
        query = (
            select(Result)
            .join(Book)
            .filter(Book.user_id == user_id)
        )

        # Добавление условий в зависимости от параметров
        if order == "newest":
            query = query.order_by(desc(Result.time))
        elif order == "older":
            query = query.order_by(Result.time)

        if searchText and len(searchText) > 0:
            query = query.filter(ilike_op(Result.bookTitle, f"%{searchText}%"))

        if page > 1:
            offset = (page - 1) * n
            query = query.offset(offset)

        query = query.limit(n)

        # Выполнение запроса и возврат результатов
        results = await self.db.execute(query)
        count = await self.get_result_count_for_user(user_id, searchText)
        res.results = results.scalars().all()
        res.total_results = count
        return res
