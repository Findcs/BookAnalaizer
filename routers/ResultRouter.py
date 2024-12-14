from typing import List, Annotated

from fastapi import APIRouter, Depends, status, UploadFile, File, Form, Query

from configs.Database import User
from services.BookService import BookService
from services.ResultService import ResultService
from services.UserService import current_active_user

ResultRouter = APIRouter(prefix="/v1/results", tags=["results"])


@ResultRouter.get(
    "/",
)
async def get(
        user: User = Depends(current_active_user),
        results_service: ResultService = Depends(),
        limit: int = Query(10, ge=1, le=100),
        order: str = Query("newest", regex="^(newest|oldest)$"),
        searchText: str = Query(None),
        page: int = Query(1, ge=1),
):
    try:
        res = await results_service.get(user, limit, order, searchText, page)
        return res.model_dump()
    except ValueError as e:
        return {"error": str(e)}
