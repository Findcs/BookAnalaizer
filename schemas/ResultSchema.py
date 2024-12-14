from typing import Optional

from pydantic import BaseModel

from configs.Database import Result


class GetTopTenResults(BaseModel):
    data: list[Result] = []
    length: int = 0

    class Config:
        arbitrary_types_allowed = True


class GetResultsResponse(BaseModel):
    results: Optional[list[Result]] = []
    total_results: Optional[int] = 0

    class Config:
        arbitrary_types_allowed = True
