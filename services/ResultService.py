from typing import Optional

from fastapi import Depends

from configs.Database import User
from repositories.ResultRepository import ResultRepository
from schemas.ResultSchema import GetTopTenResults


class ResultService:
    result_repository: ResultRepository

    def __init__(self,
                 result_repository: ResultRepository = Depends()):
        self.result_repository = result_repository

    async def get(
            self,
            user: User,
            limit: int,
            order: str = "newest",
            searchText: Optional[str] = None,
            page: int = 1
    ) -> GetTopTenResults:
        result = GetTopTenResults()
        res = await self.result_repository.get_latest_results_for_user(
            user.id, limit, order, searchText, page
        )
        result.data = res.results
        result.length = res.total_results
        return result
