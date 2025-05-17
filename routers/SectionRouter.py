from fastapi import APIRouter, Depends, status, UploadFile, File, Form, HTTPException
from uuid import UUID

from configs.Database import User
from schemas.BookFeedbackSchema import BookFeedbackSchema
from services.SectionService import SectionService
from services.BookService import BookService
from services.UserService import current_active_user

SectionRouter = APIRouter(prefix="/v1/sections", tags=["sections"])


@SectionRouter.get(
    "/",
    status_code=status.HTTP_200_OK,
)
async def get_all_sections(
        manager: SectionService = Depends(),
):
    try:
        result = await manager.get_all()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@SectionRouter.get(
    "/get_top",
    status_code=status.HTTP_200_OK,
)
async def get_all_sections(
        manager: SectionService = Depends(),
):
    try:
        result = await manager.get_top_sections()
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@SectionRouter.post(
    "/",
    status_code=status.HTTP_201_CREATED)
async def add_section(
        name: str,
        description : str,
        user: User = Depends(current_active_user),
        manager: SectionService = Depends()
):
    try:
        result = await manager.add_section(name,description)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))