from typing import List, Annotated

from fastapi import APIRouter, Depends, status, UploadFile, File, Form

from configs.Database import User
from services.BookService import BookService
from services.UserService import current_active_user

RequestsRouter = APIRouter(prefix="/v1/analyze", tags=["requests"])


@RequestsRouter.post(
    "/",
    status_code=status.HTTP_201_CREATED,
)
async def create(
        file: UploadFile = File(...),
        user: User = Depends(current_active_user),
        requests_service: BookService = Depends(),
):
    try:
        res = await requests_service.create(file, user)
        return res
    except ValueError as e:
        return {"error": str(e)}


@RequestsRouter.post(
    "/mystem",
    status_code=status.HTTP_201_CREATED,
)
async def create(
        file: UploadFile = File(...),
        user: User = Depends(current_active_user),
        requests_service: BookService = Depends(),
):
    try:
        res = await requests_service.analyze(file, user)
        return res
    except ValueError as e:
        return {"error": str(e)}

